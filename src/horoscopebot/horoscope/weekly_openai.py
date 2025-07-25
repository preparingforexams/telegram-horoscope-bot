import base64
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import cast

from openai import (
    AsyncOpenAI,
    BadRequestError,
    OpenAIError,
)
from openai.types.chat import ChatCompletionMessageParam

from horoscopebot.config import OpenAiConfig

from .horoscope import SLOT_MACHINE_VALUES, Horoscope, HoroscopeResult, Slot

_LOG = logging.getLogger(__name__)

_BASE_PROMPT = (
    "Sag mir den Verlauf meiner Woche voraus. Es ist egal, ob die"
    " Vorhersage realistisch oder akkurat ist, Hauptsache sie ist"
    " unterhaltsam und liest sich nicht wie ein übliches Horoskop."
    " Vermeide die Wörter"
    ' "Herausforderung" und "Chance". Sei nicht vage, sondern erwähne'
    " mindestens ein konkretes Ereignis.\n\n"
    "Die Antwort sollte kurz und prägnant sein."
)

_IMAGE_IMPROVEMENT_PROMPT = (
    "Beschreibe in wenigen Worten ein Bild, das deine Vorhersage illustriert."
)

_REFINEMENT_BY_SECOND_SLOT = {
    Slot.GRAPE: "Die Ereignisse sollten im Verlauf der Woche chaotischer werden.",
    Slot.LEMON: "In der Mitte der Woche sollten negative Ereignisse auftauchen.",
    Slot.SEVEN: "In der Mitte der Woche sollten positive Ereignisse auftauchen.",
    Slot.BAR: "In der Mitte der Woche sollte Alkohol ins Spiel kommen.",
}


_REFINEMENT_BY_THIRD_SLOT = {
    Slot.GRAPE: "Die Woche sollte im absoluten Chaos enden.",
    Slot.LEMON: "Die Woche sollte sehr unvorteilhaft enden.",
    Slot.SEVEN: "Die Woche sollte sehr vorteilhaft enden.",
    Slot.BAR: "Die Woche sollte im Alkoholexzess enden.",
}


@dataclass
class Variant:
    base_prompt: str

    def build_prompt(self, second_slot: Slot, third_slot: Slot) -> str:
        slot_refinement = f"{_REFINEMENT_BY_SECOND_SLOT[second_slot]} {_REFINEMENT_BY_THIRD_SLOT[third_slot]}"
        return "\n\n".join([self.base_prompt, slot_refinement, "Horoskop:"])


@dataclass
class Geggo:
    messages: list[HoroscopeResult]
    add_real_horoscope: bool


_VARIANT_BY_FIRST_SLOT: dict[Slot, Variant] = {
    Slot.BAR: Variant(
        base_prompt=(
            f"{_BASE_PROMPT}\n\nDie Vorhersage sollte zum Alkoholgenuss auffordern."
        ),
    ),
    Slot.GRAPE: Variant(
        base_prompt=(f"{_BASE_PROMPT}\n\nDie Vorhersage sollte chaotisch wirken."),
    ),
    Slot.LEMON: Variant(
        base_prompt=f"{_BASE_PROMPT}\n\nDu solltest einen eher negativen Wochenverlauf vorhersagen.",
    ),
    Slot.SEVEN: Variant(
        base_prompt=f"{_BASE_PROMPT}\n\nDu solltest einen eher positiven Wochenverlauf vorhersagen.",
    ),
}


