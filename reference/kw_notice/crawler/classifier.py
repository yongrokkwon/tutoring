import sqlite3
from dataclasses import dataclass
from datetime import date

from ..repository import attachments, notices
from .parser import ParsedNotice


@dataclass(frozen=True)
class ClassifiedCycle:
    new: list[ParsedNotice]
    modified: list[ParsedNotice]
    ignored: int
    first_run: bool


def process(conn: sqlite3.Connection,
            parsed: list[ParsedNotice],
            today: date) -> ClassifiedCycle:
    first_run = notices.count(conn) == 0
    if first_run:
        return _first_run(conn, parsed, today)
    return _regular(conn, parsed)


def _first_run(conn: sqlite3.Connection,
               parsed: list[ParsedNotice],
               today: date) -> ClassifiedCycle:
    today_iso = today.isoformat()
    new_for_alert: list[ParsedNotice] = []

    for item in parsed:
        notices.insert(conn, _to_row(item))
        if item.has_attachment:
            attachments.insert_placeholder(conn, item.duid)
        if item.posted_date == today_iso:
            new_for_alert.append(item)

    return ClassifiedCycle(
        new=new_for_alert,
        modified=[],
        ignored=len(parsed) - len(new_for_alert),
        first_run=True,
    )


def _regular(conn: sqlite3.Connection,
             parsed: list[ParsedNotice]) -> ClassifiedCycle:
    new_list: list[ParsedNotice] = []
    modified_list: list[ParsedNotice] = []
    ignored = 0

    for item in parsed:
        existing = notices.get(conn, item.duid)
        row = _to_row(item)
        if existing is None:
            notices.insert(conn, row)
            if item.has_attachment:
                attachments.insert_placeholder(conn, item.duid)
            new_list.append(item)
        elif existing["modified_date"] != item.modified_date:
            notices.update(conn, row)
            if item.has_attachment:
                attachments.insert_placeholder(conn, item.duid)
            else:
                attachments.delete_all(conn, item.duid)
            modified_list.append(item)
        else:
            ignored += 1

    return ClassifiedCycle(
        new=new_list,
        modified=modified_list,
        ignored=ignored,
        first_run=False,
    )


def _to_row(item: ParsedNotice) -> dict:
    return {
        "duid": item.duid,
        "title": item.title,
        "category_id": item.category_id,
        "author": item.author,
        "posted_date": item.posted_date,
        "modified_date": item.modified_date,
        "is_pinned": 1 if item.is_pinned else 0,
        "marked_as_new": 1 if item.marked_as_new else 0,
    }
