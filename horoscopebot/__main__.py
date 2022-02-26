import logging
from typing import Optional

import sentry_sdk

from horoscopebot.bot import Bot
from horoscopebot.config import load_env, Config

_LOG = logging.getLogger(__package__)


def _setup_logging():
    logging.basicConfig()
    _LOG.level = logging.INFO


def _setup_sentry(dsn: Optional[str]):
    if not dsn:
        _LOG.warning("Sentry DSN not found")
        return

    sentry_sdk.init(
        dsn,

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0
    )


def main():
    _setup_logging()

    config = Config.from_env(load_env(""))
    _setup_sentry(config.sentry_dsn)

    bot = Bot(config.telegram)
    bot.run()


if __name__ == '__main__':
    main()
