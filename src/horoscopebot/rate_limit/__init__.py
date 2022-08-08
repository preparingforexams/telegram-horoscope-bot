import abc
from typing import Optional, List

from pendulum import DateTime, tz

from datetime import tzinfo


class RateLimitingPolicy(abc.ABC):
    @property
    @abc.abstractmethod
    def requested_history(self) -> int:
        pass

    @abc.abstractmethod
    def can_use(
        self,
        context_id: int,
        user_id: int,
        at_time: DateTime,
        last_usages: List[DateTime],
    ) -> bool:
        pass


class RateLimitingRepo(abc.ABC):
    @abc.abstractmethod
    def add_usage(self, context_id: int, user_id: int, utc_time: DateTime):
        pass

    @abc.abstractmethod
    def get_usages(
        self,
        context_id: int,
        user_id: int,
        limit: int = 1,
    ) -> List[DateTime]:
        pass


class RateLimiter:
    def __init__(
        self,
        policy: RateLimitingPolicy,
        repo: RateLimitingRepo,
        timezone: Optional[tzinfo] = None,
    ):
        self._policy = policy
        self._repo = repo
        self._timezone = timezone or tz.timezone("Europe/Berlin")

    def can_use(self, context_id: int, user_id: int, at_time: DateTime) -> bool:
        requested_history = self._policy.requested_history
        history = self._repo.get_usages(
            context_id=context_id,
            user_id=user_id,
            limit=requested_history,
        )
        return self._policy.can_use(
            context_id=context_id,
            user_id=user_id,
            at_time=at_time.astimezone(self._timezone),
            last_usages=[usage.astimezone(self._timezone) for usage in history],
        )

    def add_usage(self, context_id: int, user_id: int, time: DateTime):
        utc_time = time.astimezone(tz.UTC)
        self._repo.add_usage(
            context_id=context_id,
            user_id=user_id,
            utc_time=utc_time,
        )
