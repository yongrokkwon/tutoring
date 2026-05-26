# 영역 1 — 공지 수집 기술 명세서

**버전**: v1.0
**작성일**: 2026-05-15
**상위 문서**: `docs/source-spec/functional-spec.md` §영역 1, `docs/source-spec/requirements.md` §3·§4·§6·§7
**범위**: 영역 1 (공지 수집)의 구현 명세 — 모듈 구조·함수 시그니처·데이터 흐름·셀렉터 사양·에러 처리·DB 사용 범위.
**범위 외**: Discord 발송 (영역 2), 설정 UI (영역 4), 조회 UI (영역 3).
**셀렉터 검증 기준**: 2026-05-15 시점 `https://www.kw.ac.kr/ko/life/notice.jsp` 응답. → `reference/` 폴더로 1회 검증 완료.

---

## 1. 모듈 / 파일 구조

```
kw_notice/
├── config.py                       # 상수 (URL, 운영시간, 재시도, USER-Agent, 기본 user_id)
├── db.py                           # SQLite 연결, 트랜잭션 컨텍스트, 스키마/시드 초기화
├── crawler/
│   ├── fetcher.py                  # HTTP 요청 + 재시도
│   ├── parser.py                   # HTML → ParsedNotice DTO 리스트
│   ├── classifier.py               # 신규/수정/무시 분류 + DB 저장
│   ├── time_utils.py               # 운영시간 판정, 주기 모드 → 발동 시각 집합
│   ├── service.py                  # 한 사이클 오케스트레이션 (fetch → parse → classify → 알림 호출)
│   └── scheduler.py                # 상주 루프 + 매분 settings 재조회 + 발동 판정
├── repository/
│   ├── categories.py               # 카테고리 한글명 ↔ ID 매핑 (categories 테이블 기반)
│   ├── notices.py                  # notices INSERT / UPDATE / SELECT by DUID / COUNT
│   ├── attachments.py              # 첨부 placeholder INSERT / DELETE
│   └── settings.py                 # user_settings + user_custom_times 로드, 기본값
└── notifier/
    └── (영역 2가 채움 — 영역 1은 모듈 경로만 참조)
```

**책임 분리 원칙**:
- `fetcher`·`parser` 는 *순수 기능* (입력 → 출력). 스케줄링·DB·알림을 모름.
- `classifier` 는 영역 1 내부 한정으로 DB 변경까지 수행한다 (`conn` 을 받음).
- `service.py` 가 영역 경계. DB 트랜잭션을 열고 영역 2 호출 지점을 명확히 만든다.
- `scheduler.py` 는 시간 외 로직을 가지지 않는다 — 매분 깨워 "지금이 발동 시각인가"만 판단.

---

## 2. 핵심 함수 시그니처 + 책임

### 2.1 `config.py`
모듈 상수만 정의 (함수 없음). 노출값:

| 상수 | 값 | 출처 |
|---|---|---|
| `NOTICE_LIST_URL` | `https://www.kw.ac.kr/ko/life/notice.jsp?srCategoryId=&mode=list&searchKey=1&searchVal=` | requirements §3-1 |
| `NOTICE_BASE_URL` | `https://www.kw.ac.kr` | 상대 URL 변환용 |
| `USER_AGENT` | `kw-notice-crawler/1.0 (...; contact: <email>)` — **ASCII 한정** | requirements §11-2, HTTP 헤더 latin-1 제약 |
| `HTTP_TIMEOUT_SEC` | `10` | functional-spec §영역 1 ②, requirements §11-2 |
| `HTTP_RETRY_COUNT` | `3` | 동일 |
| `HTTP_RETRY_DELAY_SEC` | `2` (고정) | 동일 |
| `OPERATING_HOUR_START` | `10` | requirements §4-1 |
| `OPERATING_HOUR_END` | `17` | 동일 |
| `DEFAULT_USER_ID` | `1` | requirements §2 (MVP 1인) |
| `DB_PATH` | `data/kw_notice.db` | — |

