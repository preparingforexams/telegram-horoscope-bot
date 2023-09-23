from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Self, Tuple, Union, overload

from dotenv import dotenv_values


class Env:
    def __init__(self, values: dict[str, str]):
        self._values = values

    @overload
    def get_string(
        self,
        key: str,
        default: str,
    ) -> str:
        pass

    @overload
    def get_string(
        self,
        key: str,
        default: None = None,
    ) -> str | None:
        pass

    def get_string(
        self,
        key: str,
        default: str | None = None,
    ) -> str | None:
        value = self._values.get(key)
        if value is None or not value.strip():
            return default

        return value

    def get_bool(
        self,
        key: str,
        default: bool,
    ) -> bool:
        value = self._values.get(key)
        if value is None:
            return default

        stripped = value.strip()
        if not stripped:
            return default

        return stripped == "true"

    @overload
    def get_int(
        self,
        key: str,
        default: int,
    ) -> int:
        pass

    @overload
    def get_int(
        self,
        key: str,
        default: None = None,
    ) -> int | None:
        pass

    def get_int(
        self,
        key: str,
        default: int | None = None,
    ) -> int | None:
        value = self._values.get(key)
        if value is None or not value.strip():
            return default

        return int(value)

    @overload
    def get_int_list(
        self,
        key: str,
        default: list[int],
    ) -> list[int]:
        pass

    @overload
    def get_int_list(
        self,
        key: str,
        default: None = None,
    ) -> list[int] | None:
        pass

    def get_int_list(
        self,
        key: str,
        default: list[int] | None = None,
    ) -> list[int] | None:
        values = self._values.get(key)

        if values is None or not values.strip():
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


class HoroscopeMode(Enum):
    OpenAi = "openai"
    OpenAiChat = "openai_chat"
    Steffen = "steffen"


@dataclass
class OpenAiConfig:
    debug_mode: bool
    model_name: str
    token: str

    @classmethod
    def from_env(cls, env: Env) -> Self:
        token = env.get_string("OPENAI_TOKEN")
        model_name = env.get_string("OPENAI_MODEL")

        if not (token and model_name):
            raise ValueError("Missing config values")

        return cls(
            debug_mode=env.get_bool("OPENAI_DEBUG", False),
            token=token,
            model_name=model_name,
        )


@dataclass
class HoroscopeConfig:
    mode: HoroscopeMode
    openai: Optional[OpenAiConfig]

    @classmethod
    def from_env(cls, env: Env) -> Self:
        mode = HoroscopeMode(env.get_string("HOROSCOPE_MODE", default="steffen"))
        if mode in (HoroscopeMode.OpenAi, HoroscopeMode.OpenAiChat):
            openai = OpenAiConfig.from_env(env)
        else:
            openai = None

        return cls(
            mode=mode,
            openai=openai,
        )


@dataclass
class EventPublisherConfig:
    mode: str
    project_id: str | None
    topic_name: str | None

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            mode=env.get_string("EVENT_PUBLISHER_MODE", "stub"),
            project_id=env.get_string("GOOGLE_CLOUD_PROJECT"),
            topic_name=env.get_string("PUBSUB_HOROSCOPE_TOPIC"),
        )


@dataclass
class RateLimitConfig:
    rate_limiter_type: str
    rate_limit_file: str | None

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            rate_limiter_type=env.get_string(
                "RATE_LIMITER_TYPE",
                default="actual",
            ),
            rate_limit_file=env.get_string("RATE_LIMIT_FILE"),
        )


@dataclass
class TelegramConfig:
    enabled_chats: List[int]
    token: str

    @classmethod
    def from_env(cls, env: Env) -> Self:
        token = env.get_string("TELEGRAM_TOKEN")

        if not token:
            raise ValueError("Missing Telegram token")

        return cls(
            enabled_chats=env.get_int_list(
                "TELEGRAM_ENABLED_CHATS",
                [133399998],
            ),
            token=token,
        )


@dataclass
class Config:
    app_version: str
    timezone_name: str
    horoscope: HoroscopeConfig
    event_publisher: EventPublisherConfig
    rate_limit: RateLimitConfig
    sentry_dsn: Optional[str]
    telegram: TelegramConfig

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            app_version=env.get_string("BUILD_SHA", "debug"),
            timezone_name=env.get_string(
                "TIMEZONE_NAME",
                "Europe/Berlin",
            ),
            horoscope=HoroscopeConfig.from_env(env),
            event_publisher=EventPublisherConfig.from_env(env),
            rate_limit=RateLimitConfig.from_env(env),
            sentry_dsn=env.get_string("SENTRY_DSN"),
            telegram=TelegramConfig.from_env(env),
        )
