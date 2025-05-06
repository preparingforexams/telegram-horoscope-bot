import logging
from dataclasses import dataclass
from enum import Enum
from typing import Self

from bs_config import Env

_LOG = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    db_host: str
    db_name: str
    db_user: str
    db_password: str

    @classmethod
    def from_env(cls, env: Env) -> Self | None:
        try:
            return cls(
                db_host=env.get_string("HOST", required=True),
                db_name=env.get_string("NAME", required=True),
                db_user=env.get_string("USER", required=True),
                db_password=env.get_string("PASSWORD", required=True),
            )
        except ValueError as e:
            _LOG.warning("Could not load database config: %s", e)
            return None


class HoroscopeMode(Enum):
    OpenAiChat = "openai_chat"
    OpenAiWeekly = "openai_weekly"
    Steffen = "steffen"


@dataclass
class OpenAiConfig:
    debug_mode: bool
    image_model_name: str
    model_name: str
    token: str

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            debug_mode=env.get_bool("DEBUG", default=False),
            token=env.get_string("TOKEN", required=True),
            image_model_name=env.get_string("IMAGE_MODEL", required=True),
            model_name=env.get_string("MODEL", required=True),
        )


@dataclass
class HoroscopeConfig:
    mode: HoroscopeMode
    openai: OpenAiConfig | None

    @classmethod
    def from_env(cls, env: Env) -> Self:
        mode = HoroscopeMode(env.get_string("HOROSCOPE_MODE", default="steffen"))

        if mode in [HoroscopeMode.OpenAiChat, HoroscopeMode.OpenAiWeekly]:
            openai = OpenAiConfig.from_env(env.scoped("OPENAI_"))
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
    db_config: DatabaseConfig | None
    admin_pass: bool

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            rate_limiter_type=env.get_string(
                "RATE_LIMITER_TYPE",
                default="actual",
            ),
            db_config=DatabaseConfig.from_env(env.scoped("DB_")),
            admin_pass=env.get_bool("RATE_LIMIT_ADMIN_PASS", default=True),
        )


@dataclass
class TelegramConfig:
    enabled_chats: list[int]
    token: str

    @classmethod
    def from_env(cls, env: Env) -> Self:
        token = env.get_string("TELEGRAM_TOKEN", required=True)

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
    enable_telemetry: bool
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
                "APP_VERSION",
                default="debug",
            ),
            enable_telemetry=env.get_bool(
                "ENABLE_TELEMETRY",
                default=False,
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