### 2.2 `db.py`

| 시그니처 | 책임 |
|---|---|
| `connect() -> sqlite3.Connection` | `row_factory=Row`, `PRAGMA foreign_keys=ON` 적용한 연결 반환. |
| `transaction() -> ContextManager[Connection]` | `with` 블록 종료 시 commit, 예외 시 rollback, 항상 close. |
| `init_schema() -> None` | `schema.sql` + `seeds.sql` 을 `executescript` 로 실행. 멱등. |

### 2.3 `crawler/fetcher.py`

| 시그니처 | 책임 |
|---|---|
| `fetch_list_html(url: str = NOTICE_LIST_URL) -> str` | 최대 3회 시도, 매 시도 사이 2초 sleep. 매 시도마다 `print` 로그. 3회 실패 시 `FetchError` 발생. 성공 시 UTF-8 텍스트 반환. |
| `class FetchError(Exception)` | 재시도 후에도 실패했음을 알리는 단일 예외 타입. |

**재시도 대상**: 모든 예외 (functional-spec §영역 1 ②). 5xx·타임아웃 한정 백오프는 TODO.

### 2.4 `crawler/parser.py`

```python
@dataclass(frozen=True)
class ParsedNotice:
    duid: int
    title: str
    category_id: int | None    # parser 는 항상 None. classifier 가 채움.
    category_name: str
    author: str            # 부서명
    posted_date: str       # 'YYYY-MM-DD'
    modified_date: str     # 'YYYY-MM-DD' (없으면 posted_date 와 동일)
    is_pinned: bool
    has_attachment: bool
    marked_as_new: bool
    url: str               # 절대 URL
```

| 시그니처 | 책임 |
|---|---|
| `parse(html: str) -> list[ParsedNotice]` | 목록 컨테이너 찾기 → 각 `<li>` 행 파싱 → DUID 중복 시 고정 표시 우선해서 dedupe. **DB 미사용** — `category_id` 는 `None` 으로 두고 classifier 가 채운다. |
| `class ParseError(Exception)` | 컨테이너 자체를 못 찾을 때만 발생 (행별 실패는 로그 후 skip). |

내부 helper (단일 책임):
- `_parse_row(li) -> ParsedNotice | None`
- `_extract_duid(href) -> int | None`
- `_extract_title(anchor, category_tag) -> str` — **anchor 의 `children` 만 순회**. `Comment`·ico-*·`category_tag` skip. (descendants 로 순회하면 주석 텍스트·카테고리 라벨이 title 에 끼어든다. ← 검증 단계에서 실측.)

### 2.5 `crawler/classifier.py`

```python
@dataclass(frozen=True)
class ClassifiedCycle:
    new: list[ParsedNotice]
    modified: list[ParsedNotice]
    ignored: int
    first_run: bool
```

| 시그니처 | 책임 |
|---|---|
| `process(conn, parsed, today: date) -> ClassifiedCycle` | `notices.count(conn) == 0` 이면 첫 실행 분기, 아니면 일반 분기. **`category_name → category_id` 매핑** (`categories` 테이블 조회) 도 여기서 수행 — 매핑 불가 행은 skip + 로그. DB 저장까지 한 함수 안에서 끝낸다. |

**첫 실행 분기**:
1. 파싱된 전 건 INSERT.
2. `has_attachment=True` 인 건은 attachments placeholder 1행 INSERT.
3. `posted_date == today` 인 건만 `new[]` 로 분류, 나머지는 `ignored` 카운트.
4. `modified[]` 은 비움.

**일반 분기** (각 파싱 건별):
- DUID 미존재 → INSERT + placeholder (필요 시) + `new[]` 추가.
- DUID 존재 && `modified_date` 다름 → UPDATE + 첨부 재동기화 + `modified[]` 추가.
  - 첨부 재동기화: `has_attachment=True` 면 placeholder ensure, False 면 `attachments` 행 전체 삭제.
- DUID 존재 && `modified_date` 동일 → DB 미변경, `ignored++`.

