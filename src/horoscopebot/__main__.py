import logging
from datetime import datetime, timedelta, tzinfo
from zoneinfo import ZoneInfo

import sentry_sdk
import uvloop
from bs_config import Env
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from rate_limiter import (
    RateLimiter,
    RateLimitingPolicy,
    RateLimitingRepo,
    Usage,
    policy,
    repo,
)

from horoscopebot.bot import Bot
from horoscopebot.config import (
    Config,
    HoroscopeConfig,
    HoroscopeMode,
    RateLimitConfig,
)
from horoscopebot.dementia_responder import (
    DayDementiaResponder,
    DementiaResponder,
    WeekDementiaResponder,
)
from horoscopebot.horoscope.horoscope import Horoscope
from horoscopebot.horoscope.weekly_openai import WeeklyOpenAiHoroscope
from horoscopebot.rate_limit_policy import UserPassPolicy, WeeklyLimitPolicy
from horoscopebot.telemetry import setup_telemetry

_LOG = logging.getLogger(__package__)


def _setup_logging() -> None:
    LoggingInstrumentor().instrument(set_logging_format=True)
    _LOG.level = logging.INFO


def _setup_sentry(dsn: str | None, release: str) -> None:
    if not dsn:
        _LOG.warning("Sentry DSN not found")
        return

    sentry_sdk.init(
        dsn=dsn,
        release=release,
    )


def _load_horoscope(config: HoroscopeConfig) -> Horoscope:
    match config.mode:
        case HoroscopeMode.OpenAiWeekly:
            return WeeklyOpenAiHoroscope(config.openai)  # type: ignore
        case invalid:
            raise ValueError(f"Invalid horoscope mode: {invalid}")


class _StubRateLimitPolicy(RateLimitingPolicy):
    @property
    def requested_history(self) -> int:
        return 0

    async def get_offending_usage(
        self,
        at_time: datetime,
        last_usages: list[Usage],
    ) -> Usage | None:
        return None


async def _load_rate_limiter(
    timezone: tzinfo,
    config: RateLimitConfig,
    is_weekly: bool,
) -> tuple[RateLimiter, DementiaResponder]:
    match config.rate_limiter_type:
        case "stub":
            return RateLimiter(
                policy=_StubRateLimitPolicy(),
                repo=repo.InMemoryRateLimitingRepo(),
            ), DayDementiaResponder()

    db_config = config.db_config
    repository: RateLimitingRepo

    if db_config is None:
        _LOG.warning("Using in-memory rate limiting repo")
        repository = repo.InMemoryRateLimitingRepo()
    else:
        repository = await repo.PostgresRateLimitingRepo.connect(
            host=db_config.db_host,
            database=db_config.db_name,
            username=db_config.db_user,
            password=db_config.db_password,
            min_connections=1,
            max_connections=2,
        )

    _LOG.info(
        "Admin pass is %s",
        "enabled" if config.admin_pass else "disabled",
    )
    rate_policy: RateLimitingPolicy
    if is_weekly:
        rate_policy = WeeklyLimitPolicy()
    else:
        rate_policy = policy.DailyLimitRateLimitingPolicy(limit=1)

    rate_policy = UserPassPolicy(
        fallback=rate_policy,
        user_id=133399998,
        direct_chat_only=not config.admin_pass,
    )

    dementia_responder: DementiaResponder
    if is_weekly:
        dementia_responder = WeekDementiaResponder()
    else:
        dementia_responder = DayDementiaResponder()

    return RateLimiter(
        policy=rate_policy,
        repo=repository,
        timezone=timezone,
        retention_time=timedelta(days=14),
    ), dementia_responder


async def main() -> None:
    _setup_logging()

    config = Config.from_env(Env.load(include_default_dotenv=True))
    _setup_sentry(config.sentry_dsn, release=config.app_version)
    setup_telemetry(config)

    timezone = ZoneInfo("Europe/Berlin")

    horoscope = _load_horoscope(config.horoscope)
    rate_limiter, dementia_responder = await _load_rate_limiter(
        timezone,
        config.rate_limit,
        is_weekly=config.horoscope.mode == HoroscopeMode.OpenAiWeekly,
    )

    _LOG.info("Doing housekeeping of rate limiter DB")
    await rate_limiter.do_housekeeping()

    _LOG.info("Launching bot")
    bot = Bot(
        config.telegram,
        config.nats,
        horoscope=horoscope,
        rate_limiter=rate_limiter,
        dementia_responder=dementia_responder,
        timezone=timezone,
    )
    await bot.run()


if __name__ == "__main__":
    uvloop.run(main())
