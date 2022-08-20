import logging

from pendulum import DateTime

from .. import RateLimitingPolicy, Usage

_LOG = logging.getLogger(__name__)


class DailyLimitRateLimitingPolicy(RateLimitingPolicy):
    def __init__(self, limit: int = 1):
        if limit < 1:
            raise ValueError(
                f"Limit may not be less than or equal to zero, but was {limit}"
            )
        self._limit = limit

    @property
    def requested_history(self) -> int:
        return self._limit

    def get_offending_usage(
        self,
        at_time: DateTime,
        last_usages: list[Usage],
    ) -> Usage | None:
        if len(last_usages) > self._limit:
            raise ValueError(
                f"Got more usages than the requested limit"
                f" ({len(last_usages)} > {self._limit})"
            )

        if len(last_usages) < self._limit:
            _LOG.info("ALLOW: Got fewer usages than the limit")
            # We haven't reached the limit yet
            return None

        for usage in last_usages:
            if usage.time.day != at_time.day:
                _LOG.info("ALLOW: Usage was from another day")
                # One of the usages was from another day
                return None

        _LOG.info("DENY: Usage limit reached")
        # All usages were at the same day as at_time, so we're at the limit
        return last_usages[-1]
