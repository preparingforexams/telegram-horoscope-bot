from dataclasses import dataclass
from datetime import timedelta

from pendulum import DateTime

from horoscopebot.rate_limit import Usage


@dataclass
class Response:
    text: str
    reply_message_id: int | None = None


class DementiaResponder:
    def create_response(
        self,
        current_message_id: int,
        current_message_time: DateTime,
        usage: Usage,
    ) -> Response:
        reference_id = usage.reference_id
        message_id = None if reference_id is None else int(reference_id)
        if message_id == current_message_id - 2:
            return Response("Du warst doch gerade erst dran!")

        if abs(current_message_time - usage.time) < timedelta(minutes=10):
            return Response(
                "Ich habe dir dein Horoskop vor nicht mal zehn Minuten gegeben."
                " Wirst du alt?"
            )

        if message_id is not None:
            # TODO: use horoscope message ID
            return Response(
                "Du hast dein Schicksal doch vorhin schon erfahren",
                reply_message_id=message_id,
            )

        return Response("Du warst heute schon dran.")
