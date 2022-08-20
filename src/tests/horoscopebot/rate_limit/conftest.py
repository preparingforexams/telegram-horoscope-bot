from datetime import timedelta

import pytest
from pendulum import DateTime, tz
from pendulum.tz.timezone import Timezone


@pytest.fixture()
def timezone() -> Timezone:
    return tz.timezone("Europe/Berlin")


@pytest.fixture()
def now(timezone) -> DateTime:
    return DateTime.now(timezone)


@pytest.fixture()
def earlier_today(timezone) -> DateTime:
    return DateTime.now(timezone) - timedelta(minutes=1)


@pytest.fixture()
def later_today(timezone) -> DateTime:
    result = DateTime.now(timezone) + timedelta(minutes=1)
    return result  # type: ignore


@pytest.fixture()
def yesterday(timezone) -> DateTime:
    yesterday_exact: DateTime = DateTime.now(timezone) - timedelta(days=1)
    result = yesterday_exact.replace(
        hour=23,
        minute=59,
        second=33,
        microsecond=0,
    )
    return result  # type: ignore


@pytest.fixture()
def tomorrow(timezone) -> DateTime:
    yesterday_exact = DateTime.now(timezone) + timedelta(days=1)
    result = yesterday_exact.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    return result  # type: ignore