### 2.6 `crawler/time_utils.py`

| 시그니처 | 책임 |
|---|---|
| `is_operating_now(now: datetime) -> bool` | 월~금 AND `10:00 <= now <= 17:00`. 17시 분 단위는 17:00 정각만 포함, 17:01 이후 제외. |
| `trigger_times(settings: UserSettings) -> set[str]` | 주기 모드 → `'HH:MM'` 문자열 집합. high=29개, medium=8개, low=1개, custom=`user_custom_times` 그대로. |

### 2.7 `crawler/service.py`

| 시그니처 | 책임 |
|---|---|
| `run_cycle(now: datetime, *, enforce_operating: bool = True) -> None` | 1사이클 전체. 운영시간 가드(옵션) → fetch → DB 트랜잭션 안에서 parse + classify → 트랜잭션 닫고 알림 호출 여부 판단 후 영역 2 호출. |

**알림 호출 조건** (functional-spec §영역 1 ⑥ 그대로):
- `settings.is_active == False` → 호출 안 함.
- `new[]` 와 `modified[]` 둘 다 비어 있음 → 호출 안 함.
- 그 외 → `notifier.send(new, modified)` 호출.

영역 2 가 아직 stub 인 상태에서도 이 함수의 외형은 변하지 않는다.

### 2.8 `crawler/scheduler.py`

| 시그니처 | 책임 |
|---|---|
| `run_forever() -> None` | 무한 루프. 매분 깨어남 → settings 재조회 → 운영시간 체크 → 발동 시각이면 `service.run_cycle(now)` 호출 → 다음 분 경계까지 sleep. 같은 (date, HH:MM) 슬롯은 하루에 1회만 발동. |

내부 상태:
- `fired: set[tuple[date_iso, hhmm]]` — 발동된 슬롯 추적. 날짜 바뀌면 prune.
- `last_settings: UserSettings` — DB 조회 실패 시 fallback.

---

## 3. 데이터 흐름 (영역 내부)

```
[scheduler.run_forever]  ──매분──┐
                                  │ 1. settings 재조회 (실패 시 last_settings)
                                  │ 2. is_operating_now? 아니면 sleep
                                  │ 3. now.HH:MM ∈ trigger_times(settings)?
                                  │ 4. 이 슬롯 이미 발동? 그럼 skip
                                  ▼
                          service.run_cycle(now)
                                  │
                                  ▼
                    ┌─ fetcher.fetch_list_html() ──→ FetchError? 사이클 종료
                    │           │
                    │           ▼ html: str
                    │  ┌─ db.transaction() open ──┐
                    │  │                          │
                    │  │  parser.parse(html)      │  ParseError? 트랜잭션 종료
                    │  │           │              │
                    │  │           ▼              │
                    │  │  classifier.process(     │  INSERT/UPDATE 발생
                    │  │     conn, parsed, today) │
                    │  │           │              │
                    │  │           ▼              │
                    │  │   ClassifiedCycle        │
                    │  │  settings = load(conn)   │
                    │  └─ db.transaction() close ─┘
                    │           │
                    │           ▼
                    └─ is_active && (new ∪ modified) ≠ ∅
                           │
                           └─→ notifier.send(new, modified)   (영역 2)
```

**트랜잭션 경계**: 파싱·분류·저장은 **하나의 트랜잭션**. 알림 호출은 트랜잭션 *밖* — 알림 실패가 DB 롤백을 유발하면 안 됨 (functional-spec §영역 2 의 status 기록은 영역 2 의 자체 트랜잭션이 담당).

---

## 4. 셀렉터·필드 매핑 (실제 페이지 검증)

검증 페이지: `https://www.kw.ac.kr/ko/life/notice.jsp?srCategoryId=&mode=list&searchKey=1&searchVal=` (2026-05-15).

### 4.1 컨테이너 / 행

```html
<div class="board-list-box">
  <ul>
    <li class="top-notice ">...</li>   ← 고정 공지 (페이지 상단)
    ...
    <li class="">...</li>              ← 일반 공지
    ...
  </ul>
</div>
```

