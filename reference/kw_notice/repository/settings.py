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
