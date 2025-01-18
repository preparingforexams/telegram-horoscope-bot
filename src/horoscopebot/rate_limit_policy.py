import logging
from datetime import datetime, timedelta

from rate_limiter import RateLimitingPolicy, Usage

_LOG = logging.getLogger(__name__)


class WeeklyLimitPolicy(RateLimitingPolicy):
    def __init__(self, *, limit: int = 1):
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
        *,
        at_time: datetime,
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

        monday = (at_time - timedelta(days=at_time.weekday())).date()
        for usage in last_usages:
            if usage.time >= monday:
                _LOG.info("DENY: Usage within this week")
                return usage

        _LOG.info("ALLOW: No usage from this week found")
        return None


class UserPassPolicy(RateLimitingPolicy):
    def __init__(
        self,
        fallback: RateLimitingPolicy,
        user_id: int,
        direct_chat_only: bool,
    ):
        self.fallback = fallback
        self.user_id = str(user_id)
        self.direct_chat_only = direct_chat_only

    @property
    def requested_history(self) -> int:
        return self.fallback.requested_history

    def get_offending_usage(
        self,
        *,
        at_time: datetime,
        last_usages: list[Usage],
    ) -> Usage | None:
        if last_usages:
            usage = last_usages[0]
            if usage.user_id == self.user_id:
                if not self.direct_chat_only or (usage.context_id == self.user_id):
                    _LOG.info("ALLOW: Found usage with matching user ID")
                    return None

            _LOG.warning("INDECISION: Usage found, but no match")
        else:
            _LOG.info("INDECISION: No usages found. Falling back.")

        return self.fallback.get_offending_usage(
            at_time=at_time,
            last_usages=last_usages,
        )