| 의미 | CSS 셀렉터 | 비고 |
|---|---|---|
| 컨테이너 `<ul>` | `div.board-list-box ul` | 못 찾으면 fallback 으로 첫 `<ul>` 시도 후 그래도 없으면 `ParseError` |
| 각 행 | `ul > li` (직접 자식만) | recursive=False |
| 고정 공지 판정 | `li.class` 에 `top-notice` 포함 | requirements §5 `is_pinned` |

### 4.2 행 내부 필드

행 1건 HTML 예 (고정 + 첨부 + 신규):
```html
<li class="top-notice ">
  <span class="ico-notice">Notice</span>          ← 일반 공지에는 <span class="no">10163</span>
  <div class="board-text">
    <a href="/ko/life/notice.jsp?BoardMode=view&DUID=52528&tpage=1&searchKey=1&searchVal=&srCategoryId=">
      <strong class="category">[국제학생]</strong>
      2026 GLOBAL TALENT FAIR 채용박람회 안내
      <!-- 비밀글일 경우 ... -->
      <!-- 뉴아이콘 -->
      <span class="ico-new">신규게시글</span>
      <!-- 첨부 -->
      <span class="ico-file ">Attachment</span>
    </a>
    <p class="info">
      조회수 60 | 작성일 2026-05-15 | 수정일 2026-05-15 | 국제교류팀
    </p>
  </div>
</li>
```

| 필드 | 추출 위치 | 추출 규칙 |
|---|---|---|
| `duid` | `li a[href*="DUID="]` 의 href | `urllib.parse.parse_qs` 로 `DUID` 파라미터를 정수화. 없으면 행 skip. |
| `category_name` | `li a > strong.category` 텍스트 | `[국제학생]` → 대괄호 제거 후 `국제학생`. |
| `category_id` | parser 는 `None`. classifier 가 DB `categories.name → id` 매핑 (`repository/categories.py`) | 매핑 불가 시 classifier 단계에서 행 skip + 로그. |
| `title` | `li a` 의 **직접 children** 텍스트 노드 | `Comment`·`strong.category`·`span.ico-new`·`span.ico-file` 제외. 공백 정리 후 join. ⚠ `descendants` 로 훑으면 안 됨 (주석 텍스트·카테고리 라벨 중복). |
| `is_pinned` | `li.class` 에 `top-notice` 존재 여부 | 일반 공지는 `<span class="no">번호</span>` 가 보이지만 판정에는 미사용. ※ 광운대 페이지는 시기에 따라 50~70건의 `top-notice` 행을 페이지 상단에 표시함 (2026-05-15 65건, 2026-05-16 53건 확인). `is_pinned=true` 가 다수가 되는 것은 페이지 자체 특성으로 정상. |
| `has_attachment` | `li a span.ico-file` 존재 여부 | 1단계는 placeholder 1행만 생성. |
| `marked_as_new` | `li a span.ico-new` 존재 여부 | 알림/조회 미사용 (저장만). |
| `posted_date` | `li p.info` 전체 텍스트에서 `r'작성일\s*(\d{4}-\d{2}-\d{2})'` | 없으면 행 skip. |
| `modified_date` | 동일 텍스트에서 `r'수정일\s*(\d{4}-\d{2}-\d{2})'` | 없으면 `posted_date` 로 대체. |
| `author` | `li p.info` 텍스트의 마지막 `|` 이후 토큰 | 빈 값이거나 날짜 형식이면 행 skip. |
| `url` | `urljoin(NOTICE_BASE_URL, href)` | 절대 URL. |

**중복 DUID 처리**: 같은 DUID 가 고정·일반 양쪽에 나타나면 `is_pinned=True` 인 쪽을 유지. dedupe 는 파서 안에서 끝낸다 (classifier 는 dedup 가정).

---

## 5. 에러 처리 위치와 정책

