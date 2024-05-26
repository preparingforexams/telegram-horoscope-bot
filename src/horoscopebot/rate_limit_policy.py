import logging
from datetime import datetime

from rate_limiter import RateLimitingPolicy, Usage

_LOG = logging.getLogger(__name__)


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
        if last_usages:
            usage = last_usages[0]
            if usage.user_id == self.user_id and usage.context_id == str(self.user_id):
                _LOG.info("ALLOW: Found usage with matching user ID and context ID")
                return None
        else:
            _LOG.info("INDECISION: No usages found. Falling back.")

        return self.fallback.get_offending_usage(at_time, last_usages)
