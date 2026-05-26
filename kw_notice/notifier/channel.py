from datetime import datetime
from typing import ClassVar, Protocol, runtime_checkable

from ..crawler.parser import ParsedNotice


@runtime_checkable
class NotificationChannel(Protocol):
    # seeds.sql 의 notification_channels.(id, name) 와 동기 필요
    channel_id: ClassVar[int]

    def send(self,
             new: list[ParsedNotice],
             modified: list[ParsedNotice],
             sent_at: datetime) -> bool: ...
