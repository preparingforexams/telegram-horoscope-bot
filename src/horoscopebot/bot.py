import logging
from typing import Callable, Optional, List

import requests

from horoscopebot.config import TelegramConfig
from horoscopebot.horoscope.horoscope import Horoscope

_LOG = logging.getLogger(__name__)


class Bot:
    def __init__(self, config: TelegramConfig, horoscope: Horoscope):
        self.config = config
        self.horoscope = horoscope

    def run(self):
        self._handle_updates(self._handle_update)

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

    def _handle_update(self, update: dict):
        message = update.get("message")

        if not message:
            _LOG.debug("Skipping non-message update")
            return

        if "forward_from" in message:
            _LOG.info("Forwarded from %d", message["forward_from"]["id"])

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

        user_id = message["from"]["id"]
        result_text = self.horoscope.provide_horoscope(
            dice=dice["value"], context_id=chat_id, user_id=user_id
        )

        if result_text is None:
            _LOG.debug(
                "Not sending horoscope because horoscope returned None for %d",
                dice["value"],
            )
            return

        self._send_message(
            chat_id=chat_id,
            text=result_text,
            reply_to_message_id=message["message_id"],
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
        while True:
            updates = self._request_updates(last_update_id)
            try:
                for update in updates:
                    _LOG.info(f"Received update: {update}")
                    handler(update)
                    last_update_id = update["update_id"]
            except Exception as e:
                _LOG.error("Could not handle update", exc_info=e)
