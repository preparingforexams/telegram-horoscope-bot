from dataclasses import dataclass
from enum import Enum
from typing import Self

from bs_config import Env


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
            debug_mode=env.get_bool("OPENAI_DEBUG", default=False),
            token=token,
            model_name=model_name,
        )


@dataclass
class HoroscopeConfig:
    mode: HoroscopeMode
    openai: OpenAiConfig | None

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
            mode=env.get_string("EVENT_PUBLISHER_MODE", default="stub"),
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
    enabled_chats: list[int]
    token: str

    @classmethod
    def from_env(cls, env: Env) -> Self:
        token = env.get_string("TELEGRAM_TOKEN")

        if not token:
            raise ValueError("Missing Telegram token")

        return cls(
            enabled_chats=env.get_int_list(
                "TELEGRAM_ENABLED_CHATS",
                default=[133399998],
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
    sentry_dsn: str | None
    telegram: TelegramConfig

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            app_version=env.get_string(
                "BUILD_SHA",
                default="debug",
            ),
            timezone_name=env.get_string(
                "TIMEZONE_NAME",
                default="Europe/Berlin",
            ),
            horoscope=HoroscopeConfig.from_env(env),
            event_publisher=EventPublisherConfig.from_env(env),
            rate_limit=RateLimitConfig.from_env(env),
            sentry_dsn=env.get_string("SENTRY_DSN"),
            telegram=TelegramConfig.from_env(env),
        )
