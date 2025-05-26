import logging
import signal
import time
from collections.abc import Callable
from datetime import UTC, datetime, tzinfo
from time import sleep
from typing import Any, Self, cast

from httpx import Client, HTTPStatusError, Response, TimeoutException
from opentelemetry import trace
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from rate_limiter import RateLimiter

from horoscopebot.config import TelegramConfig
from horoscopebot.dementia_responder import DementiaResponder
from horoscopebot.horoscope.horoscope import Horoscope, HoroscopeResult

_LOG = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class RateLimitException(Exception):
    def __init__(self, retry_after: float):
        self.retry_after = retry_after

    @classmethod
    def from_response(cls, response: Response) -> Self:
        parameters = response.json()["parameters"]
        if parameters:
            return cls(retry_after=float(parameters["retry_after"]))

        return cls(retry_after=60.0)


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
        self._session = Client()
        HTTPXClientInstrumentor().instrument_client(self._session)
        self._should_terminate = False

    def run(self):
        signal.signal(signal.SIGTERM, self._on_kill)
        signal.signal(signal.SIGINT, self._on_kill)
        self._handle_updates(self._handle_update)

    def _on_kill(self, kill_signal: int, _):
        _LOG.info(
            "Received %s signal, requesting termination...",
            signal.Signals(kill_signal).name,
        )
        self._should_terminate = True

    def _build_url(self, method: str) -> str:
        return f"https://api.telegram.org/bot{self.config.token}/{method}"

    @staticmethod
    def _get_actual_body(response: Response):
        if response.status_code == 429:
            raise RateLimitException.from_response(response)

        response.raise_for_status()
        body = response.json()
        if body.get("ok"):
            return body["result"]
        raise ValueError(f"Body was not ok! {body}")

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

    def _send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_message_id: int | None,
        use_html_parsing: bool = False,
        image: bytes | None = None,
    ) -> dict:
        parsing_conf = {"parse_mode": "HTML"} if use_html_parsing else {}
        _LOG.info("Sending message with text length %d", len(text))

        text_limit = 4096 if image is None else 1024
        text_parts = self._split_text(text, first_limit=text_limit)

        if image is None:
            response = self._session.post(
                self._build_url("sendMessage"),
                json={
                    "text": text_parts[0],
                    "chat_id": chat_id,
                    "reply_to_message_id": reply_to_message_id,
                    **parsing_conf,
                },
            )
        else:
            response = self._session.post(
                self._build_url("sendPhoto"),
                data={
                    "caption": text_parts[0],
                    "chat_id": chat_id,
                    "reply_to_message_id": reply_to_message_id,
                    **parsing_conf,
                },
                files={
                    "photo": image,
                },
                timeout=20,
            )

        if reply_to_message_id is not None and response.status_code == 400:
            raise ReplyMessageGoneException(reply_to_message_id)

        if response.is_success:
            for text_part in text_parts[1:]:
                self._session.post(
                    self._build_url("sendMessage"),
                    json={
                        "text": text_part,
                        "chat_id": chat_id,
                        **parsing_conf,
                    },
                )

        return self._get_actual_body(response)

    @staticmethod
    def _is_lemons(dice: int) -> bool:
        return dice == 43

    def _handle_update(self, update: dict[str, Any]):
        with tracer.start_as_current_span("handle_update") as span:
            span = cast(trace.Span, span)
            span.set_attribute("telegram.update_keys", list(update.keys()))
            span.set_attribute("telegram.update_id", update["update_id"])
            span.set_attribute("is_processed", False)

            message = update.get("message")

            if not message:
                _LOG.debug("Skipping non-message update")
                return

            chat_id = message["chat"]["id"]
            span.set_attribute("telegram.chat_id", chat_id)
            user_id = message["from"]["id"]
            span.set_attribute("telegram.user_id", user_id)
            time = datetime.fromtimestamp(
                message["date"],
                tz=UTC,
            ).astimezone(self._timezone)
            span.set_attribute("telegram.message_timestamp", time.isoformat())
            message_id = message["message_id"]
            span.set_attribute("telegram.message_id", message_id)

            if chat_id not in self.config.enabled_chats:
                _LOG.debug("Not enabled in chat %d", chat_id)
                return

            dice: dict | None = message.get("dice")
            if not dice:
                _LOG.debug("Skipping non-dice message")
                return

            if dice["emoji"] != "🎰":
                _LOG.debug("Skipping non-slot-machine message")
                return

            span.set_attribute("is_processed", True)

            dice_value = dice["value"]

            conflicting_usage = self._rate_limiter.get_offending_usage(
                context_id=chat_id,
                user_id=user_id,
                at_time=time,
            )

            if conflicting_usage is not None:
                if self._is_lemons(dice_value):
                    # The other bot will send the picture anyway, so we'll be quiet
                    return

                response = self._dementia_responder.create_response(
                    current_message_id=message_id,
                    current_message_time=time,
                    usage=conflicting_usage,
                )
                reply_message_id = response.reply_message_id or message_id
                try:
                    self._send_message(
                        chat_id=chat_id,
                        reply_to_message_id=reply_message_id,
                        text=response.text,
                    )
                except ReplyMessageGoneException as e:
                    _LOG.error("Could not reply to message", exc_info=e)

                return

            horoscope_results: list[HoroscopeResult] = []
            if not self._is_lemons(dice_value):
                with tracer.start_as_current_span("provide_horoscope"):
                    horoscope_results = self.horoscope.provide_horoscope(
                        dice=dice_value,
                        context_id=chat_id,
                        user_id=user_id,
                        message_id=message_id,
                        message_time=time,
                    )

            response_id: str | None = None
            if not horoscope_results:
                _LOG.debug(
                    "Not sending horoscope because horoscope returned None for %d",
                    dice["value"],
                )
            else:
                first_result = horoscope_results[0]
                try:
                    response_message = self._send_message(
                        chat_id=chat_id,
                        text=first_result.formatted_message,
                        image=first_result.image,
                        use_html_parsing=first_result.should_use_html_parsing,
                        reply_to_message_id=message_id,
                    )
                except ReplyMessageGoneException as e:
                    _LOG.error("Could not reply to message", exc_info=e)
                    return

                for result in horoscope_results[1:]:
                    sleep(2)
                    response_message = self._send_message(
                        chat_id=chat_id,
                        text=result.formatted_message,
                        image=result.image,
                        use_html_parsing=result.should_use_html_parsing,
                        reply_to_message_id=None,
                    )

                response_message_id = response_message["message_id"]
                response_id = str(response_message_id)

            self._rate_limiter.add_usage(
                context_id=chat_id,
                user_id=user_id,
                time=time,
                reference_id=str(message_id),
                response_id=response_id,
            )

    def _request_updates(
        self, client: Client, last_update_id: int | None
    ) -> list[dict]:
        body = {
            "timeout": 10,
        }
        if last_update_id:
            body["offset"] = last_update_id + 1

        try:
            return self._get_actual_body(
                client.post(
                    self._build_url("getUpdates"),
                    json=body,
                    timeout=15,
                )
            )
        except TimeoutException as e:
            _LOG.warning("Encountered timeout while getting updates", exc_info=e)
            return []
        except RateLimitException as e:
            _LOG.warning(
                "Sent too many requests to Telegram, retrying after %f seconds",
                e.retry_after,
            )
            time.sleep(e.retry_after)
            return []
        except HTTPStatusError as e:
            _LOG.error("Got HTTPStatusError when requesting updates", exc_info=e)
            return []

    def _handle_updates(self, handler: Callable[[dict], None]):
        last_update_id: int | None = None
        client = Client()
        try:
            while not self._should_terminate:
                updates = self._request_updates(client, last_update_id)
                try:
                    for update in updates:
                        _LOG.info(f"Received update: {update}")
                        handler(update)
                        last_update_id = update["update_id"]
                except Exception as e:
                    _LOG.error("Could not handle update", exc_info=e)
            _LOG.info("Stopping update handling because of terminate signal")
        finally:
            client.close()
            self._session.close()
