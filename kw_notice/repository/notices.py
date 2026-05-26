import sqlite3
from typing import Optional


def list_recent(conn: sqlite3.Connection,
                limit: int = 100) -> list[sqlite3.Row]:
    """area-3-viewer.md §4 — 정렬: is_pinned DESC, MAX(posted, modified) DESC,
    updated_at DESC, duid DESC. MAX 는 SQLite 의 스칼라 함수 (2 인자).
    """
    return list(conn.execute(
        """
        SELECT
            n.duid,
            n.title,
            n.author,
            n.posted_date,
            n.modified_date,
            n.is_pinned,
            n.url,
            c.name AS category_name,
            EXISTS(SELECT 1 FROM attachments a
                    WHERE a.notice_duid = n.duid) AS has_attachment
        FROM notices n
        JOIN categories c ON c.id = n.category_id
        ORDER BY
            n.is_pinned DESC,
            MAX(n.posted_date, n.modified_date) DESC,
            n.updated_at DESC,
            n.duid DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall())


def count(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS n FROM notices").fetchone()
    return int(row["n"])


def get(conn: sqlite3.Connection, duid: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM notices WHERE duid = ?", (duid,)
    ).fetchone()


def insert(conn: sqlite3.Connection, notice: dict) -> None:
    conn.execute(
        """
        INSERT INTO notices
            (duid, title, category_id, author, posted_date, modified_date,
             is_pinned, marked_as_new, url)
        VALUES
            (:duid, :title, :category_id, :author, :posted_date,
             :modified_date, :is_pinned, :marked_as_new, :url)
        """,
        notice,
    )


def update(conn: sqlite3.Connection, notice: dict) -> None:
    conn.execute(
        """
        UPDATE notices
           SET title         = :title,
               category_id   = :category_id,
               author        = :author,
               posted_date   = :posted_date,
               modified_date = :modified_date,
               is_pinned     = :is_pinned,
               marked_as_new = :marked_as_new,
               url           = :url,
               updated_at    = datetime('now')
         WHERE duid          = :duid
        """,
        notice,
    )
