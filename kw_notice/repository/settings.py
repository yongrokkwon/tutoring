import sqlite3
from dataclasses import dataclass

from .. import config


@dataclass(frozen=True)
class UserSettings:
    user_id: int
    frequency_mode: int
    is_active: bool
    custom_times: tuple[str, ...]


_DEFAULT = UserSettings(
    user_id=config.DEFAULT_USER_ID,
    frequency_mode=2,
    is_active=True,
    custom_times=(),
)


def load(conn: sqlite3.Connection,
         user_id: int = config.DEFAULT_USER_ID) -> UserSettings:
    row = conn.execute(
        "SELECT frequency_mode, is_active FROM user_settings WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        return _DEFAULT
    times = tuple(
        r["time_hhmm"] for r in conn.execute(
            "SELECT time_hhmm FROM user_custom_times "
            "WHERE user_id = ? ORDER BY time_hhmm",
            (user_id,),
        )
    )
    return UserSettings(
        user_id=user_id,
        frequency_mode=int(row["frequency_mode"]),
        is_active=bool(row["is_active"]),
        custom_times=times,
    )


def default() -> UserSettings:
    return _DEFAULT


def update(conn: sqlite3.Connection,
           user_id: int,
           frequency_mode: int,
           is_active: bool) -> None:
    conn.execute(
        """
        UPDATE user_settings
           SET frequency_mode = ?,
               is_active      = ?,
               updated_at     = datetime('now')
         WHERE user_id        = ?
        """,
        (frequency_mode, 1 if is_active else 0, user_id),
    )


def add_custom_times(conn: sqlite3.Connection,
                     user_id: int,
                     times: list[str]) -> None:
    if not times:
        return
    conn.executemany(
        "INSERT INTO user_custom_times (user_id, time_hhmm) VALUES (?, ?)",
        [(user_id, t) for t in times],
    )


def delete_custom_time(conn: sqlite3.Connection,
                       user_id: int,
                       custom_time_id: int) -> None:
    conn.execute(
        "DELETE FROM user_custom_times WHERE id = ? AND user_id = ?",
        (custom_time_id, user_id),
    )


def list_custom_times_with_id(conn: sqlite3.Connection,
                              user_id: int) -> list[tuple[int, str]]:
    return [
        (int(r["id"]), r["time_hhmm"])
        for r in conn.execute(
            "SELECT id, time_hhmm FROM user_custom_times "
            "WHERE user_id = ? ORDER BY time_hhmm",
            (user_id,),
        )
    ]
