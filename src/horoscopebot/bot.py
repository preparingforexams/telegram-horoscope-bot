import asyncio
import logging
import signal
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import tzinfo
from typing import Any, cast

from opentelemetry import trace
from rate_limiter import RateLimiter
from telegram import Chat, Message, ReplyParameters, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    ContextTypes,
    ExtBot,
    MessageHandler,
    Updater,
    filters,
)

from horoscopebot.config import TelegramConfig
from horoscopebot.dementia_responder import DementiaResponder
from horoscopebot.horoscope.horoscope import Horoscope, HoroscopeResult

_LOG = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


type TelegramContext = ContextTypes.DEFAULT_TYPE


@asynccontextmanager
async def telegram_span(*, update: Update, name: str) -> AsyncIterator[trace.Span]:
    with tracer.start_as_current_span(name) as span:
        span.set_attribute(
            "telegram.update_keys",
            list(update.to_dict(recursive=False).keys()),
        )
        span.set_attribute("telegram.update_id", update.update_id)

        if message := update.effective_message:
            span.set_attribute("telegram.message_id", message.message_id)
            span.set_attribute("telegram.message_timestamp", message.date.isoformat())

        if chat := update.effective_chat:
            span.set_attribute("telegram.chat_id", chat.id)
            span.set_attribute("telegram.chat_type", chat.type)

        if user := update.effective_user:
            span.set_attribute("telegram.user_id", user.id)

        yield span


class ReplyMessageGoneException(Exception):
    pass


