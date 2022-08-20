from __future__ import annotations

import abc
from dataclasses import dataclass

from deprecated.classic import deprecated
from pendulum import DateTime, tz
from pendulum.tz.timezone import Timezone


@dataclass(frozen=True)
class Usage:
    context_id: str
    user_id: str
    time: DateTime
    reference_id: str | None
    response_id: str | None

    def in_timezone(self, timezone: Timezone) -> Usage:
        return Usage(
            context_id=self.context_id,
            user_id=self.user_id,
            time=self.time.in_timezone(timezone),
            reference_id=self.reference_id,
            response_id=self.response_id,
        )


class RateLimitingPolicy(abc.ABC):
    @property
    @abc.abstractmethod
    def requested_history(self) -> int:
        pass

    @abc.abstractmethod
    def get_offending_usage(
        self,
        at_time: DateTime,
        last_usages: list[Usage],
    ) -> Usage | None:
        pass


class RateLimitingRepo(abc.ABC):
    @abc.abstractmethod
    def add_usage(
        self,
        context_id: str,
        user_id: str,
        utc_time: DateTime,
        reference_id: str | None,
        response_id: str | None,
    ):
        pass

    @abc.abstractmethod
    def get_usages(
        self,
        context_id: str,
        user_id: str,
        limit: int = 1,
    ) -> list[Usage]:
        pass


class RateLimiter:
    def __init__(
        self,
        policy: RateLimitingPolicy,
        repo: RateLimitingRepo,
        timezone: Timezone | None = None,
    ):
        self._policy = policy
        self._repo = repo
        self._timezone = timezone or tz.timezone("Europe/Berlin")

    @deprecated("Use get_offending_usage instead")
    def can_use(
        self, context_id: str | int, user_id: str | int, at_time: DateTime
    ) -> bool:
        offending_usage = self.get_offending_usage(
            context_id=context_id,
            user_id=user_id,
            at_time=at_time,
        )
        return offending_usage is None

    def get_offending_usage(
        self,
        context_id: str | int,
        user_id: str | int,
        at_time: DateTime,
    ) -> Usage | None:
        context_id = str(context_id)
        user_id = str(user_id)
        requested_history = self._policy.requested_history
        history = self._repo.get_usages(
            context_id=context_id,
            user_id=user_id,
            limit=requested_history,
        )
        return self._policy.get_offending_usage(
            at_time=at_time,
            last_usages=[usage.in_timezone(self._timezone) for usage in history],
        )

    def add_usage(
        self,
        context_id: str | int,
        user_id: str | int,
        time: DateTime,
        reference_id: str | None = None,
        response_id: str | None = None,
    ):
        context_id = str(context_id)
        user_id = str(user_id)
        utc_time = time.astimezone(tz.UTC)
        self._repo.add_usage(
            context_id=context_id,
            user_id=user_id,
            utc_time=utc_time,
            reference_id=reference_id,
            response_id=response_id,
        )
