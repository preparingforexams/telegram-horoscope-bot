import logging
import signal
from typing import Callable, Optional, List

import pendulum
import requests

from horoscopebot.config import TelegramConfig
from horoscopebot.dementia_responder import DementiaResponder
from horoscopebot.horoscope.horoscope import Horoscope
from .rate_limit import RateLimiter

_LOG = logging.getLogger(__name__)


class Bot:
    def __init__(
        self,
        config: TelegramConfig,
        horoscope: Horoscope,
        rate_limiter: RateLimiter,
    ):
        self.config = config
        self.horoscope = horoscope
        self._dementia_responder = DementiaResponder()
        self._rate_limiter = rate_limiter
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
    def _get_actual_body(response: requests.Response):
        response.raise_for_status()
        body = response.json()
        if body.get("ok"):
            return body["result"]
        raise ValueError(f"Body was not ok! {body}")

    def _send_message(
        self, chat_id: int, text: str, reply_to_message_id: Optional[int]
    ) -> dict:
        return self._get_actual_body(
            requests.post(
                self._build_url("sendMessage"),
                json={
                    "text": text,
                    "chat_id": chat_id,
                    "reply_to_message_id": reply_to_message_id,
                },
                timeout=10,
            )
        )

    @staticmethod
    def _is_lemons(dice: int) -> bool:
        return dice == 43

    def _handle_update(self, update: dict):
        message = update.get("message")

        if not message:
            _LOG.debug("Skipping non-message update")
            return

        chat_id = message["chat"]["id"]
        if chat_id not in self.config.enabled_chats:
            _LOG.debug("Not enabled in chat %d", chat_id)
            return

        dice: Optional[dict] = message.get("dice")
        if not dice:
            _LOG.debug("Skipping non-dice message")
            return

        if dice["emoji"] != "🎰":
            _LOG.debug("Skipping non-slot-machine message")
            return

        timestamp = message["date"]
        time = pendulum.from_timestamp(timestamp)
        user_id = message["from"]["id"]
        message_id = message["message_id"]
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
            self._send_message(
                chat_id=chat_id,
                reply_to_message_id=reply_message_id,
                text=response.text,
            )
            return

        result_text: str | None = None
        if not self._is_lemons(dice_value):
            result_text = self.horoscope.provide_horoscope(
                dice=dice_value,
                context_id=chat_id,
                user_id=user_id,
                message_id=message_id,
                message_time=time,
            )

        response_id: str | None = None
        if result_text is None:
            _LOG.debug(
                "Not sending horoscope because horoscope returned None for %d",
                dice["value"],
            )
        else:
            response = self._send_message(
                chat_id=chat_id,
                text=result_text,
                reply_to_message_id=message_id,
            )
            response_id = str(response["message_id"])

        self._rate_limiter.add_usage(
            context_id=chat_id,
            user_id=user_id,
            time=time,
            reference_id=str(message_id),
            response_id=response_id,
        )

    def _request_updates(self, last_update_id: Optional[int]) -> List[dict]:
        body: Optional[dict] = None
        if last_update_id:
            body = {
                "offset": last_update_id + 1,
                "timeout": 10,
            }
        return self._get_actual_body(
            requests.post(
                self._build_url("getUpdates"),
                json=body,
                timeout=15,
            )
        )

    def _handle_updates(self, handler: Callable[[dict], None]):
        last_update_id: Optional[int] = None
        while not self._should_terminate:
            updates = self._request_updates(last_update_id)
            try:
                for update in updates:
                    _LOG.info(f"Received update: {update}")
                    handler(update)
                    last_update_id = update["update_id"]
            except Exception as e:
                _LOG.error("Could not handle update", exc_info=e)
        _LOG.info("Stopping update handling because of terminate signal")
