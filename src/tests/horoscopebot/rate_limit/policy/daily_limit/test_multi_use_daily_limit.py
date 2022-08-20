import pytest

from horoscopebot.rate_limit import RateLimitingPolicy
from horoscopebot.rate_limit.policy.daily_limit import DailyLimitRateLimitingPolicy


@pytest.fixture()
def policy() -> RateLimitingPolicy:
    return DailyLimitRateLimitingPolicy(limit=3)


@pytest.mark.parametrize(
    "time_fixture_names",
    [
        [],
        ["earlier_today", "yesterday"],
        ["earlier_today", "earlier_today"],
        ["later_today", "earlier_today", "yesterday"],
        ["tomorrow", "earlier_today", "earlier_today"],
    ],
)
def test_get_offending_usages_pass(
    policy,
    now,
    create_usage,
    time_fixture_names,
    request,
):
    times = [request.getfixturevalue(name) for name in time_fixture_names]
    usages = [create_usage(time) for time in times]
    offending_usage = policy.get_offending_usage(now, usages)
    assert offending_usage is None


def test_get_offending_usages_fail(
    policy,
    now,
    create_usage,
    earlier_today,
    later_today,
):
    later_usage = create_usage(later_today)
    earlier_usage = create_usage(earlier_today)
    earlier_usage2 = create_usage(earlier_today)
    offending_usage = policy.get_offending_usage(
        now,
        [later_usage, earlier_usage2, earlier_usage],
    )
    assert offending_usage == earlier_usage
