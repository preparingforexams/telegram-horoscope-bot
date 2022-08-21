import logging
from dataclasses import dataclass

from pendulum import DateTime
from rate_limit import Usage

_LOG = logging.getLogger(__name__)


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

        response_id = usage.response_id
        response_message_id = None if response_id is None else int(response_id)

        if message_id == current_message_id - 2:
            return Response("Du warst doch gerade erst dran!")

        if current_message_time.diff(usage.time).in_minutes() < 10:
            return Response(
                "Ich habe dir dein Horoskop vor nicht mal zehn Minuten gegeben."
                " Wirst du alt?"
            )

        reply_message_id = response_message_id or message_id
        if reply_message_id:
            return Response(
                "Du hast dein Schicksal doch vorhin schon erfahren!",
                reply_message_id=reply_message_id,
            )

        return Response("Du warst heute schon dran.")
