import logging
from pathlib import Path
from typing import Optional

import sentry_sdk

from horoscopebot.bot import Bot
from horoscopebot.config import (
    load_env,
    Config,
    HoroscopeConfig,
    HoroscopeMode,
    RateLimitConfig,
)
from horoscopebot.horoscope.horoscope import Horoscope
from horoscopebot.horoscope.openai import OpenAiHoroscope
from horoscopebot.horoscope.steffen import SteffenHoroscope
from horoscopebot.rate_limit import RateLimiter, repo, policy, RateLimitingRepo

_LOG = logging.getLogger(__package__)


def _setup_logging():
    logging.basicConfig()
    _LOG.level = logging.INFO


def _setup_sentry(dsn: Optional[str], release: str):
    if not dsn:
        _LOG.warning("Sentry DSN not found")
        return

    sentry_sdk.init(
        dsn=dsn,
        release=release,
    )


def _load_horoscope(config: HoroscopeConfig) -> Horoscope:
    if config.mode == HoroscopeMode.Steffen:
        return SteffenHoroscope()
    elif config.mode == HoroscopeMode.OpenAi:
        return OpenAiHoroscope(config.openai)  # type:ignore
    else:
        raise ValueError()


def _load_rate_limiter(config: RateLimitConfig) -> RateLimiter:
    rate_limit_file = config.rate_limit_file
    repository: RateLimitingRepo

    if rate_limit_file is None:
        _LOG.warning("Using in-memory rate limiting repo")
        repository = repo.InMemoryRateLimitingRepo()
    else:
        repository = repo.SqliteRateLimitingRepo.connect(Path(rate_limit_file))

    return RateLimiter(
        policy=policy.DailyLimitRateLimitingPolicy(limit=1),
        repo=repository,
    )


def main():
    _setup_logging()

    config = Config.from_env(load_env(""))
    _setup_sentry(config.sentry_dsn, release=config.app_version)

    horoscope = _load_horoscope(config.horoscope)
    rate_limiter = _load_rate_limiter(config.rate_limit)

    bot = Bot(
        config.telegram,
        horoscope=horoscope,
        rate_limiter=rate_limiter,
    )
    _LOG.info("Launching bot...")
    bot.run()


if __name__ == "__main__":
    main()
