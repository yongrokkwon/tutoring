import sqlite3


def has_any(conn: sqlite3.Connection, duid: int) -> bool:
    row = conn.execute(
        "SELECT 1 FROM attachments WHERE notice_duid = ? LIMIT 1", (duid,)
    ).fetchone()
    return row is not None


def insert_placeholder(conn: sqlite3.Connection, duid: int) -> None:
    if has_any(conn, duid):
        return
    conn.execute(
        "INSERT INTO attachments (notice_duid, filename, url) "
        "VALUES (?, NULL, NULL)",
        (duid,),
    )


def delete_all(conn: sqlite3.Connection, duid: int) -> None:
    conn.execute("DELETE FROM attachments WHERE notice_duid = ?", (duid,))
