from pendulum import DateTime

from .. import RateLimitingRepo, Usage


class InMemoryRateLimitingRepo(RateLimitingRepo):
    def __init__(self):
        # TODO: this implementation should store more than one usage
        self._usage_time_by_user: dict[str, dict[str, Usage]] = {}

    def get_usages(
        self,
        context_id: str,
        user_id: str,
        limit: int = 1,
    ) -> list[Usage]:
        usage = self._usage_time_by_user.get(context_id, {}).get(user_id)
        return [usage] if usage else []

    def add_usage(
        self,
        context_id: str,
        user_id: str,
        utc_time: DateTime,
        reference_id: str | None,
        response_id: str | None,
    ):
        if context_id not in self._usage_time_by_user:
            self._usage_time_by_user[context_id] = {}

        self._usage_time_by_user[context_id][user_id] = Usage(
            context_id=context_id,
            user_id=user_id,
            time=utc_time,
            reference_id=reference_id,
            response_id=response_id,
        )
