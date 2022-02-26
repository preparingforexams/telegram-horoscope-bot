from datetime import datetime
from typing import Dict


class RateLimiter:
    def __init__(self):
        self._usage_time_by_user: Dict[int, Dict[int, datetime]] = {}

    def can_use(self, context_id: int, user_id: int, at_time: datetime) -> bool:
        last_usage = self._usage_time_by_user.get(context_id, {}).get(user_id)
        if not last_usage:
            return True

        return at_time.day != last_usage.day

    def add_usage(self, context_id: int, user_id: int, time: datetime):
        if context_id not in self._usage_time_by_user:
            self._usage_time_by_user[context_id] = {}

        self._usage_time_by_user[context_id][user_id] = time
