from typing import Dict, List

from pendulum import DateTime
from .. import RateLimitingRepo


class InMemoryRateLimitingRepo(RateLimitingRepo):
    def __init__(self):
        # TODO: this implementation should store more than one usage
        self._usage_time_by_user: Dict[int, Dict[int, DateTime]] = {}

    def get_usages(
        self,
        context_id: int,
        user_id: int,
        limit: int = 1,
    ) -> List[DateTime]:
        usage_time = self._usage_time_by_user.get(context_id, {}).get(user_id)
        return [usage_time] if usage_time else []

    def add_usage(self, context_id: int, user_id: int, utc_time: DateTime):
        if context_id not in self._usage_time_by_user:
            self._usage_time_by_user[context_id] = {}

        self._usage_time_by_user[context_id][user_id] = utc_time
