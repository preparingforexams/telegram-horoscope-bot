import abc
import dataclasses
import json


@dataclasses.dataclass
class Event(abc.ABC):
    chat_id: int

    def serialize(self) -> bytes:
        return json.dumps(dataclasses.asdict(self)).encode("utf-8")


class EventPublishingException(Exception):
    pass


class EventPublisher(abc.ABC):
    @abc.abstractmethod
    def publish(self, event: Event):
        pass
