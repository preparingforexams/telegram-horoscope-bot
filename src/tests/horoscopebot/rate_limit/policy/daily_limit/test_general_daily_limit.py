import pytest

from horoscopebot.rate_limit.policy.daily_limit import DailyLimitRateLimitingPolicy


@pytest.mark.parametrize(
    "limit",
    [
        0,
        -1,
    ],
)
def test_invalid_limit(limit):
    with pytest.raises(ValueError):
        DailyLimitRateLimitingPolicy(limit=limit)


@pytest.mark.parametrize(
    "limit",
    [
        1,
        2,
        10,
    ],
)
def test_requested_history_matches_limit(limit):
    policy = DailyLimitRateLimitingPolicy(limit=limit)
    assert policy.requested_history == limit
