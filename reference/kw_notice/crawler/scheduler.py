import time
from datetime import datetime, timedelta

from .. import db
from ..repository import settings as settings_repo
from ..repository.settings import UserSettings
from . import service, time_utils


def run_forever() -> None:
    print("[scheduler] 시작. 매 분 user_settings 재조회 + 발동 시각 판단.")
    fired: set[tuple[str, str]] = set()  # (YYYY-MM-DD, HH:MM)
    last_settings: UserSettings = settings_repo.default()

    while True:
        now = datetime.now()

        try:
            with db.transaction() as conn:
                last_settings = settings_repo.load(conn)
        except Exception as exc:
            print(f"[scheduler] 설정 조회 실패, 직전 캐시 사용: {exc!r}")

        _prune_stale(fired, now)

        if time_utils.is_operating_now(now):
            triggers = time_utils.trigger_times(last_settings)
            current_slot = now.strftime("%H:%M")
            date_iso = now.strftime("%Y-%m-%d")
            key = (date_iso, current_slot)
            if current_slot in triggers and key not in fired:
                print(f"[scheduler] {date_iso} {current_slot} 발동")
                fired.add(key)
                try:
                    service.run_cycle(now)
                except Exception as exc:
                    print(f"[scheduler] 사이클 예외, 다음 사이클 진행: {exc!r}")

        time.sleep(_sleep_to_next_minute())


def _sleep_to_next_minute() -> float:
    now = datetime.now()
    nxt = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    return max(1.0, (nxt - now).total_seconds())


def _prune_stale(fired: set[tuple[str, str]], now: datetime) -> None:
    today = now.strftime("%Y-%m-%d")
    stale = {entry for entry in fired if entry[0] != today}
    fired.difference_update(stale)