class WeeklyOpenAiHoroscope(Horoscope):
    def __init__(self, config: OpenAiConfig):
        self._debug_mode = config.debug_mode
        self._model_name = config.model_name
        self._image_moderation_level = config.image_moderation_level
        self._image_model_name = config.image_model_name
        self._image_quality = config.image_quality
        self._open_ai = AsyncOpenAI(api_key=config.token)

    async def provide_horoscope(
        self,
        dice: int,
        context_id: int,
        user_id: int,
        message_id: int,
        message_time: datetime,
    ) -> list[HoroscopeResult]:
        slots = SLOT_MACHINE_VALUES[dice]
        return await self._create_horoscope(user_id, slots, message_time)

    async def _create_horoscope(
        self,
        user_id: int,
        slots: tuple[Slot, Slot, Slot],
        time: datetime,
    ) -> list[HoroscopeResult]:
        if self._debug_mode:
            return [HoroscopeResult(message="debug mode is turned on")]

        geggo = await self._make_geggo(user_id, time)
        if geggo and geggo.add_real_horoscope:
            result = geggo.messages
        elif geggo and not geggo.add_real_horoscope:
            return geggo.messages
        else:
            result = []

        variant = _VARIANT_BY_FIRST_SLOT[slots[0]]
        prompt = variant.build_prompt(slots[1], slots[2])
        completion = await self._create_completion(user_id, prompt)
        result.append(completion)

        return result

    async def _make_geggo(self, user_id: int, time: datetime) -> Geggo | None:
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
            return Geggo(
                messages=[
                    await self._create_completion(
                        user_id,
                        prompt,
                        temperature=1.1,
                        max_tokens=200,
                        frequency_penalty=0,
                        presence_penalty=0,
                    )
                ],
                add_real_horoscope=False,
            )

        if user_id == 167930454 and time.month == 5 and time.day > 25:
            message = "Du musst Steuern sparen."
            image = await self._create_image(
                [
                    dict(role="user", content="Gib Horoskop."),
                    dict(
                        role="assistant",
                        content="Baron Münchhausen reitet eine Kanonenkugel durch die Luft in Richtung Akropolis.",
                    ),
                ],
                improve_prompt=False,
            )
            return Geggo(
                messages=[
                    HoroscopeResult(
                        message=message,
                        image=image,
                    ),
                    HoroscopeResult(message="Spaß"),
                ],
                add_real_horoscope=True,
            )

        return None

    async def _create_completion(
        self,
        user_id: int,
        prompt: str,
        temperature: float = 1.1,
        max_tokens: int = 300,
        frequency_penalty: float = 0.35,
        presence_penalty: float = 0.75,
    ) -> HoroscopeResult:
        _LOG.info("Requesting chat completion")
        messages: list[ChatCompletionMessageParam] = [dict(role="user", content=prompt)]
        response = await self._open_ai.chat.completions.create(
            model=self._model_name,
            max_tokens=max_tokens,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            temperature=temperature,
            user=str(user_id),
            messages=messages,
        )
        message = response.choices[0].message
        image = await self._create_image(
            [
                *messages,
                dict(role=message.role, content=message.content),
            ]
        )
        return HoroscopeResult(
            message=cast(str, message.content),
            image=image,
        )

    async def _improve_image_prompt(
        self,
        messages: Sequence[ChatCompletionMessageParam],
    ) -> ChatCompletionMessageParam | None:
        _LOG.info("Improving image prompt")
        try:
            response = await self._open_ai.chat.completions.create(
                model=self._model_name,
                messages=[
                    *messages,
                    dict(
                        role="user",
                        content=_IMAGE_IMPROVEMENT_PROMPT,
                    ),
                ],
                max_tokens=128,
                temperature=1.4,
            )
            message = response.choices[0].message
            return dict(role=message.role, content=message.content)
        except OpenAIError as e:
            _LOG.error("Could not improve image generation prompt", exc_info=e)
            return None

    async def _create_image(
        self,
        messages: list[ChatCompletionMessageParam],
        *,
        improve_prompt: bool = True,
    ) -> bytes | None:
        if improve_prompt:
            improvement_message = (
                await self._improve_image_prompt(messages) or messages[-1]
            )
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
            ai_response = await self._open_ai.images.generate(
                model=self._image_model_name,
                quality=self._image_quality,
                moderation=self._image_moderation_level,
                prompt=prompt,
                size="1024x1024",
                timeout=60,
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

        data = ai_response.data
        if data is None:
            raise ValueError("Did not receive data as response")

        base64_data = data[0].b64_json

        if not base64_data:
            raise ValueError("Did not receive image in response")

        return base64.b64decode(base64_data)