class Bot:
    def __init__(
        self,
        config: TelegramConfig,
        horoscope: Horoscope,
        rate_limiter: RateLimiter,
        dementia_responder: DementiaResponder,
        timezone: tzinfo,
    ):
        self.config = config
        self.horoscope = horoscope
        self._rate_limiter = rate_limiter
        self._timezone = timezone
        self._dementia_responder = dementia_responder
        self._should_terminate = False

    async def __post_shutdown(self, _: Any) -> None:
        _LOG.info("Post shutdown hook called")
        await self._rate_limiter.close()

    async def run(self) -> None:
        bot = ExtBot(token=self.config.token)
        updater = Updater(bot, asyncio.Queue())

        app: Application = (
            Application.builder()
            .updater(updater)  # type: ignore[arg-type]
            .post_shutdown(self.__post_shutdown)
            .build()
        )

        app.add_handler(
            MessageHandler(
                filters=filters.Dice.SLOT_MACHINE,
                callback=self._handle_message,
            )
        )

        async with app:
            _LOG.info("Running bot")
            await app.start()
            await updater.start_polling()

            finish_line = asyncio.Event()
            loop = asyncio.get_running_loop()
            for sig in [signal.SIGTERM, signal.SIGINT]:
                loop.add_signal_handler(
                    sig,
                    finish_line.set,
                )

            _LOG.info("Waiting for exit signal")
            await finish_line.wait()
            _LOG.info("Exit signal received.")

            _LOG.debug("Stopping updater")
            await updater.stop()
            _LOG.debug("Stopping application")
            await app.stop()
            _LOG.debug("Exiting app context manager")

    @staticmethod
    def _split_text(text: str, first_limit: int) -> list[str]:
        chunks = []
        remaining = text
        limit = first_limit
        while remaining:
            if len(remaining) <= limit:
                chunks.append(remaining)
                break

            end_index = limit
            while not remaining[end_index - 1].isspace():
                end_index -= 1
            chunks.append(remaining[:end_index])
            remaining = remaining[end_index:]
            limit = 4096

        return chunks

    async def _send_message(
        self,
        chat: Chat,
        text: str,
        reply_to_message_id: int | None,
        use_html_parsing: bool = False,
        image: bytes | None = None,
    ) -> Message:
        _LOG.info("Sending message with text length %d", len(text))

        text_limit = 4096 if image is None else 1024
        text_parts = self._split_text(text, first_limit=text_limit)

        parse_mode = ParseMode.HTML if use_html_parsing else None
        if reply_to_message_id is None:
            reply_parameters = None
        else:
            reply_parameters = ReplyParameters(
                message_id=reply_to_message_id,
                allow_sending_without_reply=False,
            )

        message: Message

        try:
            if image is None:
                message = await chat.send_message(
                    text=text_parts[0],
                    reply_parameters=reply_parameters,
                    parse_mode=parse_mode,
                )
            else:
                message = await chat.send_photo(
                    photo=image,
                    caption=text_parts[0],
                    reply_parameters=reply_parameters,
                    parse_mode=parse_mode,
                )
        except BadRequest as e:
            if reply_to_message_id is not None:
                # Most likely the reply message is gone.
                raise ReplyMessageGoneException(reply_to_message_id) from e

            raise e

        for text_part in text_parts[1:]:
            await chat.send_message(
                text=text_part,
                parse_mode=parse_mode,
            )

        return message

    @staticmethod
    def _is_lemons(dice: int) -> bool:
        return dice == 43

    async def _handle_message(self, update: Update, ctx: TelegramContext):
        async with telegram_span(update=update, name="handle_message"):
            message = cast(Message, update.message)
            chat = message.chat
            user = message.from_user
            if user is None:
                _LOG.error("No user in message")
                return
            user_id = user.id
            time = message.date.astimezone(self._timezone)

            if chat.id not in self.config.enabled_chats:
                _LOG.debug("Not enabled in chat %d", chat.id)
                return

            dice = message.dice
            if not dice:
                _LOG.warning("Skipping non-dice message")
                return

            if dice.emoji != "🎰":
                _LOG.warning("Skipping non-slot-machine message")
                return

            dice_value = dice.value

            conflicting_usage = await self._rate_limiter.get_offending_usage(
                context_id=chat.id,
                user_id=user_id,
                at_time=time,
            )

            if conflicting_usage is not None:
                if self._is_lemons(dice_value):
                    # The other bot will send the picture anyway, so we'll be quiet
                    return

                response = self._dementia_responder.create_response(
                    current_message_id=message.message_id,
                    current_message_time=time,
                    usage=conflicting_usage,
                )
                reply_message_id = response.reply_message_id or message.message_id
                try:
                    await self._send_message(
                        chat=chat,
                        reply_to_message_id=reply_message_id,
                        text=response.text,
                    )
                except ReplyMessageGoneException as e:
                    _LOG.error("Could not reply to message", exc_info=e)

                return

            horoscope_results: list[HoroscopeResult] = []
            if not self._is_lemons(dice_value):
                with tracer.start_as_current_span("provide_horoscope"):
                    horoscope_results = await self.horoscope.provide_horoscope(
                        dice=dice_value,
                        context_id=chat.id,
                        user_id=user_id,
                        message_id=message.message_id,
                        message_time=time,
                    )

            response_id: str | None = None
            if not horoscope_results:
                _LOG.debug(
                    "Not sending horoscope because horoscope returned None for %d",
                    dice.value,
                )
            else:
                first_result = horoscope_results[0]
                try:
                    response_message = await self._send_message(
                        chat=chat,
                        text=first_result.formatted_message,
                        image=first_result.image,
                        use_html_parsing=first_result.should_use_html_parsing,
                        reply_to_message_id=message.message_id,
                    )
                except ReplyMessageGoneException as e:
                    _LOG.error("Could not reply to message", exc_info=e)
                    return

                for result in horoscope_results[1:]:
                    await asyncio.sleep(2)
                    response_message = await self._send_message(
                        chat=chat,
                        text=result.formatted_message,
                        image=result.image,
                        use_html_parsing=result.should_use_html_parsing,
                        reply_to_message_id=None,
                    )

                response_message_id = response_message.message_id
                response_id = str(response_message_id)

            await self._rate_limiter.add_usage(
                context_id=chat.id,
                user_id=user_id,
                time=time,
                reference_id=str(message.message_id),
                response_id=response_id,
            )
