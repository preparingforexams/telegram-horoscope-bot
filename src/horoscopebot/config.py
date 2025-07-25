import logging
from dataclasses import dataclass
from enum import Enum
from typing import Literal, Self, cast

from bs_config import Env
from bs_nats_updater import NatsConfig

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
    OpenAiWeekly = "openai_weekly"


type OpenAiImageQuality = Literal["low", "medium", "high"]
type OpenAiModerationLevel = Literal["auto", "low"]


@dataclass
class OpenAiConfig:
    debug_mode: bool
    image_model_name: str
    image_moderation_level: OpenAiModerationLevel
    image_quality: OpenAiImageQuality
    model_name: str
    token: str

    @staticmethod
    def _validate_image_quality(value: str) -> OpenAiImageQuality:
        if value not in ["low", "medium", "high"]:
            raise ValueError(f"Invalid image quality: {value}")
        return cast(OpenAiImageQuality, value)

    @staticmethod
    def _validate_image_moderation_level(value: str) -> OpenAiModerationLevel:
        if value not in ["low", "auto"]:
            raise ValueError(f"Invalid image moderation level: {value}")
        return cast(OpenAiModerationLevel, value)

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            debug_mode=env.get_bool("DEBUG", default=False),
            token=env.get_string("TOKEN", required=True),
            image_model_name=env.get_string("IMAGE_MODEL", required=True),
            image_moderation_level=cls._validate_image_moderation_level(
                env.get_string("IMAGE_MODERATION_LEVEL", default="low"),
            ),
            image_quality=cls._validate_image_quality(
                env.get_string("IMAGE_QUALITY", default="medium"),
            ),
            model_name=env.get_string("MODEL", required=True),
        )


@dataclass
class HoroscopeConfig:
    mode: HoroscopeMode
    openai: OpenAiConfig | None

    @classmethod
    def from_env(cls, env: Env) -> Self:
        mode = HoroscopeMode(env.get_string("HOROSCOPE_MODE", default="openai_weekly"))

        if mode in [HoroscopeMode.OpenAiWeekly]:
            openai = OpenAiConfig.from_env(env.scoped("OPENAI_"))
        else:
            openai = None

        return cls(
            mode=mode,
            openai=openai,
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
    nats: NatsConfig
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
            nats=NatsConfig.from_env(env.scoped("NATS_")),
            rate_limit=RateLimitConfig.from_env(env),
            sentry_dsn=env.get_string("SENTRY_DSN"),
            telegram=TelegramConfig.from_env(env),
        )
