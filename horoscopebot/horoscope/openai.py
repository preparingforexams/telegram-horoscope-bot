from typing import Optional

from horoscopebot.config import OpenAiConfig
from horoscopebot.horoscope.horoscope import Horoscope


class OpenAiHoroscope(Horoscope):

    def __init__(self, config: OpenAiConfig):
        self._config = config

    def provide_horoscope(self, dice: int, context_id: int, user_id: int) -> Optional[str]:
        # TODO: implement
        return None