| 발생 지점 | 정책 |
|---|---|
| HTTP 요청 실패 (모든 예외) | `fetcher` 가 3회 재시도. 매 시도 `print` 로그. 3회 실패 시 `FetchError` 발생 → `service.run_cycle` 에서 catch → 사이클 조용히 종료. |
| 응답은 왔으나 컨테이너 셀렉터 못 찾음 | `parser.parse` 가 `ParseError` 발생. `service.run_cycle` 에서 catch → 로그 + 사이클 종료. |
| 행별 파싱 실패 (DUID 누락, 카테고리 매핑 실패, 작성일 누락, 부서 누락) | 해당 행만 skip + `print` 로그. 다른 행은 계속 진행. (functional-spec §영역 1 예외 정책: 1단계는 try/except + 로그.) |
| DB 쓰기 실패 | `db.transaction()` 가 rollback. 예외는 `service.run_cycle` 까지 올라가 catch + 로그. 다음 사이클로 진행. |
| `settings` 조회 실패 (스케줄러) | `last_settings` 캐시 사용. 첫 조회부터 실패하면 `repository.settings.default()` 적용 (medium / is_active=True / custom_times=()). |
| 사이클 자체 예외 (스케줄러 수준) | `scheduler.run_forever` 의 루프 안에서 try/except. 로그 후 다음 분으로 계속. 프로세스는 죽지 않음. |
| 미지의 예외 | 1단계 명세 범위 외. try/except + 로그만. |

**로그 매체**: 모두 `print` (requirements §11-3).

**데이터 품질 이슈 통과 정책**: 원본 페이지의 제목에 비대칭 따옴표·괄호 등 데이터 품질 이슈가 있어도 **가공 없이 그대로 저장·표시** (광운대 원본 보존 원칙). 예: `교류사업」` 처럼 닫는 부호만 있는 경우 통과. parser 가 정상화하지 않는다 — 원본과의 일관성·검증 가능성이 표시 미관보다 우선.

---

## 6. 영역 1이 다루는 DB 스키마 (발췌)

### 6.1 읽기

```sql
-- 주기 모드, is_active 결정
SELECT frequency_mode, is_active
  FROM user_settings
 WHERE user_id = :uid;

-- custom 모드일 때 발동 시각
SELECT time_hhmm
  FROM user_custom_times
 WHERE user_id = :uid
 ORDER BY time_hhmm;

-- 카테고리 한글명 → ID 역매핑 (source of truth = categories 테이블)
SELECT id, name FROM categories;

-- 첫 실행 판정
SELECT COUNT(*) FROM notices;

-- 신규/수정 판별
SELECT modified_date FROM notices WHERE duid = :duid;
```

### 6.2 쓰기

```sql
-- 신규
INSERT INTO notices (duid, title, category_id, author,
                     posted_date, modified_date,
                     is_pinned, marked_as_new, url)
VALUES (...);

-- 수정
UPDATE notices
   SET title=:title, category_id=:cat, author=:author,
       posted_date=:posted, modified_date=:modified,
       is_pinned=:pinned, marked_as_new=:new,
       url=:url,
       updated_at = datetime('now')
 WHERE duid = :duid;

-- 첨부 placeholder
INSERT INTO attachments (notice_duid, filename, url)
VALUES (:duid, NULL, NULL);

-- 첨부 재동기화 (수정 공지에서 첨부 사라짐)
DELETE FROM attachments WHERE notice_duid = :duid;
```

### 6.3 영역 1이 *건드리지 않는* 테이블

`notifications` (영역 2), `users.discord_webhook_url`·`users.email`·`users.name` 등 사용자 채널 정보 (영역 2·4), `notification_*` 매핑 테이블 (영역 2).

`user_settings`·`user_custom_times` 는 **읽기 전용** — 쓰기는 영역 4 의 책임.

---

## 7. 검증 체크리스트 (구현 후 확인할 것)

