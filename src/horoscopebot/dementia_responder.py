import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from rate_limiter import Usage

_LOG = logging.getLogger(__name__)


@dataclass
class Response:
    text: str
    reply_message_id: int | None = None


class DementiaResponder:
    def create_response(
        self,
        current_message_id: int,
        current_message_time: datetime,
        usage: Usage,
    ) -> Response:
        reference_id = usage.reference_id
        message_id = None if reference_id is None else int(reference_id)

        response_id = usage.response_id
        response_message_id = None if response_id is None else int(response_id)

        if message_id == current_message_id - 2:
            return Response("Dein Horoskop steht direkt über deiner Slot Machine 🎰!")

        time_diff = abs(current_message_time - usage.time)
        if time_diff < timedelta(minutes=10):
            return Response(
                "Ich habe dir dein Horoskop vor nicht mal zehn Minuten gegeben."
                " Wirst du alt?"
            )

        reply_message_id = response_message_id or message_id
        if reply_message_id:
            text = "Du hast dein Schicksal doch vorhin schon erfahren!"

            if current_message_time.hour > 7 and usage.time.hour < 3:
                text = (
                    "Hast du nen Filmriss?"
                    " Dein Horoskop hast du gestern Nacht schon erfragt!"
                )
            elif time_diff > timedelta(hours=4) and usage.time.hour < 11:
                text = "Du hast dein Schicksal doch heute Morgen schon erfahren!"
            elif usage.time.hour < 15 and current_message_time.hour > 18:
                text = "Es wird auch abends nicht besser."

            return Response(
                text,
                reply_message_id=reply_message_id,
            )

        return Response("Du warst heute schon dran.")
