import logging
import random
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TypedDict

import httpx
import openai
from httpx import RequestError
from openai import InvalidRequestError, OpenAIError

from horoscopebot.config import OpenAiConfig

from .horoscope import SLOT_MACHINE_VALUES, Horoscope, HoroscopeResult, Slot

_LOG = logging.getLogger(__name__)

_BASE_PROMPT = (
    r"Schreibe in zwei kurzen Sätzen eine originelle Vorhersage meines Tagesverlaufs,"
    r" oder auch nur eines bestimmten Ereignisses."
)

_IMAGE_IMPROVEMENT_PROMPT = (
    "Beschreibe in wenigen Worten ein Bild, das deine Vorhersage illustriert."
)


class ChatRole(str, Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"


class ChatMessage(TypedDict):
    role: ChatRole
    content: str


@dataclass
class Variation:
    probability: float
    prompt: str


@dataclass
class Avenue:
    base_prompt: str
    variations: list[Variation]

    def build_prompt(self) -> str:
        active_variation_prompts = [
            variation.prompt
            for variation in self.variations
            if random.random() <= variation.probability
        ]

        return "\n\n".join([self.base_prompt, *active_variation_prompts, "Horoskop:"])


_AVENUE_BY_FIRST_SLOT: dict[Slot, Avenue] = {
    Slot.BAR: Avenue(
        base_prompt=(
            f"{_BASE_PROMPT}\n\nDas Horoskop sollte zum Alkoholgenuss animieren."
        ),
        variations=[
            Variation(
                probability=0.15,
                prompt=(
                    "Referenziere Fabienne's exzessiven Alkoholismus. Beachte dabei,"
                    "dass Fabienne ein Mann ist, und keinen Wein trinkt."
                ),
            ),
            Variation(
                probability=0.05,
                prompt="Schlage vor, Dousnbier zu trinken",
            ),
            Variation(
                probability=0.05,
                prompt="Schlage vor, Hugo zu trinken",
            ),
            Variation(
                probability=0.02,
                prompt="Schlage vor, Rakete zu trinken",
            ),
            Variation(
                probability=0.05,
                prompt="Schlage vor, Dream Jizz zu trinken",
            ),
            Variation(
                probability=0.05,
                prompt="Schlage vor Eiersaft zu trinken",
            ),
            Variation(
                probability=0.1,
                prompt=(
                    "Erläutere die positiven gesundheitlichen Auswirkungen von Alkohol,"
                    " wenn auch frei erfunden."
                ),
            ),
            Variation(
                probability=0.05,
                prompt="Beleidige mich wegen meiner mangelnden Disziplin.",
            ),
        ],
    ),
    Slot.GRAPE: Avenue(
        base_prompt=(
            "Sage mir in zwei kurzen Sätzen eine sehr unerwartete Begebenheit voraus,"
            " die heute in meinem Alltag passieren wird."
            " Realismus ist dabei unerheblich."
        ),
        variations=[
            Variation(probability=0.2, prompt="Nutze Traum-Logik."),
            Variation(
                probability=0.2, prompt="Die Situation sollte auf der Arbeit passieren."
            ),
            Variation(
                probability=0.2,
                prompt="Die Situation sollte beim Spaziergang passieren.",
            ),
            Variation(probability=0.1, prompt="Referenziere kontextfrei Trauben."),
        ],
    ),
    Slot.LEMON: Avenue(
        base_prompt=f"""{_BASE_PROMPT}

Du solltest einen eher negativen Tagesverlauf vorhersagen.

Eine Liste guter Beispiele:
- Bleib einfach liegen.
- Morgens zwei Pfannen in die Eier und alles wird gut.
- Heute wird phänomenal enttäuschend.
- Dein Lebenslauf erhält heute einen neuen Eintrag.
- Dreh einfach wieder um.
- Weißt du noch, diese eine Deadline?
- Du verläufst dich heute in deiner Wohnung.
- Der Abwasch entwickelt intelligentes Leben.
- Du stößt dir den kleinen Zeh.
- Bad hair day.
- Deine Freunde machen sich über deine Frisur lustig.
- Ein platter Autoreifen verändert heute dein Leben.
- Im Kühlschrank gibt es nichts zu sehen.
- Du fängst schwach an, lässt dann aber auch stark nach.
""",
        variations=[],
    ),
    Slot.SEVEN: Avenue(
        base_prompt=f"""{_BASE_PROMPT}

Du solltest einen eher positiven Tagesverlauf vorhersagen.

Eine Liste guter Beispiele:
- Du triffst heute dein Idol.
- Heute lebst du ein Leben wie Larry.
- Heute gibt dir jemand eine zweite Chance.
- Sag niemals niemals. Mist.
- Entweder du hörst heute auf zu rauchen oder du fängst damit an.
- Lass alles liegen und greif nach den Sternen.
- Lass dich nicht unterkriegen.
- Alles wird gut.
- Geh ein Risiko ein, du wirst es nicht bereuen.
- Bereite dich auf etwas großes vor.
- Heute siehst du einen Ballon und freust dich.
- Du hättest heute alles schaffen können, aber brichst dir ein Bein.
- Du erreichst alle deine Ziele.
- Dein Leben hat heute endlich wieder Sinn.
- Niemand kann dich aufhalten!
- Du hast heute die Chance, dein Leben zu verändern. Nehme sie wahr!
""",
        variations=[
            Variation(
                probability=0.2,
                prompt=(
                    "Schlage eine riskante Aktivität vor,"
                    " der ich heute nachgehen könnte."
                ),
            ),
        ],
    ),
}


class OpenAiChatHoroscope(Horoscope):
    def __init__(self, config: OpenAiConfig):
        self._debug_mode = config.debug_mode
        self._model_name = config.model_name
        openai.api_key = config.token

    def provide_horoscope(
        self,
        dice: int,
        context_id: int,
        user_id: int,
        message_id: int,
        message_time: datetime,
    ) -> HoroscopeResult | None:
        slots = SLOT_MACHINE_VALUES[dice]
        return self._create_horoscope(user_id, slots, message_time)

    def _create_horoscope(
        self,
        user_id: int,
        slots: tuple[Slot, Slot, Slot],
        time: datetime,
    ) -> HoroscopeResult | None:
        if self._debug_mode:
            return HoroscopeResult(message="debug mode is turned on")

        geggo = self._make_geggo(user_id, time)
        if geggo:
            return HoroscopeResult(message=geggo)

        avenue = _AVENUE_BY_FIRST_SLOT[slots[0]]
        prompt = avenue.build_prompt()
        completion = self._create_completion(user_id, prompt)
        return completion

    def _make_geggo(self, user_id: int, time: datetime) -> str | None:
        if time.hour == 0 and time.minute == 18:
            return "Um 0:18 Uhr schmeckt der Traubensaft am herrlichsten."

        return None

    def _create_completion(self, user_id: int, prompt: str) -> HoroscopeResult:
        messages = [ChatMessage(role=ChatRole.USER, content=prompt)]
        response = openai.ChatCompletion.create(
            model=self._model_name,
            max_tokens=100,
            frequency_penalty=0.35,
            presence_penalty=0.75,
            user=str(user_id),
            messages=messages,
        )
        message = response.choices[0].message
        image = self._create_image([*messages, message])
        return HoroscopeResult(
            message=message.content,
            image=image,
        )

    def _improve_image_prompt(self, messages: list[ChatMessage]) -> ChatMessage | None:
        try:
            response = openai.ChatCompletion.create(
                model=self._model_name,
                messages=[
                    *messages,
                    ChatMessage(
                        role=ChatRole.USER,
                        content=_IMAGE_IMPROVEMENT_PROMPT,
                    ),
                ],
                max_tokens=128,
            )
            message = response.choices[0].message
            _LOG.info(
                "Improved prompt from '%s'\nto '%s'",
                messages[-1]["content"],
                message["content"],
            )
            return message
        except OpenAIError as e:
            _LOG.error("Could not improve image generation prompt", exc_info=e)
            return None

    def _create_image(self, messages: list[ChatMessage]) -> bytes | None:
        improvement_message = self._improve_image_prompt(messages) or messages[-1]
        prompt = improvement_message["content"]

        try:
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size="512x512",
                response_format="url",
            )
        except InvalidRequestError as e:
            # Only ever saw this because of their profanity filter. Of course the error
            # code was fucking None, so I would have to check the message to make sure
            # that the error is actually about their "safety system", but I won't.
            _LOG.debug("Got InvalidRequestError from OpenAI", exc_info=e)
            return None
        except OpenAIError as e:
            _LOG.error("An error occurred during image generation", exc_info=e)
            return None

        url = response["data"][0]["url"]

        try:
            response = httpx.get(url, timeout=60)
        except RequestError as e:
            _LOG.error("Could not request generated image", exc_info=e)
            return None

        if response.status_code >= 400:
            _LOG.error(
                "Got unsuccessful response %d when trying to get image",
                response.status_code,
            )
            return None

        return response.content
