from datetime import datetime

from .. import db
from ..notifier import pipeline
from ..repository import settings as settings_repo
from . import classifier, fetcher, parser, time_utils


def run_cycle(now: datetime, *, enforce_operating: bool = True) -> None:
    """공지 수집 한 사이클. fetch → parse → 분류·저장 → 알림 호출.

    enforce_operating=False 는 수동 디버그(crawl-once) 전용 우회.
    """
    if enforce_operating and not time_utils.is_operating_now(now):
        return

    try:
        html = fetcher.fetch_list_html()
    except fetcher.FetchError as exc:
        print(f"[service] HTTP 사이클 실패, 조용히 종료: {exc}")
        return

    with db.transaction() as conn:
        try:
            parsed = parser.parse(html, conn)
        except Exception as exc:
            print(f"[service] 파싱 실패: {exc!r}")
            return

        current = settings_repo.load(conn)
        result = classifier.process(conn, parsed, today=now.date())

    print(
        f"[service] 사이클 결과 — new={len(result.new)}, "
        f"modified={len(result.modified)}, ignored={result.ignored}, "
        f"first_run={result.first_run}"
    )

    if not current.is_active:
        return
    if not result.new and not result.modified:
        return
    pipeline.send(result.new, result.modified)
