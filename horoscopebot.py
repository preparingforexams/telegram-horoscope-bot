import logging
import os
import sys
from datetime import datetime
from enum import Enum, auto
from typing import Callable, Optional, List, Tuple, Dict
from zoneinfo import ZoneInfo

import requests
import sentry_sdk

_API_KEY = os.getenv("TELEGRAM_API_KEY")

_LOG = logging.getLogger("horoscopebot")


class Slot(Enum):
    BAR = auto()
    GRAPE = auto()
    LEMON = auto()
    SEVEN = auto()


_SLOT_MACHINE_VALUES: Dict[int, Tuple[Slot, Slot, Slot]] = {
    1: (Slot.BAR, Slot.BAR, Slot.BAR),
    2: (Slot.GRAPE, Slot.BAR, Slot.BAR),
    3: (Slot.LEMON, Slot.BAR, Slot.BAR),
    4: (Slot.SEVEN, Slot.BAR, Slot.BAR),
    5: (Slot.BAR, Slot.GRAPE, Slot.BAR),
    6: (Slot.GRAPE, Slot.GRAPE, Slot.BAR),
    7: (Slot.LEMON, Slot.GRAPE, Slot.BAR),
    8: (Slot.SEVEN, Slot.GRAPE, Slot.BAR),
    9: (Slot.BAR, Slot.LEMON, Slot.BAR),
    10: (Slot.GRAPE, Slot.LEMON, Slot.BAR),
    11: (Slot.LEMON, Slot.LEMON, Slot.BAR),
    12: (Slot.SEVEN, Slot.LEMON, Slot.BAR),
    13: (Slot.BAR, Slot.SEVEN, Slot.BAR),
    14: (Slot.GRAPE, Slot.SEVEN, Slot.BAR),
    15: (Slot.LEMON, Slot.SEVEN, Slot.BAR),
    16: (Slot.SEVEN, Slot.SEVEN, Slot.BAR),
    17: (Slot.BAR, Slot.BAR, Slot.GRAPE),
    18: (Slot.GRAPE, Slot.BAR, Slot.GRAPE),
    19: (Slot.LEMON, Slot.BAR, Slot.GRAPE),
    20: (Slot.SEVEN, Slot.BAR, Slot.GRAPE),
    21: (Slot.BAR, Slot.GRAPE, Slot.GRAPE),
    22: (Slot.GRAPE, Slot.GRAPE, Slot.GRAPE),
    23: (Slot.LEMON, Slot.GRAPE, Slot.GRAPE),
    24: (Slot.SEVEN, Slot.GRAPE, Slot.GRAPE),
    25: (Slot.BAR, Slot.LEMON, Slot.GRAPE),
    26: (Slot.GRAPE, Slot.LEMON, Slot.GRAPE),
    27: (Slot.LEMON, Slot.LEMON, Slot.GRAPE),
    28: (Slot.SEVEN, Slot.LEMON, Slot.GRAPE),
    29: (Slot.BAR, Slot.SEVEN, Slot.GRAPE),
    30: (Slot.GRAPE, Slot.SEVEN, Slot.GRAPE),
    31: (Slot.LEMON, Slot.SEVEN, Slot.GRAPE),
    32: (Slot.SEVEN, Slot.SEVEN, Slot.GRAPE),
    33: (Slot.BAR, Slot.BAR, Slot.LEMON),
    34: (Slot.GRAPE, Slot.BAR, Slot.LEMON),
    35: (Slot.LEMON, Slot.BAR, Slot.LEMON),
    36: (Slot.SEVEN, Slot.BAR, Slot.LEMON),
    37: (Slot.BAR, Slot.GRAPE, Slot.LEMON),
    38: (Slot.GRAPE, Slot.GRAPE, Slot.LEMON),
    39: (Slot.LEMON, Slot.GRAPE, Slot.LEMON),
    40: (Slot.SEVEN, Slot.GRAPE, Slot.LEMON),
    41: (Slot.BAR, Slot.LEMON, Slot.LEMON),
    42: (Slot.GRAPE, Slot.LEMON, Slot.LEMON),
    43: (Slot.LEMON, Slot.LEMON, Slot.LEMON),
    44: (Slot.SEVEN, Slot.LEMON, Slot.LEMON),
    45: (Slot.BAR, Slot.SEVEN, Slot.LEMON),
    46: (Slot.GRAPE, Slot.SEVEN, Slot.LEMON),
    47: (Slot.LEMON, Slot.SEVEN, Slot.LEMON),
    48: (Slot.SEVEN, Slot.SEVEN, Slot.LEMON),
    49: (Slot.BAR, Slot.BAR, Slot.SEVEN),
    50: (Slot.GRAPE, Slot.BAR, Slot.SEVEN),
    51: (Slot.LEMON, Slot.BAR, Slot.SEVEN),
    52: (Slot.SEVEN, Slot.BAR, Slot.SEVEN),
    53: (Slot.BAR, Slot.GRAPE, Slot.SEVEN),
    54: (Slot.GRAPE, Slot.GRAPE, Slot.SEVEN),
    55: (Slot.LEMON, Slot.GRAPE, Slot.SEVEN),
    56: (Slot.SEVEN, Slot.GRAPE, Slot.SEVEN),
    57: (Slot.BAR, Slot.LEMON, Slot.SEVEN),
    58: (Slot.GRAPE, Slot.LEMON, Slot.SEVEN),
    59: (Slot.LEMON, Slot.LEMON, Slot.SEVEN),
    60: (Slot.SEVEN, Slot.LEMON, Slot.SEVEN),
    61: (Slot.BAR, Slot.SEVEN, Slot.SEVEN),
    62: (Slot.GRAPE, Slot.SEVEN, Slot.SEVEN),
    63: (Slot.LEMON, Slot.SEVEN, Slot.SEVEN),
    64: (Slot.SEVEN, Slot.SEVEN, Slot.SEVEN),
}

