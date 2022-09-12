from __future__ import annotations

import logging
from concurrent import futures

from google.cloud.pubsub_v1 import PublisherClient

from horoscopebot.config import EventPublisherConfig
from horoscopebot.event.publisher import Event, EventPublisher, EventPublishingException

_LOG = logging.getLogger(__name__)


class PubSubEventPublisher(EventPublisher):
    def __init__(self, config: EventPublisherConfig):
        if not config.project_id or not config.topic_name:
            raise ValueError("Missing project_id or topic_name")

        self.client = PublisherClient()
        self.topic = f"projects/{config.project_id}/topics/{config.topic_name}"

    def publish(self, event: Event):
        _LOG.debug("Publishing event %s", event)
        future = self.client.publish(
            topic=self.topic,
            data=event.serialize(),
        )
        try:
            future.result(timeout=60)
        except futures.TimeoutError as e:
            raise EventPublishingException from e
        except Exception as e:
            raise EventPublishingException from e
