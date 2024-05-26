from datetime import datetime

from rate_limiter import RateLimitingPolicy, Usage


class UserPassPolicy(RateLimitingPolicy):

    def __init__(self, fallback: RateLimitingPolicy, user_id: int):
        self.fallback = fallback
        self.user_id = user_id

    @property
    def requested_history(self) -> int:
        return self.fallback.requested_history

    def get_offending_usage(
        self,
        at_time: datetime,
        last_usages: list[Usage],
    ) -> Usage | None:
        if last_usages and last_usages[0].user_id == self.user_id:
            return None

        return self.fallback.get_offending_usage(at_time, last_usages)
