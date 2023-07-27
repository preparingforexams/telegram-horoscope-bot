import abc
from dataclasses import dataclass
from enum import Enum, auto

from pendulum import DateTime


@dataclass
class HoroscopeResult:
    message: str
    image: bytes | None = None

    @property
    def should_use_html_parsing(self) -> bool:
        return False

    @property
    def formatted_message(self) -> str:
        if self.should_use_html_parsing:
            return f"<tg-spoiler>{self.message}</tg-spoiler>"

        return self.message


class Horoscope(abc.ABC):
    @abc.abstractmethod
    def provide_horoscope(
        self,
        dice: int,
        context_id: int,
        user_id: int,
        message_id: int,
        message_time: DateTime,
    ) -> HoroscopeResult | None:
        pass


class Slot(Enum):
    BAR = auto()
    GRAPE = auto()
    LEMON = auto()
    SEVEN = auto()


SLOT_MACHINE_VALUES: dict[int, tuple[Slot, Slot, Slot]] = {
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
