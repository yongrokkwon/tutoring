import sqlite3
from typing import Optional


def get_discord_webhook(conn: sqlite3.Connection,
                        user_id: int) -> Optional[str]:
    row = conn.execute(
        "SELECT discord_webhook_url FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        return None
    url = row["discord_webhook_url"]
    if url is None or url == "":
        return None
    return url
