from dataclasses import dataclass

from horoscopebot.rate_limit import Usage


@dataclass
class Response:
    text: str
    reply_message_id: int | None = None


class DementiaResponder:
    def create_response(
        self,
        current_message_id: int,
        usage: Usage,
    ) -> Response:
        # TODO: sophistication
        return Response(text="Du warst heute schon dran.")
