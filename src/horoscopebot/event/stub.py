import logging

from horoscopebot.event.publisher import Event, EventPublisher

_LOG = logging.getLogger(__name__)


class StubEventPublisher(EventPublisher):
    def publish(self, event: Event):
        _LOG.debug("Not sending event %s because I'm just a stub", event)
