import dataclasses
from datetime import timedelta

import pendulum
import pytest
from rate_limit import Usage

from horoscopebot.dementia_responder import DementiaResponder


@pytest.fixture()
def responder() -> DementiaResponder:
    return DementiaResponder()


@pytest.fixture()
def usage() -> Usage:
    return Usage(
        context_id="context",
        user_id="user",
        time=pendulum.now(),
        reference_id="2",
        response_id="5",
    )


def test_ten_minute_rule(responder: DementiaResponder, usage):
    now = pendulum.now()
    usage = dataclasses.replace(usage, time=usage.time - timedelta(minutes=5))
    response = responder.create_response(
        10,
        now,
        usage,
    )
    assert "nicht mal zehn Minuten" in response.text
    assert response.reply_message_id is None


def test_ten_minute_rule_too_long(responder: DementiaResponder, usage):
    now = pendulum.now()
    usage = dataclasses.replace(usage, time=usage.time - timedelta(minutes=11))
    response = responder.create_response(
        10,
        now,
        usage,
    )
    assert "nicht mal zehn Minuten" not in response.text
