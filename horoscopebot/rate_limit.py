from datetime import datetime
from typing import Dict


class RateLimiter:
    _usage_time_by_user: Dict[int, datetime]

    def can_use(self, user_id: int, at_time: datetime) -> bool:
        last_usage = self._usage_time_by_user.get(user_id)
        if not last_usage:
            return True

        return at_time.day != last_usage.day

    def add_usage(self, user_id: int, time: datetime):
        self._usage_time_by_user[user_id] = time
