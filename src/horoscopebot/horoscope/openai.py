import random
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple

import openai
import pendulum

from horoscopebot.config import OpenAiConfig
from .horoscope import Horoscope, SLOT_MACHINE_VALUES, Slot
from ..rate_limit import RateLimiter

_BASE_PROMPT = (
    r"Write a creative and witty horoscope for the day without mentioning a specific zodiac sign."
    r" The horoscope must be written in German. The horoscope should consist of two short sentences."
    r' Use "Du" instead of "Sie".'
)


@dataclass
class Variation:
    probability: float
    prompt: str


@dataclass
class Avenue:
    base_prompt: str
    variations: List[Variation]

    def build_prompt(self) -> str:
        active_variation_prompts = [
            variation.prompt
            for variation in self.variations
            if random.random() <= variation.probability
        ]

        return "\n\n".join([self.base_prompt, *active_variation_prompts, "Horoskop:"])


_AVENUE_BY_FIRST_SLOT: Dict[Slot, Avenue] = {
    Slot.BAR: Avenue(
        base_prompt=f"{_BASE_PROMPT}\n\nThe horoscope should encourage alcohol consumption.",
        variations=[
            Variation(
                probability=0.4,
                prompt="Include a reference to Torben's excessive alcoholism.",
            ),
            Variation(
                probability=0.4,
                prompt="""A list of examples of drinks to include:
- Dousnbier
- Ein Dösli Kölsch
- Hugo
- Ringreiterbowle
- Rakete
- Trichter""",
            ),
            Variation(
                probability=0.2,
                prompt="Suggest some random positive effects of alcohol on the liver.",
            ),
        ],
    ),
    Slot.GRAPE: Avenue(
        base_prompt=(
            "Beschreibe in zwei kurzen Sätzen eine sehr unerwartete Begebenheit,"
            " die jemandem heute in seinem Alltag passieren wird."
            " Schreibe in der zweiten Person. Die Begebenheit sollte vollkommen undenkbar sein."
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

The outlook of the horoscope should be negative.

A list of good examples:
- "Bleib einfach liegen."
- "Morgens zwei Pfannen in die Eier und alles wird gut."
- "Heute wird phänomenal enttäuschend."
- "Dein Lebenslauf erhält heute einen neuen Eintrag."
- "Dreh einfach wieder um."
- "Weißt du noch, diese eine Deadline?"
- "Du verläufst dich heute in deiner Wohnung."
- "Der Abwasch entwickelt intelligentes Leben."
- "Du stößt dir den kleinen Zeh."
- "Bad hair day."
- "Deine Freunde machen sich über deine Frisur lustig."
- "Ein platter Autoreifen verändert heute dein Leben."
- "Im Kühlschrank gibt es nichts zu sehen."
- "Völlig übermüdet manövrierst du dich doch noch elegant durch den Tag in Richtung Bett."
- "Du fängst schwach an, lässt dann aber auch stark nach."
""",
        variations=[],
    ),
    Slot.SEVEN: Avenue(
        base_prompt=f"""{_BASE_PROMPT}

The outlook of the horoscope should be very positive.

List of good examples:
- "Du triffst heute dein Idol."
- "Heute lebst du ein Leben wie Larry."
- "Heute gibt dir jemand eine zweite Chance."
- "Sag niemals niemals. Mist."
- "Entweder du hörst heute auf zu rauchen oder du fängst damit an."
- "Lass alles liegen und greif nach den Sternen."
- "Lass dich nicht unterkriegen."
- "Alles wird gut."
- "Geh ein Risiko ein, du wirst es nicht bereuen."
- "Bereite dich auf etwas großes vor."
- "Heute siehst du einen Ballon und freust dich."
- "Du hättest heute alles schaffen können, aber brichst dir ein Bein."
- "Du erreichst alle deine Ziele."
- "Dein Leben hat heute endlich wieder Sinn."
- "Niemand kann dich aufhalten!"
- "Du hast heute die Chance, dein Leben zu verändern. Nehme sie wahr!"
""",
        variations=[
            Variation(
                probability=0.2,
                prompt="Suggest a random risky activity that one could do in their daily life.",
            ),
        ],
    ),
}


class OpenAiHoroscope(Horoscope):
    def __init__(self, config: OpenAiConfig):
        self._config = config
        openai.api_key = config.token

        self._rate_limiter = RateLimiter()

    def provide_horoscope(
        self, dice: int, context_id: int, user_id: int
    ) -> Optional[str]:
        slots = SLOT_MACHINE_VALUES[dice]

        now = pendulum.now(pendulum.UTC)
        if not self._rate_limiter.can_use(
            context_id=context_id, user_id=user_id, at_time=now
        ):
            return "Du warst heute schon dran."

        result = self._create_horoscope(user_id, slots)
        self._rate_limiter.add_usage(context_id=context_id, user_id=user_id, time=now)
        return result

    def _create_horoscope(
        self, user_id: int, slots: Tuple[Slot, Slot, Slot]
    ) -> Optional[str]:
        if slots == (Slot.LEMON, Slot.LEMON, Slot.LEMON):
            return None

        avenue = _AVENUE_BY_FIRST_SLOT[slots[0]]
        prompt = avenue.build_prompt()
        completion = self._create_completion(user_id, prompt)

        return completion

    def _create_completion(self, user_id: int, prompt: str) -> str:
        response = openai.Completion.create(
            engine="text-davinci-001",
            prompt=prompt,
            temperature=1,
            max_tokens=96,
            top_p=1,
            frequency_penalty=0.35,
            presence_penalty=0.75,
            user=str(user_id),
        )
        return response.choices[0].text
