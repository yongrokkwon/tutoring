import sqlite3
from datetime import datetime

from ..crawler.parser import ParsedNotice

# seeds.sql 의 (table, id) 와 동기 필요 — _pre-impl-checklist §1.4
TYPE_NEW = 1
TYPE_MODIFIED = 2
STATUS_SUCCESS = 1
STATUS_FAILED = 2
CHANNEL_DISCORD = 1


def insert_batch(conn: sqlite3.Connection,
                 user_id: int,
                 channel_id: int,
                 new: list[ParsedNotice],
                 modified: list[ParsedNotice],
                 status_id: int,
                 sent_at: datetime) -> None:
    rows = []
    sent_at_text = sent_at.strftime("%Y-%m-%d %H:%M:%S")
    for item in new:
        rows.append((user_id, item.duid, channel_id,
                     TYPE_NEW, status_id, sent_at_text))
    for item in modified:
        rows.append((user_id, item.duid, channel_id,
                     TYPE_MODIFIED, status_id, sent_at_text))
    if not rows:
        return
    conn.executemany(
        """
        INSERT INTO notifications
            (user_id, notice_duid, channel_id, type_id, status_id, sent_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
