import sqlite3
from dataclasses import dataclass
from datetime import date

from ..repository import attachments, categories, notices
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
    # category_name → category_id 매핑은 여기서. 매핑 불가 행은 skip + 로그.
    mapped: list[ParsedNotice] = []
    skipped = 0
    for item in parsed:
        cat_id = categories.name_to_id(conn, item.category_name)
        if cat_id is None:
            print(f"[classifier] unknown category {item.category_name!r} (DUID={item.duid})")
            skipped += 1
            continue
        mapped.append(_with_category_id(item, cat_id))

    first_run = notices.count(conn) == 0
    if first_run:
        cycle = _first_run(conn, mapped, today)
    else:
        cycle = _regular(conn, mapped)

    if skipped:
        cycle = ClassifiedCycle(
            new=cycle.new,
            modified=cycle.modified,
            ignored=cycle.ignored + skipped,
            first_run=cycle.first_run,
        )
    return cycle


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


def _with_category_id(item: ParsedNotice, cat_id: int) -> ParsedNotice:
    return ParsedNotice(
        duid=item.duid,
        title=item.title,
        category_id=cat_id,
        category_name=item.category_name,
        author=item.author,
        posted_date=item.posted_date,
        modified_date=item.modified_date,
        is_pinned=item.is_pinned,
        has_attachment=item.has_attachment,
        marked_as_new=item.marked_as_new,
        url=item.url,
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
        "url": item.url,
    }
