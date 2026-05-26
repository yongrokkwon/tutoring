"""광운대 공지사항 크롤러 — 1단계 MVP 실행 진입점.

사용:
  python main.py init        # DB 초기화 (스키마 + 시드)
  python main.py crawl-once  # 사이클 1회만 실행 (스케줄 무시, 운영시간 무시)
  python main.py run         # 상주 + 스케줄 (운영시간/주기 모드 준수)
"""
import sys
from datetime import datetime

from kw_notice import db
from kw_notice.crawler import scheduler, service


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
        scheduler.run_forever()
        return 0
    print(f"알 수 없는 명령: {cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
