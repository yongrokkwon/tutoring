import re
import sqlite3
from dataclasses import dataclass
from typing import Iterator, Optional
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from .. import config
from ..repository import categories

_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_POSTED_RE = re.compile(r"작성일\s*(\d{4}-\d{2}-\d{2})")
_MODIFIED_RE = re.compile(r"수정일\s*(\d{4}-\d{2}-\d{2})")
_BRACKET_RE = re.compile(r"\[([^\]]+)\]")


@dataclass(frozen=True)
class ParsedNotice:
    duid: int
    title: str
    category_id: int
    category_name: str
    author: str
    posted_date: str
    modified_date: str
    is_pinned: bool
    has_attachment: bool
    marked_as_new: bool
    url: str


class ParseError(Exception):
    pass


def parse(html: str, conn: sqlite3.Connection) -> list[ParsedNotice]:
    soup = BeautifulSoup(html, "html.parser")
    list_box = soup.select_one("div.board-list-box ul") or soup.select_one("ul")
    if list_box is None:
        raise ParseError("게시판 목록 컨테이너를 찾을 수 없음")

    seen: dict[int, ParsedNotice] = {}
    for li in list_box.find_all("li", recursive=False):
        row = _parse_row(li, conn)
        if row is None:
            continue
        # 같은 DUID 가 고정/일반 양쪽에 노출될 수 있다 — 고정 표시를 우선해 유지.
        existing = seen.get(row.duid)
        if existing is None or (row.is_pinned and not existing.is_pinned):
            seen[row.duid] = row
    return list(seen.values())


def _parse_row(li: Tag, conn: sqlite3.Connection) -> Optional[ParsedNotice]:
    anchor = li.find("a", href=lambda h: h and "DUID=" in h)
    if anchor is None:
        return None

    duid = _extract_duid(anchor["href"])
    if duid is None:
        return None

    info = li.find("p", class_="info")
    if info is None:
        return None
    info_text = info.get_text(" ", strip=True)
    posted = _match_one(_POSTED_RE, info_text)
    modified = _match_one(_MODIFIED_RE, info_text) or posted
    if not posted:
        return None
    author = info_text.rsplit("|", 1)[-1].strip()
    if not author or _DATE_RE.match(author):
        return None

    category_tag = anchor.find("strong", class_="category")
    if category_tag is None:
        return None
    category_name = _strip_brackets(category_tag.get_text(strip=True))
    category_id = categories.name_to_id(conn, category_name)
    if category_id is None:
        # 모르는 카테고리 — 1단계 명세 범위 외, 로그 후 스킵.
        print(f"[parser] unknown category {category_name!r} (DUID={duid})")
        return None

    title = _extract_title(anchor, category_tag)
    if not title:
        return None

    is_pinned = "top-notice" in (li.get("class") or [])
    has_attachment = anchor.find("span", class_="ico-file") is not None
    marked_as_new = anchor.find("span", class_="ico-new") is not None

    return ParsedNotice(
        duid=duid,
        title=title,
        category_id=category_id,
        category_name=category_name,
        author=author,
        posted_date=posted,
        modified_date=modified,
        is_pinned=is_pinned,
        has_attachment=has_attachment,
        marked_as_new=marked_as_new,
        url=urljoin(config.NOTICE_BASE_URL, anchor["href"]),
    )


def _extract_duid(href: str) -> Optional[int]:
    qs = parse_qs(urlparse(href).query)
    raw = qs.get("DUID", [None])[0]
    try:
        return int(raw) if raw is not None else None
    except ValueError:
        return None


def _extract_title(anchor: Tag, category_tag: Tag) -> str:
    parts: list[str] = []
    for child in anchor.children:
        if isinstance(child, Comment):
            continue
        if isinstance(child, NavigableString):
            text = str(child).strip()
            if text:
                parts.append(text)
            continue
        if child is category_tag:
            continue
        if child.name == "span" and any(
            cls in (child.get("class") or [])
            for cls in ("ico-new", "ico-file")
        ):
            continue
        text = child.get_text(" ", strip=True)
        if text:
            parts.append(text)
    return " ".join(parts).strip()


def _match_one(pattern: re.Pattern[str], text: str) -> Optional[str]:
    m = pattern.search(text)
    return m.group(1) if m else None


def _strip_brackets(text: str) -> str:
    m = _BRACKET_RE.search(text)
    return m.group(1) if m else text
