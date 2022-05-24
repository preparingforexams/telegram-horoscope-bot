from typing import Optional

from .horoscope import Horoscope, Slot, SLOT_MACHINE_VALUES

_HOROSCOPE_BY_COMBINATION = {
    (Slot.LEMON, Slot.LEMON, Slot.GRAPE): "Bleib einfach liegen.",
    (
        Slot.LEMON,
        Slot.LEMON,
        Slot.BAR,
    ): "Morgens zwei Pfannen in die Eier und alles wird gut.",
    (Slot.LEMON, Slot.LEMON, Slot.SEVEN): "Der Tag nimmt eine positive Wendung.",
    (Slot.LEMON, Slot.GRAPE, Slot.LEMON): "Heute wird phänomenal enttäuschend.",
    (
        Slot.LEMON,
        Slot.GRAPE,
        Slot.GRAPE,
    ): "Dein Lebenslauf erhält heute einen neuen Eintrag.",
    (Slot.LEMON, Slot.GRAPE, Slot.BAR): "Dreh einfach wieder um.",
    (Slot.LEMON, Slot.GRAPE, Slot.SEVEN): "Weißt du noch, diese eine Deadline?",
    (Slot.LEMON, Slot.BAR, Slot.LEMON): "Du verläufst dich heute in deiner Wohnung.",
    (Slot.LEMON, Slot.BAR, Slot.BAR): "Der Abwasch entwickelt intelligentes Leben.",
    (Slot.LEMON, Slot.BAR, Slot.GRAPE): "Du stößt dir den kleinen Zeh.",
    (Slot.LEMON, Slot.BAR, Slot.SEVEN): "Bad hair day.",
    (
        Slot.LEMON,
        Slot.SEVEN,
        Slot.LEMON,
    ): "Deine Freunde machen sich über deine Frisur lustig.",
    (
        Slot.LEMON,
        Slot.SEVEN,
        Slot.BAR,
    ): "Ein platter Autoreifen verändert heute dein Leben.",
    (Slot.LEMON, Slot.SEVEN, Slot.GRAPE): "Im Kühlschrank gibt es nichts zu sehen.",
    (
        Slot.LEMON,
        Slot.SEVEN,
        Slot.SEVEN,
    ): "Völlig übermüdet manövrierst du dich doch noch elegant durch den Tag in Richtung Bett.",
    (
        Slot.GRAPE,
        Slot.LEMON,
        Slot.LEMON,
    ): "Du fängst schwach an, lässt dann aber auch stark nach.",
    (
        Slot.GRAPE,
        Slot.LEMON,
        Slot.GRAPE,
    ): "Eine sprechende Katze gibt dir einen guten Rat.",
    (
        Slot.GRAPE,
        Slot.LEMON,
        Slot.BAR,
    ): "Du wirst heute Zeuge eines prägenden Ereignisses.",
    (
        Slot.GRAPE,
        Slot.LEMON,
        Slot.SEVEN,
    ): "Eine Melone aus dem 3. Stock verfehlt dich haarscharf.",
    (Slot.GRAPE, Slot.GRAPE, Slot.LEMON): "7 Jahre Arbeit machen sich heute bezahlt.",
    (Slot.GRAPE, Slot.GRAPE, Slot.GRAPE): "Trauben stampfen!",
    (
        Slot.GRAPE,
        Slot.GRAPE,
        Slot.BAR,
    ): "Es sind nur 23 Dohlen, doch du witterst Gefahr.",
    (
        Slot.GRAPE,
        Slot.GRAPE,
        Slot.SEVEN,
    ): "Arrangier dich mit einem Fisch in der Badewanne.",
    (
        Slot.GRAPE,
        Slot.BAR,
        Slot.LEMON,
    ): "Jemand erzählt dir, dass Enten eigentlich gar keine Tiere sind.",
    (
        Slot.GRAPE,
        Slot.BAR,
        Slot.GRAPE,
    ): "Du verlierst dich heute in einer Diskussion über Elefantenbabys.",
    (
        Slot.GRAPE,
        Slot.BAR,
        Slot.BAR,
    ): "Ein spanischer Geheimagent reibt dich mit Apfelsaft ein und die Polizei schaut tatenlos zu.",
    (Slot.GRAPE, Slot.BAR, Slot.SEVEN): "Eine Rinderherde nimmt dir die Vorfahrt.",
    (
        Slot.GRAPE,
        Slot.SEVEN,
        Slot.LEMON,
    ): "Etwas verschwindet heute plötzlich und du zweifelst an deiner mentalen Verfassung.",
    (Slot.GRAPE, Slot.SEVEN, Slot.GRAPE): "Deine linke Socke hat heute Abend ein Loch.",
    (Slot.GRAPE, Slot.SEVEN, Slot.BAR): "Ein Eichhörnchen klaut dein Portemonnaie.",
    (
        Slot.GRAPE,
        Slot.SEVEN,
        Slot.SEVEN,
    ): "Du vergisst deine Schlüssel und wirst Millionär.",
    (
        Slot.BAR,
        Slot.LEMON,
        Slot.LEMON,
    ): "Eine Bierdusche am späten Nachmittag wird dich erquicken.",
    (Slot.BAR, Slot.LEMON, Slot.GRAPE): "Heute wirst du dir einen Kater antrinken.",
    (Slot.BAR, Slot.LEMON, Slot.BAR): "Heute hast du einen Kater.",
    (
        Slot.BAR,
        Slot.LEMON,
        Slot.SEVEN,
    ): "Du wachst besoffen auf und schläfst besoffen ein.",
    (Slot.BAR, Slot.GRAPE, Slot.LEMON): "Du erreichst heute deinen Wunschpegel.",
    (Slot.BAR, Slot.GRAPE, Slot.GRAPE): "Heute hilft auch saufen nicht mehr.",
    (Slot.BAR, Slot.GRAPE, Slot.BAR): "Alkohol löst heute die meisten deiner Probleme.",
    (Slot.BAR, Slot.GRAPE, Slot.SEVEN): "Heute wird vergleichsweise nüchtern.",
    (Slot.BAR, Slot.BAR, Slot.LEMON): "Kenning West kommt heute aus der Ferne, alder.",
    (
        Slot.BAR,
        Slot.BAR,
        Slot.GRAPE,
    ): "Ein Überraschungstrichter gibt dir neuen Schwung.",
    (Slot.BAR, Slot.BAR, Slot.BAR): "Saufen ist gesund.",
    (
        Slot.BAR,
        Slot.BAR,
        Slot.SEVEN,
    ): "2 Bier sind 1 Bier und dann darfst du auch noch fahren.",
    (
        Slot.BAR,
        Slot.SEVEN,
        Slot.LEMON,
    ): "Egal wie viel du heute trinkst, Torben trinkt mehr.",
    (Slot.BAR, Slot.SEVEN, Slot.GRAPE): "Torben trinkt zu viel Alkohol.",
    (Slot.BAR, Slot.SEVEN, Slot.BAR): "Die Leber meldet sich.",
    (Slot.BAR, Slot.SEVEN, Slot.SEVEN): "Der morgendliche Kurze wird sich rächen.",
    (
        Slot.SEVEN,
        Slot.LEMON,
        Slot.LEMON,
    ): "Ausgeschlafen begibst du dich heute in die Abgründe deines Daseins.",
    (Slot.SEVEN, Slot.LEMON, Slot.GRAPE): "Du triffst heute dein Idol.",
    (Slot.SEVEN, Slot.LEMON, Slot.BAR): "Heute lebst du ein Leben wie Larry.",
    (Slot.SEVEN, Slot.LEMON, Slot.SEVEN): "Heute gibt dir jemand eine zweite Chance.",
    (Slot.SEVEN, Slot.GRAPE, Slot.LEMON): "Sag niemals niemals. Mist.",
    (
        Slot.SEVEN,
        Slot.GRAPE,
        Slot.GRAPE,
    ): "Entweder du hörst heute auf zu rauchen oder du fängst damit an.",
    (Slot.SEVEN, Slot.GRAPE, Slot.BAR): "Lass alles liegen und greif nach den Sternen.",
    (Slot.SEVEN, Slot.GRAPE, Slot.SEVEN): "Lass dich nicht unterkriegen.",
    (Slot.SEVEN, Slot.BAR, Slot.LEMON): "Alles wird gut.",
    (
        Slot.SEVEN,
        Slot.BAR,
        Slot.GRAPE,
    ): "Geh ein Risiko ein, du wirst es nicht bereuen.",
    (Slot.SEVEN, Slot.BAR, Slot.BAR): "Bereite dich auf etwas großes vor.",
    (Slot.SEVEN, Slot.BAR, Slot.SEVEN): "Heute siehst du einen Ballon und freust dich.",
    (
        Slot.SEVEN,
        Slot.SEVEN,
        Slot.LEMON,
    ): "Du hättest heute alles schaffen können, aber brichst dir ein Bein.",
    (Slot.SEVEN, Slot.SEVEN, Slot.GRAPE): "Du erreichst alle deine Ziele.",
    (Slot.SEVEN, Slot.SEVEN, Slot.BAR): "Dein Leben hat heute endlich wieder Sinn.",
    (Slot.SEVEN, Slot.SEVEN, Slot.SEVEN): "Niemand kann dich aufhalten!",
}


class SteffenHoroscope(Horoscope):
    def provide_horoscope(
        self, dice: int, context_id: int, user_id: int
    ) -> Optional[str]:
        slots = SLOT_MACHINE_VALUES[dice]
        return _HOROSCOPE_BY_COMBINATION.get(slots)
