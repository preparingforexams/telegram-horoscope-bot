import random
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Tuple

import openai
import pendulum
from horoscopebot.config import OpenAiConfig

from .horoscope import Horoscope, SLOT_MACHINE_VALUES, Slot
from ..rate_limit import RateLimiter, policy, repo

_BASE_PROMPT = (
    r"Write a creative and witty horoscope for the day without mentioning a specific "
    r"zodiac sign. The horoscope must be written in German. The horoscope should "
    r"consist of two short sentences. "
    r'Use "Du" instead of "Sie".'
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
        base_prompt=(
            f"{_BASE_PROMPT}\n\nThe horoscope should encourage alcohol consumption."
        ),
        variations=[
            Variation(
                probability=0.3,
                prompt="Include a reference to Fabienne's excessive alcoholism.",
            ),
            Variation(
                probability=0.05,
                prompt="Suggest drinking Dousnbier",
            ),
            Variation(
                probability=0.05,
                prompt="Suggest drinking Hugo",
            ),
            Variation(
                probability=0.05,
                prompt="Suggest drinking Rakete",
            ),
            Variation(
                probability=0.1,
                prompt="Suggest some random positive effects of alcohol on the liver.",
            ),
            Variation(
                probability=0.05,
                prompt="Bully the reader for their lack of discipline.",
            ),
        ],
    ),
    Slot.GRAPE: Avenue(
        base_prompt=(
            "Beschreibe in zwei kurzen Sätzen eine sehr unerwartete Begebenheit, "
            "die jemandem heute in seinem Alltag passieren wird. Schreibe in der "
            "zweiten Person. Die Begebenheit sollte vollkommen undenkbar sein."
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
                prompt=(
                    "Suggest a random risky activity that one "
                    "could do in their daily life."
                ),
            ),
        ],
    ),
}

_KANU_GEGGO: Dict[int, str] = {
    # Born
    133399998: (
        "Heute verbrennst du dich in der Sonne. "
        "Darauf solltest du erstmal ein Bembel trinken."
    ),
    # Katharine
    1365395775: (
        "Dein Kater verschwindet wie von selbst! "
        "Exakt in dem Moment in dem du kenterst."
        " Trink über den Schock doch einfach mal ein Dösli Bembel!"
    ),
    # Alexander Holt
    444493856: (
        "Du wirst heute vor begeistertem Publikum hingetrichtet."
        " Born freut sich über das Dösli Bembel, das du ihm gleich bringst."
    ),
    # Barbara Salesch
    1093712857: (
        "Du hättest mit Kanusaufen kommen sollen! "
        "Jetzt musst du zu Hause alleine trinken."
    ),
    # Torge
    139656428: (
        "Überwinde deine Berührungsängste mit dem Alkohol und trink noch ein Bier über "
        "den Durst! Es wird dir guttun."
        " Born freut sich über das Dösli Bembel, das du ihm gleich bringst."
    ),
    # Tischler
    1603772877: (
        "Der Ouzo ist vielleicht seit gestern leer, aber auch für einen anderen Schnaps"
        " für deine guten Freunde muss heute Zeit sein."
    ),
    # Patt
    166418774: (
        "Das Paddel in die eine Hand, das Bier in die andere, und dann Vollgas! "
        "Heute hat der Zug keine Bremsen und der Trichter ist dein bester Freund."
    ),
}


class OpenAiHoroscope(Horoscope):
    def __init__(self, config: OpenAiConfig):
        self._config = config
        openai.api_key = config.token

        self._rate_limiter = RateLimiter(
            policy=policy.DailyLimitRateLimitingPolicy(limit=1),
            repo=repo.InMemoryRateLimitingRepo(),
        )

    def provide_horoscope(
        self, dice: int, context_id: int, user_id: int
    ) -> Optional[str]:
        slots = SLOT_MACHINE_VALUES[dice]

        now = pendulum.now(pendulum.UTC)
        if not self._rate_limiter.can_use(
            context_id=context_id, user_id=user_id, at_time=now
        ):
            if self._is_lemons(slots):
                # The other bot will send the picture anyway, so we'll be quiet
                return None
            return "Du warst heute schon dran."

        result = self._create_horoscope(user_id, slots, now)
        self._rate_limiter.add_usage(context_id=context_id, user_id=user_id, time=now)
        return result

    @staticmethod
    def _is_lemons(slots: Tuple[Slot, Slot, Slot]) -> bool:
        return slots == (Slot.LEMON, Slot.LEMON, Slot.LEMON)

    def _create_horoscope(
        self,
        user_id: int,
        slots: Tuple[Slot, Slot, Slot],
        time: datetime,
    ) -> Optional[str]:
        geggo = self._make_geggo(user_id, time)
        if geggo:
            return geggo

        if self._is_lemons(slots):
            return None

        avenue = _AVENUE_BY_FIRST_SLOT[slots[0]]
        prompt = avenue.build_prompt()
        completion = self._create_completion(user_id, prompt)
        return completion

    def _make_geggo(self, user_id: int, time: datetime) -> Optional[str]:
        date = time.date()
        if date.year == 2022 and date.month == 5 and date.day == 28:
            return _KANU_GEGGO.get(user_id)

        return None

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
