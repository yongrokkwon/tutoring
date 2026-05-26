from datetime import datetime

from .. import config
from ..repository.settings import UserSettings


def is_operating_now(now: datetime) -> bool:
    if now.weekday() >= 5:  # 토(5) / 일(6) 제외
        return False
    hour = now.hour
    if hour < config.OPERATING_HOUR_START:
        return False
    if hour > config.OPERATING_HOUR_END:
        return False
    if hour == config.OPERATING_HOUR_END and now.minute > 0:
        return False
    return True


def trigger_times(settings: UserSettings) -> set[str]:
    mode = settings.frequency_mode
    if mode == 1:  # high — 15 분 간격
        return {
            f"{h:02d}:{m:02d}"
            for h in range(config.OPERATING_HOUR_START,
                           config.OPERATING_HOUR_END + 1)
            for m in (0, 15, 30, 45)
            if not (h == config.OPERATING_HOUR_END and m != 0)
        }
    if mode == 2:  # medium — 매시 정각
        return {
            f"{h:02d}:00"
            for h in range(config.OPERATING_HOUR_START,
                           config.OPERATING_HOUR_END + 1)
        }
    if mode == 3:  # low — 17:00 1 회
        return {f"{config.OPERATING_HOUR_END:02d}:00"}
    if mode == 0:  # custom
        return set(settings.custom_times)
    return set()
