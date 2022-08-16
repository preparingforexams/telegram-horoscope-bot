import logging
from typing import List

from pendulum import DateTime

from .. import RateLimitingPolicy

_LOG = logging.getLogger(__name__)


class DailyLimitRateLimitingPolicy(RateLimitingPolicy):
    def __init__(self, limit: int = 1):
        self._limit = limit

    @property
    def requested_history(self) -> int:
        return self._limit

    def can_use(
        self,
        context_id: int,
        user_id: int,
        at_time: DateTime,
        last_usages: List[DateTime],
    ) -> bool:
        if len(last_usages) < self._limit:
            _LOG.info("ALLOW: Got fewer usages than the limit")
            # We haven't reached the limit yet
            return True

        for usage in last_usages:
            if usage.day != at_time.day:
                _LOG.info("ALLOW: Usage was from another day")
                # One of the usages was from another day
                return True

        _LOG.info("DENY: Usage limit reached")
        # All usages were at the same day as at_time, so we're at the limit
        return False
