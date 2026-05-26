import sqlite3
from typing import Optional

# 광운대 목록 HTML 의 <strong class='category'> 텍스트는 한글이므로
# DB seed (messages.ui.label.category.N) 를 역인덱싱해 ID 로 환원한다.
# 표시명 변경 시 SQL 만 고치면 코드가 따라온다.
_CACHE: dict[str, int] = {}


def name_to_id(conn: sqlite3.Connection, name: str) -> Optional[int]:
    if not _CACHE:
        rows = conn.execute(
            "SELECT key, template FROM messages "
            "WHERE key LIKE 'ui.label.category.%'"
        ).fetchall()
        for row in rows:
            cat_id = int(row["key"].rsplit(".", 1)[-1])
            _CACHE[row["template"]] = cat_id
    return _CACHE.get(name)


def reset_cache() -> None:
    _CACHE.clear()
