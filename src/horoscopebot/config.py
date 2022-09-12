from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Tuple, Optional, Union

from dotenv import dotenv_values


class Env:
    def __init__(self, values: Dict[str, str]):
        self._values = values

    def get_string(
        self,
        key: str,
        default: Optional[str] = None,
        required: bool = True,
    ) -> Optional[str]:
        value = self._values.get(key, default)
        if required:
            if value is None:
                raise ValueError(f"Value for {key} is missing")
            if not value.strip():
                raise ValueError(f"Value for {key} is blank")

        return value

    def get_int(
        self,
        key: str,
        default: Optional[int] = None,
        required: bool = True,
    ) -> Optional[int]:
        value = self._values.get(key)
        if required and default is None:
            if value is None:
                raise ValueError(f"Value for {key} is missing")
            if not value.strip():
                raise ValueError(f"Value for {key} is blank")
        elif value is None or not value.strip() and default is not None:
            return default

        return int(value)

    def get_int_list(
        self,
        key: str,
        default: Optional[List[int]] = None,
        required: bool = True,
    ) -> Optional[List[int]]:
        values = self._values.get(key)
        if required and default is None:
            if values is None:
                raise ValueError(f"Value for {key} is missing")
            if not values.strip():
                raise ValueError(f"Value for {key} is blank")
        elif values is None or not values.strip() and default is not None:
            return default

        return [int(value) for value in values.split(",")]


def _load_env(name: str) -> dict:
    if not name:
        return dotenv_values(".env")
    else:
        return dotenv_values(f".env.{name}")


def load_env(names: Union[str, Tuple[str, ...]]) -> Env:
    result = {}

    if isinstance(names, str):
        result.update(_load_env(names))
    elif isinstance(names, tuple):
        for name in names:
            result.update(_load_env(name))
    else:
        raise ValueError(f"Invalid .env names: {names}")

    from os import environ

    result.update(environ)

    return Env(result)


@dataclass
class Config:
    app_version: str
    horoscope: HoroscopeConfig
    event_publisher: EventPublisherConfig
    rate_limit: RateLimitConfig
    sentry_dsn: Optional[str]
    telegram: TelegramConfig

    @classmethod
    def from_env(cls, env: Env) -> Config:
        return cls(
            app_version=env.get_string("BUILD_SHA", "debug"),  # type: ignore
            horoscope=HoroscopeConfig.from_env(env),
            event_publisher=EventPublisherConfig.from_env(env),
            rate_limit=RateLimitConfig.from_env(env),
            sentry_dsn=env.get_string("SENTRY_DSN", required=False),
            telegram=TelegramConfig.from_env(env),
        )


class HoroscopeMode(Enum):
    OpenAi = "openai"
    Steffen = "steffen"


@dataclass
class HoroscopeConfig:
    mode: HoroscopeMode
    openai: Optional[OpenAiConfig]

    @classmethod
    def from_env(cls, env: Env) -> HoroscopeConfig:
        mode = HoroscopeMode(env.get_string("HOROSCOPE_MODE", default="steffen"))
        openai = OpenAiConfig.from_env(env) if mode == HoroscopeMode.OpenAi else None

        return cls(
            mode=mode,
            openai=openai,
        )


@dataclass
class OpenAiConfig:
    debug_mode: bool
    token: str

    @classmethod
    def from_env(cls, env: Env) -> OpenAiConfig:
        return cls(
            debug_mode=env.get_string("OPENAI_DEBUG", "false") == "true",
            token=env.get_string("OPENAI_TOKEN"),  # type:ignore
        )


@dataclass
class EventPublisherConfig:
    mode: str
    project_id: str | None
    topic_name: str | None

    @classmethod
    def from_env(cls, env: Env) -> EventPublisherConfig:
        return cls(
            mode=env.get_string("EVENT_PUBLISHER_MODE", "stub"),  # type: ignore
            project_id=env.get_string("GOOGLE_CLOUD_PROJECT", required=False),
            topic_name=env.get_string("PUBSUB_HOROSCOPE_TOPIC", required=False),
        )


@dataclass
class RateLimitConfig:
    rate_limit_file: str | None

    @classmethod
    def from_env(cls, env: Env) -> RateLimitConfig:
        return cls(
            rate_limit_file=env.get_string(
                "RATE_LIMIT_FILE", required=False
            ),  # type: ignore
        )


@dataclass
class TelegramConfig:
    enabled_chats: List[int]
    token: str

    @classmethod
    def from_env(cls, env: Env) -> TelegramConfig:
        return cls(
            enabled_chats=env.get_int_list(  # type:ignore
                "TELEGRAM_ENABLED_CHATS",
                [133399998],
            ),
            token=env.get_string("TELEGRAM_API_KEY"),  # type:ignore
        )