- [ ] `python main.py init` 실행 → `data/kw_notice.db` 생성 + 시드 11+4+2+2+2 카테고리/모드/채널/타입/상태 + messages 16건 + user(id=1) + user_settings(2, 1) 존재.
- [ ] 빈 DB 에서 `crawl-once` 1회 실행 → `notices` 행 수 ≈ 페이지 1페이지 항목 수, `attachments` 행 수 = 첨부 마크 있는 행 수, 알림 호출은 `posted_date == today` 인 건만.
- [ ] 비어있지 않은 DB 에서 동일 페이지 재실행 → `new=0, modified=0, ignored=N`.
- [ ] DB 의 임의 행 `modified_date` 를 과거로 변경 후 재실행 → `modified=1`.
- [ ] `user_settings.is_active=0` 설정 후 재실행 → 사이클은 돌지만 알림 호출 없음.
- [ ] 발동 시각 집합: high=29, medium=8, low=1. custom 은 등록 시각 그대로.
- [ ] 평일 09:59 / 17:01 / 토요일 → `is_operating_now` False.
- [ ] User-Agent 가 ASCII (latin-1 인코딩 가능).

---

## 8. 미해결 사항 / TODO (1단계 범위 외)

functional-spec / requirements 의 TODO 와 동일. 본 명세서는 그것들을 *구현 위치만* 미리 표시:

- 재시도 대상을 5xx·타임아웃 한정으로 축소 + 지수 백오프 → `fetcher.py`.
- 크롤링 연속 N회 실패 시 운영자 Discord 알림 → `service.py` 가 영역 2 의 운영 알림 채널 호출.
- 첫 실행 정책에 `modified_date == today` 추가 → `classifier._first_run`.

---

## 9. 영역 1 → 영역 2 인터페이스 (영역 2 명세서가 이어받음)

```python
# notifier 모듈이 이 시그니처를 만족해야 한다 (영역 2 명세서에서 확정).
def send(new: list[ParsedNotice],
         modified: list[ParsedNotice]) -> None: ...
```

- 호출 측 (영역 1) 의 보장:
  - 두 리스트가 모두 비어 있는 채로는 호출하지 않는다.
  - `is_active=False` 면 호출하지 않는다.
  - DB 트랜잭션은 *닫혀 있다*. 영역 2 는 자체 트랜잭션을 연다.
- 호출 측이 *보장하지 않는* 것:
  - 호출 성공/실패 결과를 영역 1 에 돌려주지 않는다. 영역 2 가 `notifications` 에 직접 기록.

---

## 10. ERD / DB 스키마 동기화 액션 (본 구현 시작 전)

본 명세서의 결정 [1]·[2] 는 현재 `db-schema.txt` (DBDiagram DSL) 와 어긋난다.
본 구현 착수 전 `db-schema.txt` 와 함께 갱신될 `schema.sql` / `seeds.sql` 에
다음을 반드시 반영한다.

### 10.1 `notices` 테이블
- 컬럼 추가: `url TEXT NOT NULL` — 원문 URL. `ParsedNotice.url` 의 저장처.
- INSERT / UPDATE 모두 `url` 포함 (§6.2 참조).

### 10.2 `categories` 테이블 — source of truth 승격
- 컬럼 추가: `name TEXT NOT NULL UNIQUE`.
- 시드 변경: `(id)` 11행 → `(id, name)` 11행
  (0='일반', 1='학사', 2='학생', 3='봉사', 4='등록/장학', 5='입학',
   6='시설', 7='병무', 8='외부', 9='국제교류', 10='국제학생').
- `messages.ui.label.category.N` 는 **UI 라벨 전용**으로 역할 한정.
  카테고리 매핑·SELECT 는 모두 `categories` 테이블만 사용.

### 10.3 본 명세서·향후 영역 명세서가 전제하는 것
- `repository/categories.py` 의 캐시 로드 SQL: `SELECT id, name FROM categories`.
- 영역 3 (조회) 의 카테고리 표시도 `categories.name` 을 직접 JOIN
  (영역 3 명세 단계에서 동일 전제 유지).