_HOROSCOPE_BY_SLOT = {
    0: {
        Slot.SEVEN: "wahnsinnig",
        Slot.BAR: "erschreckend",
        Slot.GRAPE: "moderat",
        Slot.LEMON: "fast",
    }, 1: {
        Slot.SEVEN: "geil",
        Slot.BAR: "besoffen",
        Slot.GRAPE: "bedrückend",
        Slot.LEMON: "enttäuschend",
    }, 2: {
        Slot.SEVEN: "Veränder die Welt.",
        Slot.BAR: "Mach was draus.",
        Slot.GRAPE: "Quäl dich durch.",
        Slot.LEMON: "Bleib lieber liegen.",
    },
}


def _build_url(method: str) -> str:
    return f"https://api.telegram.org/bot{_API_KEY}/{method}"


def _get_actual_body(response: requests.Response):
    response.raise_for_status()
    body = response.json()
    if body.get("ok"):
        return body["result"]
    raise ValueError(f"Body was not ok! {body}")


def _send_message(chat_id: int, text: str, reply_to_message_id: Optional[int]) -> dict:
    return _get_actual_body(requests.post(
        _build_url("sendMessage"),
        json={
            "text": text,
            "chat_id": chat_id,
            "reply_to_message_id": reply_to_message_id,
        },
        timeout=10,
    ))


def _is_new_years_day() -> bool:
    utc_date = datetime.now()
    zone = ZoneInfo("Europe/Berlin")
    date = utc_date.astimezone(zone)
    return date.month == 1 and date.day == 1


def _build_horoscope(value: int) -> str:
    slots = _SLOT_MACHINE_VALUES[value]

    def _get_horoscope(slot: int):
        return _HOROSCOPE_BY_SLOT[slot][slots[slot]]

    horoscope = (
        f"{_get_horoscope(0)} {_get_horoscope(1)}. {_get_horoscope(2)}"
    )

    scope = "Jahr" if _is_new_years_day() else "Tag"

    return f"Dein {scope} wird {horoscope}"


def _handle_update(update: dict):
    message = update.get("message")

    if not message:
        _LOG.debug("Skipping non-message update")
        return

    dice: Optional[dict] = message.get("dice")
    if not dice:
        _LOG.debug("Skipping non-dice message")
        return

    if dice["emoji"] != "🎰":
        _LOG.debug("Skipping non-slot-machine message")
        return

    result_text = _build_horoscope(dice["value"])

    _send_message(
        chat_id=message["chat"]["id"],
        text=result_text,
        reply_to_message_id=message["message_id"],
    )


def _request_updates(last_update_id: Optional[int]) -> List[dict]:
    body: Optional[dict] = None
    if last_update_id:
        body = {
            "offset": last_update_id + 1,
            "timeout": 10,
        }
    return _get_actual_body(requests.post(
        _build_url("getUpdates"),
        json=body,
        timeout=15,
    ))


def _handle_updates(handler: Callable[[dict], None]):
    last_update_id: Optional[int] = None
    while True:
        updates = _request_updates(last_update_id)
        try:
            for update in updates:
                _LOG.info(f"Received update: {update}")
                handler(update)
                last_update_id = update["update_id"]
        except Exception as e:
            _LOG.error("Could not handle update", exc_info=e)


def _setup_logging():
    logging.basicConfig()
    _LOG.level = logging.INFO


def _setup_sentry():
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        _LOG.warning("Sentry DSN not found")
        return

    sentry_sdk.init(
        dsn,

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0
    )


def main():
    _setup_logging()
    _setup_sentry()

    if not _API_KEY:
        _LOG.error("Missing API key")
        sys.exit(1)

    _handle_updates(_handle_update)


if __name__ == '__main__':
    main()
