from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "kw_notice.db"
SCHEMA_PATH = PROJECT_ROOT / "schema.sql"
SEEDS_PATH = PROJECT_ROOT / "seeds.sql"

NOTICE_LIST_URL = (
    "https://www.kw.ac.kr/ko/life/notice.jsp"
    "?srCategoryId=&mode=list&searchKey=1&searchVal="
)
NOTICE_BASE_URL = "https://www.kw.ac.kr"

USER_AGENT = (
    "kw-notice-crawler/1.0 "
    "(educational project; respects >=1s interval; "
    "contact: oyo260325@gmail.com)"
)

HTTP_TIMEOUT_SEC = 10
HTTP_RETRY_COUNT = 3
HTTP_RETRY_DELAY_SEC = 2

OPERATING_HOUR_START = 10
OPERATING_HOUR_END = 17

DEFAULT_USER_ID = 1
