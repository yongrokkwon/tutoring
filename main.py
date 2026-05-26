"""광운대 공지사항 크롤러 — 1단계 MVP 진입점.

사용:
  python main.py init        # DB 초기화 (스키마 + 시드)
  python main.py crawl-once  # 사이클 1 회만 (운영시간 무시 — 디버그 전용)
  python main.py run         # 상주 + Flask + 스케줄러 (단일 프로세스)

run 동작 (_pre-impl-checklist §5.3): 스케줄러를 daemon thread 로 띄우고
메인 스레드는 Flask app.run() 으로 서빙. SQLite 기본 격리로 충분
(connection 은 매 호출마다 새로 열어 스레드 안전).
"""
import sys
import threading
from datetime import datetime

from kw_notice import db
from kw_notice.crawler import scheduler, service
from kw_notice.web import create_app


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    cmd = args[0]
    if cmd == "init":
        db.init_schema()
        print("DB 초기화 완료")
        return 0
    if cmd == "crawl-once":
        db.init_schema()
        service.run_cycle(datetime.now(), enforce_operating=False)
        return 0
    if cmd == "run":
        db.init_schema()
        threading.Thread(
            target=scheduler.run_forever, daemon=True, name="scheduler"
        ).start()
        app = create_app()
        app.run(host="127.0.0.1", port=5002, debug=False)
        return 0
    print(f"알 수 없는 명령: {cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
