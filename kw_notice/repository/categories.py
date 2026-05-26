import sqlite3
from typing import Optional

# 카테고리 한글명 → ID 역매핑. 카테고리 source of truth = categories.name
# (영역 1 §10.2). messages.ui.label.category.* 는 동일 값의 사본 — 사용 안 함.
_CACHE: dict[str, int] = {}


def name_to_id(conn: sqlite3.Connection, name: str) -> Optional[int]:
    if not _CACHE:
        rows = conn.execute("SELECT id, name FROM categories").fetchall()
        for row in rows:
            _CACHE[row["name"]] = int(row["id"])
    return _CACHE.get(name)


def reset_cache() -> None:
    _CACHE.clear()
