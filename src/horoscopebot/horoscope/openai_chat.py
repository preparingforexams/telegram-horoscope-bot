import logging
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence, cast

import httpx
from httpx import RequestError
from openai import BadRequestError, OpenAI, OpenAIError
from openai.types.chat import ChatCompletionMessageParam
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

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
        self._http_client = httpx.Client(timeout=20)
        HTTPXClientInstrumentor().instrument_client(self._http_client)
        self._open_ai = OpenAI(api_key=config.token, http_client=self._http_client)

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

        if geggo := self._make_geggo(user_id, time):
            return geggo

        avenue = _AVENUE_BY_FIRST_SLOT[slots[0]]
        prompt = avenue.build_prompt()
        completion = self._create_completion(user_id, prompt)
        return completion

    def _make_geggo(self, user_id: int, time: datetime) -> HoroscopeResult | None:
        if time.hour == 0 and time.minute == 18:
            return HoroscopeResult(
                "Um 0:18 Uhr schmeckt der Traubensaft am herrlichsten."
            )

        if time.month == 1 and time.day == 1:
            prompt = (
                "Sag mir den Verlauf meines Jahres voraus. Es ist egal, ob die"
                " Vorhersage realistisch oder akkurat ist, Hauptsache sie ist"
                " unterhaltsam und liest sich nicht wie ein übliches Horoskop."
                " Vermeide die Wörter"
                ' "Herausforderung" und "Chance". Sei nicht vage, sondern erwähne'
                " mindestens ein konkretes Ereignis.\n\n"
                "Die Antwort sollte kurz und prägnant sein."
            )
            return self._create_completion(
                user_id,
                prompt,
                temperature=1.1,
                max_tokens=200,
                frequency_penalty=0,
                presence_penalty=0,
            )

        if user_id == 133399998 or (
            user_id == 167930454 and time.month == 5 and time.day == 27
        ):
            message = "Du musst Steuern sparen."
            image = self._create_image(
                [
                    dict(role="user", content="Gib Horoskop."),
                    dict(
                        role="assistant",
                        content="Baron Münchhausen reitet eine Kanonenkugel in Richtung Akropolis.",
                    ),
                ],
                improve_prompt=False,
            )
            return HoroscopeResult(
                message=message,
                image=image,
            )

        return None

    def _create_completion(
        self,
        user_id: int,
        prompt: str,
        temperature: float = 1.0,
        max_tokens: int = 100,
        frequency_penalty: float = 0.35,
        presence_penalty: float = 0.75,
    ) -> HoroscopeResult:
        _LOG.info("Requesting chat completion")
        messages: list[ChatCompletionMessageParam] = [dict(role="user", content=prompt)]
        response = self._open_ai.chat.completions.create(
            model=self._model_name,
            max_tokens=max_tokens,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            temperature=temperature,
            user=str(user_id),
            messages=messages,
        )
        message = response.choices[0].message
        image = self._create_image(
            [
                *messages,
                dict(role=message.role, content=message.content),
            ]
        )
        return HoroscopeResult(
            message=cast(str, message.content),
            image=image,
        )

    def _improve_image_prompt(
        self,
        messages: Sequence[ChatCompletionMessageParam],
    ) -> ChatCompletionMessageParam | None:
        _LOG.info("Improving image prompt")
        try:
            response = self._open_ai.chat.completions.create(
                model=self._model_name,
                messages=[
                    *messages,
                    dict(
                        role="user",
                        content=_IMAGE_IMPROVEMENT_PROMPT,
                    ),
                ],
                max_tokens=128,
            )
            message = response.choices[0].message
            return dict(role=message.role, content=message.content)
        except OpenAIError as e:
            _LOG.error("Could not improve image generation prompt", exc_info=e)
            return None

    def _create_image(
        self,
        messages: list[ChatCompletionMessageParam],
        *,
        improve_prompt: bool = True,
    ) -> bytes | None:
        if improve_prompt:
            improvement_message = self._improve_image_prompt(messages) or messages[-1]
        else:
            improvement_message = messages[-1]

        prompt = improvement_message["content"]

        if not prompt:
            _LOG.error("Can't generate image because prompt is missing")
            return None
        elif not isinstance(prompt, str):
            _LOG.error("Prompt is not a str, but a %s", type(prompt))
            return None

        _LOG.info("Requesting image with prompt %s", prompt)
        try:
            ai_response = self._open_ai.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                response_format="url",
            )
        except BadRequestError as e:
            # Only ever saw this because of their profanity filter. Of course the error
            # code was fucking None, so I would have to check the message to make sure
            # that the error is actually about their "safety system", but I won't.
            _LOG.debug("Got InvalidRequestError from OpenAI", exc_info=e)
            return None
        except OpenAIError as e:
            _LOG.error("An error occurred during image generation", exc_info=e)
            return None

        url = ai_response.data[0].url

        if not url:
            raise ValueError("Did not receive URL as response")

        try:
            response = self._http_client.get(url, timeout=60)
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
