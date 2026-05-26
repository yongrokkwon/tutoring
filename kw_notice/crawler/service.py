from datetime import datetime

from .. import db
from ..notifier import service as notifier_service
from ..repository import settings as settings_repo
from . import classifier, fetcher, parser, time_utils


def run_cycle(now: datetime, *, enforce_operating: bool = True) -> None:
    """공지 수집 한 사이클.

    enforce_operating=False 는 수동 디버그 (crawl-once) 전용 우회.
    트랜잭션 경계: 파싱·분류·저장은 단일 트랜잭션. 알림 호출은 그 밖.
    """
    if enforce_operating and not time_utils.is_operating_now(now):
        return

    try:
        html = fetcher.fetch_list_html()
    except fetcher.FetchError as exc:
        print(f"[service] HTTP 사이클 실패, 조용히 종료: {exc}")
        return

    try:
        parsed = parser.parse(html)
    except parser.ParseError as exc:
        print(f"[service] 파싱 실패: {exc!r}")
        return
    except Exception as exc:
        print(f"[service] 예기치 못한 파싱 예외: {exc!r}")
        return

    try:
        with db.transaction() as conn:
            result = classifier.process(conn, parsed, today=now.date())
            current = settings_repo.load(conn)
    except Exception as exc:
        print(f"[service] 분류·저장 실패: {exc!r}")
        return

    print(
        f"[service] 사이클 결과 — new={len(result.new)}, "
        f"modified={len(result.modified)}, ignored={result.ignored}, "
        f"first_run={result.first_run}"
    )

    if not current.is_active:
        return
    if not result.new and not result.modified:
        return
    try:
        notifier_service.send(result.new, result.modified)
    except Exception as exc:
        print(f"[service] 알림 호출 예외, 사이클은 계속: {exc!r}")
