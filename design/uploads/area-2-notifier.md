# 영역 2 — 알림 발송 기술 명세서

**버전**: v1.3
**작성일**: 2026-05-20
**상위 문서**: `docs/source-spec/functional-spec.md` §영역 2, `docs/source-spec/requirements.md` §8
**선행 명세**: `area-1-crawler.md` §9 (영역 1 → 영역 2 인터페이스)
**범위**: Discord 웹훅 발송, `notifications` 이력 INSERT, 채널 추상화 (1.5단계 카카오 대비), **Discord content 2000자 한도 대응 메시지 분할 발송**.
**범위 외**: 발송 실패 재시도 사이클 (TODO), 카카오 알림톡 구현체.
**상위 결정 반영**:
- [1] 메시지 템플릿은 **코드 하드코딩** — `notifier/discord.py` 안 상수. `messages` 테이블의 `notification.*` 키는 시드에서 제거 (§7.1).
- [2] Discord 본문은 **content 평문 한 덩이** + 마크다운 `[제목](URL)`. 마크다운은 Discord 어댑터 내부에서만.
- [3] `notifications` INSERT 단위 = (new N + modified M) 묶음 N+M행. 결과 확정 후 INSERT. `sent_at` 동일. **발송 횟수는 1회 또는 분할 N회 — N 회여도 INSERT 는 1 batch.**
- [4] **메시지 분할 정책** (v1.3 신설, 2026-05-20 인시던트 후 보강):
  - 한도: **1,900자** (Discord 2000 - 마진 100).
  - 단위: **라인 단위** 그리디 패킹. 섹션 (new/modified) 별로 별도 청크 시퀀스 생성 (한 청크 내 섹션 혼합 없음).
  - 분할 시 카운트 헤더: 각 섹션 첫 청크 `🆕 새 공지 20건 (1/3)`, 동일 섹션 이어지는 청크 `🆕 새 공지 20건 (이어서 2/3)`. 총 청크 수가 1이면 페이지 표기 생략.
  - footer (`발송 시각: ...`): **마지막 청크에만** 부착.
  - 다중 POST status: **POST 1건이라도 실패하면 해당 사이클 전체 `status_id=2 (FAILED)`** 일괄 기록. 부분 성공 추적은 1단계 범위 외.
  - POST 간격: 분할된 메시지 사이 **0.5초 sleep** (Discord rate limit 5/2s 회피).
  - 단일 라인이 한도 초과 시: **`…` 으로 자르고** 한도 안에 강제로 들어가게. 한 라인이 한 청크를 통째로 차지하는 것은 허용.

---

## 1. 모듈 / 파일 구조

```
kw_notice/
├── notifier/
│   ├── service.py            # entry —영역 1 이 호출. 채널 조회·발송·이력 INSERT 오케스트레이션.
│   ├── channel.py            # NotificationChannel Protocol (1.5단계 카카오 대비)
│   └── discord.py            # DiscordChannel 구현체 + 메시지 템플릿 상수 + HTTP POST 재시도
└── repository/
    ├── users.py              # 사용자 채널 정보 조회 (영역 2 신설)
    └── notifications.py      # 발송 이력 batch INSERT (영역 2 신설)
```

**책임 분리 원칙** (영역 1 과 동일 톤):
- `service.py` 가 영역 경계. 영역 1 의 `send(new, modified)` 시그니처를 만족.
- `discord.py` 는 **HTTP·문자열 조립만** 다룬다. DB·스케줄링 모름.
- `channel.py` 는 Protocol 정의만. 구현체 import 안 함 (순환 의존 방지).
- `repository/notifications.py` 는 batch INSERT 한 함수만 제공.

영역 1 의 `repository/categories.py` 등 다른 영역 모듈은 **읽지도 쓰지도 않는다**.

---

## 2. 핵심 함수 시그니처 + 책임

### 2.1 `notifier/channel.py`

```python
from typing import Protocol, runtime_checkable
from datetime import datetime
from kw_notice.crawler.parser import ParsedNotice

@runtime_checkable
class NotificationChannel(Protocol):
    channel_id: ClassVar[int]  # notification_channels.id (1=discord, 2=kakao)

    def send(self,
             new: list[ParsedNotice],
             modified: list[ParsedNotice],
             sent_at: datetime) -> bool: ...
```

| 약속 | 내용 |
|---|---|
| 입력 | 구조화된 `ParsedNotice` 리스트 두 개 — 어댑터가 자체 합성. 합성된 평문을 호출 측이 미리 만들지 않음 (결정 [2]). |
| 출력 | 발송 성공 여부 (`True/False`). 부분 실패 개념 없음 — 묶음 1회 POST 라 전부 성공 or 전부 실패. |
| `sent_at` | service 가 결정해서 어댑터·repository 양쪽에 *같은 값* 을 넘긴다 (결정 [3] 동일 시각 보장). |

### 2.2 `notifier/discord.py`

| 시그니처 | 책임 |
|---|---|
| `class DiscordChannel:` `__init__(self, webhook_url: str)` | 웹훅 URL 보관. |
| `channel_id: ClassVar[int] = 1` | `notification_channels.id` 매핑. |
| `.send(new, modified, sent_at) -> bool` | `_build_messages` → `_post_all` 순. 예외 발생하지 않음 (성공/실패 모두 bool). |
| `_build_messages(new, modified, sent_at) -> list[str]` | 본문 평문을 **분할 정책 적용해 1개 이상의 메시지로** 조립 (§3). 순수 함수. 한 메시지 ≤ 1,900자 보장. |
| `_post_all(messages: list[str]) -> bool` | 각 메시지를 순차 POST. 메시지 사이 0.5초 sleep. **모든 메시지 성공 시 `True`, 하나라도 실패 시 `False`** (그래도 남은 메시지 전송 시도는 계속 — 부분 도달이 이력보다 낫다는 판단). |
| `_post_one(content: str) -> bool` | 단일 메시지 1건 POST. `requests.post(webhook_url, json={"content": content})`. 재시도 3회, 매 시도 사이 2초 sleep, 매 시도마다 `print` 로그. |

**템플릿 상수** (모듈 최상단, 결정 [1] · [4]):

```python
HEADER_NEW = "🆕 새 공지 {count}건"
HEADER_MODIFIED = "✏️ 수정된 공지 {count}건"
HEADER_PAGE_FIRST = " ({page}/{total})"          # 섹션 첫 청크
HEADER_PAGE_CONT  = " (이어서 {page}/{total})"   # 동일 섹션 이어지는 청크
LINE_NEW = "· [{category}] {title}{attachment} ({date}) — [원문](<{url}>)"
LINE_MODIFIED = "· [수정] [{category}] {title}{attachment} ({date}) — [원문](<{url}>)"
ATTACHMENT_MARK = " 📎"
FOOTER = "발송 시각: {timestamp}"
TIMESTAMP_FMT = "%Y-%m-%d %H:%M"
SECTION_SEP = "\n\n"             # 섹션 사이 빈 줄 1
SPLIT_THRESHOLD = 1900           # Discord 한도 2000 - 안전 마진 100
SPLIT_POST_DELAY_SEC = 0.5       # rate limit (5요청/2초) 회피
LINE_TRUNCATE_SUFFIX = "…"
LINE_MAX_LEN = 1800              # 단일 라인이 자체로 청크 통째 사용 가능 (header/footer/페이지 표기 ~100자 reserve)
```

**HTTP 설정**: 영역 1 `config.HTTP_TIMEOUT_SEC` / `HTTP_RETRY_COUNT` / `HTTP_RETRY_DELAY_SEC` 그대로 재사용 (동일 정책, requirements §11-2).

### 2.3 `notifier/service.py`

```python
def send(new: list[ParsedNotice],
         modified: list[ParsedNotice],
         user_id: int = config.DEFAULT_USER_ID) -> None: ...
```

| 단계 | 내용 |
|---|---|
| 사전 조건 | 호출 시점에 영역 1 이 보장: 두 리스트가 둘 다 비어 있지 않다 AND `is_active=True`. service 는 재검증하지 않음. |
| 1. 채널 조회 (Tx1, 짧음) | `repository.users.get_discord_webhook(conn, user_id)` 조회 → commit. |
| 2. 시각 고정 | `sent_at = datetime.now()` — 어댑터·이력 양쪽에 같은 값. webhook 유무와 무관하게 잡는다. |
| 3. 발송 (Tx 밖) | webhook 있음 → `DiscordChannel(webhook).send(new, modified, sent_at)` → `bool`. webhook 없음 (NULL/빈) → `print` 로그 + `ok=False`. HTTP 는 어떤 트랜잭션에도 속하지 않음. |
| 4. 이력 INSERT (Tx2, 짧음) | `repository.notifications.insert_batch(conn, user_id, channel_id=1, new, modified, status_id, sent_at)` → commit. status: 성공=1, 실패=2. new 항목 type=1, modified 항목 type=2. **빈 webhook 도 `status_id=2` 로 INSERT** (§5 참조). |
| 트랜잭션 | DB 접근은 **두 개의 짧은 트랜잭션**. HTTP POST 는 그 사이에서 트랜잭션 밖. |

### 2.4 `repository/users.py`

| 시그니처 | 책임 |
|---|---|
| `get_discord_webhook(conn, user_id) -> str \| None` | `SELECT discord_webhook_url FROM users WHERE id=?`. 미존재·NULL·빈 문자열 모두 `None` 반환. |

### 2.5 `repository/notifications.py`

| 시그니처 | 책임 |
|---|---|
| `insert_batch(conn, user_id, channel_id, new, modified, status_id, sent_at) -> None` | `executemany` 로 N+M 행 일괄 INSERT. new → `type_id=1`, modified → `type_id=2`. 모든 행 `sent_at` 동일. |

상수 매핑 (모듈 최상단):
```python
TYPE_NEW = 1
TYPE_MODIFIED = 2
STATUS_SUCCESS = 1
STATUS_FAILED = 2
CHANNEL_DISCORD = 1
```

---

## 3. 메시지 양식 — 정확한 출력 사양

functional-spec §영역 2 의 양식을 **마크다운 링크 형식으로 확정**.

### 3.1 양쪽 섹션 모두 있을 때

```
🆕 새 공지 2건
· [국제학생] 2026 GLOBAL TALENT FAIR 채용박람회 안내 📎 (2026-05-15) — [원문](https://www.kw.ac.kr/ko/life/notice.jsp?BoardMode=view&DUID=52528&...)
· [학사] 2026년도 1학기 국제학생증 ISIC발급 지원행사 안내 📎 (2026-05-15) — [원문](https://...)

✏️ 수정된 공지 1건
· [수정] [일반] [HUSS-디지털경제] 2026 ㅎㄷ:Contents Planning 프로그램 안내 (2026-05-15) — [원문](https://...)

발송 시각: 2026-05-15 14:00
```

> 예시의 modified 라인 `(2026-05-15)` 는 **수정일**이다 (작성일과 같은 날일 수도 있고 더 과거일 수도 있음). new 라인의 `(2026-05-15)` 는 작성일.

### 3.2 규칙 (모두 검증 가능한 형태)

| 항목 | 규칙 |
|---|---|
| 섹션 순서 | 항상 new → modified → footer. |
| 섹션 누락 | `new == []` 면 새 공지 섹션 통째 생략, `modified == []` 면 수정 섹션 통째 생략. 양쪽 다 비어 있는 입력은 영역 1 에서 차단됨 (호출 사전 조건). |
| 라인 prefix | new = `· `, modified = `· [수정] `. |
| 카테고리 | `[{category_name}]`. 대괄호는 어댑터가 부여. `ParsedNotice.category_name` 은 대괄호 없는 한글명. |
| 📎 | `ParsedNotice.has_attachment == True` 일 때만 *제목 바로 뒤에* 공백 1칸과 함께 ` 📎`. |
| new 라인 날짜 | `({posted_date})` — 작성일. |
| modified 라인 날짜 | `({modified_date})` — 수정일. (`ParsedNotice.modified_date`.) ※ Discord 본문 길이 절약을 위해 수정일 한 개만 표시. 영역 3 (웹 목록) 은 `area-3-viewer.md` §6.1 에 따라 작성·수정 양쪽을 일자 컬럼에 표시 — 매체별 차이는 의도된 결정. |
| 링크 | 마크다운 `[원문](<{url}>)` — URL 을 `<>` 로 감싸 Discord 의 페이지 미리보기 카드 자동 생성 **비활성화** (채널 스크롤 절약). `ParsedNotice.url` 그대로. URL escape 안 함 (Discord 가 처리). |
| footer 타임스탬프 | `sent_at.strftime("%Y-%m-%d %H:%M")` — 초 단위 절삭. |
| 섹션 사이 | 빈 줄 1 (`\n\n`). |
| 헤더 카운트 | `len(new)` / `len(modified)` 그대로. 둘 다 비어 있는 경우는 §3.2 누락 규칙으로 처리. |

### 3.3 길이 — 분할 발송 정책 (결정 [4])

Discord webhook `content` 한계는 2,000자. 영역 2 v1.3 부터 **1,900자 한도로 라인 단위 그리디 분할**한다.

**알고리즘**:
1. `new` / `modified` 각각의 라인을 §3.2 규칙으로 포맷 → `new_lines` / `mod_lines`.
2. 각 라인이 `LINE_MAX_LEN(1800)` 초과 시 `LINE_TRUNCATE_SUFFIX` 로 절단 (1단계 한국어 공지 평균 길이로는 사실상 미발생, 안전망).
3. **Fast-path** — v1.2 방식대로 두 섹션을 합친 단일 본문 (헤더·라인·SECTION_SEP·footer 모두 포함) 을 먼저 조립. 길이 ≤ `SPLIT_THRESHOLD` 이면 그대로 `[content]` 1건 반환 후 종료. 이 경로에서는 페이지 표기·이어서 표기 모두 없음. **양쪽 섹션이 함께 들어가는 케이스는 이 경로에서만 발생** (= 분할이 필요해진 시점부터는 섹션 혼합 없음).
4. **분할 경로** (3 의 길이가 한도 초과 시) — 섹션별로 그리디 패킹:
   - 한 청크에 (헤더 + 누적 라인) 길이가 (`SPLIT_THRESHOLD` - 헤더베이스 - `_PACK_RESERVE`) 를 초과하지 않도록 라인 추가.
   - `_PACK_RESERVE = 50` = 페이지 표기 최악치 `" (이어서 99/99)"` (~14자) + 마지막 청크 footer `\n\n발송 시각: YYYY-MM-DD HH:MM` (~24자) + 안전 버퍼.
5. 섹션별 청크들을 이어붙임 — new 청크들 다음에 modified 청크들. **분할 경로에서는 한 청크 안에 두 섹션이 섞이지 않음** (구현 단순화).
6. 페이지 표기 부착 (분할 경로 전용, `total ≥ 2`):
   - 각 섹션의 첫 청크 헤더에 `HEADER_PAGE_FIRST` (`(idx/total)`).
   - 동일 섹션의 이어지는 청크 헤더에 `HEADER_PAGE_CONT` (`(이어서 idx/total)`).
   - 마지막 청크에만 `SECTION_SEP + FOOTER` 부착.
7. 최종 list[str] 반환.

> **Fast-path 의 의미**: 양쪽 섹션이 합해서 1,900자 이내면 v1.2 와 동일한 단일 메시지가 나간다. 1단계 일반 운영시간 사이클은 거의 항상 fast-path. 분할 경로는 운영 첫 사이클·휴일 직후 누적분 같은 예외적 큰 배치에서만 발동.

**예시 (5/20 인시던트 재현 시나리오: new 20 + mod 12)**:

청크 1/3 (new 첫 청크):
```
🆕 새 공지 20건 (1/3)
· [등록/장학] ...
· ...
... (라인 12개)
```
청크 2/3 (new 이어서):
```
🆕 새 공지 20건 (이어서 2/3)
· ... (라인 8개)
```
청크 3/3 (modified, 마지막):
```
✏️ 수정된 공지 12건 (3/3)
· [수정] ...
... (라인 12개)

발송 시각: 2026-05-20 11:00
```

> `(이어서 1/N)` 은 의미가 없으므로 각 섹션의 첫 청크는 무조건 `HEADER_PAGE_FIRST`. modified 섹션이 자체 청크 시퀀스의 시작이므로 청크 3 도 `HEADER_PAGE_FIRST` (이어서 표기 없음).

### 3.4 발송 순서·간격

`_post_all` 은 메시지 list 를 순서대로 POST. 메시지 1 → sleep `SPLIT_POST_DELAY_SEC` → 메시지 2 → sleep → ... → 메시지 N. 단일 메시지 (N=1) 일 때는 sleep 없음.

POST 도중 한 건이 최종 실패해도 **남은 메시지 POST 는 계속**한다 (부분 도달 ≥ 0건 도달). 모든 POST 가 끝난 뒤 한 건이라도 실패가 있으면 `_post_all` 은 `False` 반환.

### 3.5 status 결정

`_post_all` 의 `bool` 결과로 batch INSERT 의 `status_id` 가 결정:
- 모든 메시지 성공 → `STATUS_SUCCESS(1)`
- 1건이라도 실패 → `STATUS_FAILED(2)` (전체 N+M 행 일괄)

부분 성공 추적 (어떤 청크가 도달했는지) 은 1단계 범위 외. `notifications` 스키마에 청크 ID 가 없어 표현 불가. → `_pre-impl-checklist.md` §6 TODO 신설 후보.

---

## 4. 데이터 흐름

```
영역 1.service.run_cycle()
        │  (is_active && new∪modified ≠ ∅)
        ▼
notifier.service.send(new, modified, user_id=1)
        │
        ▼
  ┌─ Tx1 (짧음) ─────────────────────────────────┐
  │  webhook = users.get_discord_webhook(uid)    │
  └─ commit ─────────────────────────────────────┘
        │
        ▼
  sent_at = datetime.now()    # webhook 유무와 무관하게 잡음
        │
        ▼
  ── HTTP POST (트랜잭션 밖) ───────────────────────
  if webhook:
      ok = DiscordChannel(webhook).send(
              new, modified, sent_at)
        ├─ _build_messages(...) → list[str]
        │    ├ 라인 truncate (LINE_MAX_LEN 초과 시 …)
        │    ├ 섹션별 그리디 청크 패킹 (≤ SPLIT_THRESHOLD)
        │    └ 페이지 표기 + 마지막 청크 footer 부착
        └─ _post_all(messages) → bool
             ├ for msg in messages:
             │   ├ _post_one(msg) — 재시도 3회·2초 sleep
             │   └ 메시지 사이 0.5초 sleep
             └ 모두 성공 시 True, 1건이라도 실패 시 False (남은 메시지 POST 는 계속)
  else:
      print("[notifier] webhook 없음 — 시도 생략")
      ok = False
        │
        ▼
  status_id = 1 if ok else 2
        │
        ▼
  ┌─ Tx2 (짧음) ─────────────────────────────────┐
  │  notifications.insert_batch(                 │
  │       uid, channel_id=1,                     │
  │       new, modified,                         │
  │       status_id, sent_at)                    │
  └─ commit ─────────────────────────────────────┘
```

**트랜잭션 경계**: 채널 조회 (Tx1) 와 이력 INSERT (Tx2) 는 **분리된 두 개의 짧은 트랜잭션**. HTTP POST 는 두 트랜잭션 사이에서 어떤 트랜잭션에도 속하지 않은 채 진행된다 — DB 잠금 시간을 최소화.

**트랜잭션 분리의 부작용 (어두운 면)**: HTTP POST 성공 + Tx2 INSERT 실패 케이스에서 Discord 에는 메시지가 도달했으나 `notifications` 에 흔적이 남지 않는다. 1단계는 단일 프로세스·로컬 SQLite 라 발생 가능성 극히 낮음 (FK 위반 같은 *데이터 오류* 가 영역 1 classifier 단계에서 차단된 정상 DUID 라 발생 ≈ 0%). 3단계 멀티프로세스 진입 시 보상 트랜잭션 또는 outbox 패턴 검토 — `_pre-impl-checklist.md` §6 TODO 22.

---

## 5. 에러 처리 위치와 정책

| 발생 지점 | 정책 |
|---|---|
| `discord_webhook_url` 가 NULL/빈 문자열 | service 가 `print` 로그 + HTTP 시도 생략 + `notifications` 에 (new+modified) 행을 `status_id=2(failed)` 로 INSERT. `sent_at` 은 시각 고정 시점의 `datetime.now()`. ※ `status=skipped` 같은 별도 상태 추가는 1.5단계 TODO. |
| HTTP 요청 실패 (모든 예외) | `_post_one` 이 3회 재시도. 매 시도 `print`. 최종 실패 시 `False` 반환. 예외는 service 로 올라가지 않음. |
| Discord 4xx / 5xx | `response.raise_for_status()` 가 예외 → 재시도 대상. 마지막 시도까지 실패 시 해당 메시지 `False`. |
| 메시지 길이 초과 (Discord 400) | **선제적으로 분할** (§3.3). 분할 후에도 한도 초과 = 단일 라인이 1800 초과인데 truncate 누락 = 코드 버그. 실수로 한도 넘으면 위 4xx 경로로 `False`. |
| 분할 메시지 일부 실패 | 남은 메시지 POST 는 계속. 전체 결과 `False` → `status=failed` 로 N+M 행 일괄 INSERT (결정 [4]). |
| `notifications` INSERT 실패 | 1단계 명세 범위 외. `db.transaction()` 의 rollback 으로 해당 사이클 이력만 사라짐. 다음 사이클로 진행. |
| service 자체 예외 | 영역 1 의 `run_cycle` 이 try/except 로 잡아 로그 (영역 1 §5). 영역 2 에서 추가로 잡지 않음. |

**중요 정책 — 발송 실패 누락**: `status=failed` 로 기록된 공지는 **자동 재시도하지 않음** (functional-spec §영역 2 ⚠ 그대로). 다음 사이클의 신규/수정 판별 기준이 DUID·modified_date 라서, 이 공지는 같은 상태로는 다시 알림 대상에 잡히지 않는다 → 누락. 개선은 TODO.

**재시도 정책 TODO**: 현재 모든 HTTP 에러에 재시도 3회. 4xx 는 재시도해도 결과 동일이라 비효율 — 5xx·타임아웃 한정 재시도 + 지수 백오프는 영역 1 TODO 1 과 같은 정책으로 1단계 후 처리. (`_pre-impl-checklist.md` §6 TODO 1 과 묶어서.)

---

## 6. 영역 2가 다루는 DB 스키마 (발췌)

### 6.1 읽기

```sql
SELECT discord_webhook_url FROM users WHERE id = :uid;
```

### 6.2 쓰기

```sql
INSERT INTO notifications
    (user_id, notice_duid, channel_id, type_id, status_id, sent_at)
VALUES
    (:uid, :duid, :ch, :type, :status, :sent_at);
-- executemany 로 (new + modified) 묶음 1회.
```

### 6.3 영역 2가 *건드리지 않는* 테이블

`notices`, `attachments`, `categories`, `messages`, `user_settings`, `user_custom_times`,
`frequency_modes`, `notification_channels`, `notification_types`, `notification_statuses`.

매핑 테이블 3개 (`notification_*`) 는 시드에 고정된 ID 를 코드 상수로 들고 사용하므로 SELECT 안 함.

---

## 7. ERD / DB 스키마 동기화 액션 (본 구현 시작 전)

영역 1 §10 에 이어, 결정 [1] 의 결과:

### 7.1 `messages` 테이블 시드 — 한정
- `notification.*` 로 시작하는 키는 **시드에서 제거**한다 (예: `notification.discord.header.new`, `notification.discord.line.new`, `notification.discord.footer` 등).
- `messages` 는 **UI 라벨 전용**으로 한정 — `ui.label.*` 만 시드.
- `db-schema.txt` 의 `messages` 테이블 Note 에서 "알림 템플릿 포함" 표현도 제거.

### 7.2 `notification_*` 매핑 테이블
- 코드 상수와 일관: discord=1, kakao=2 / new=1, modified=2 / success=1, failed=2. 시드 그대로.

### 7.3 본 구현 시 채널 추가 (1.5단계)
- 카카오 추가 시 `notifier/kakao.py` 신설 + `NotificationChannel` Protocol 만족.
- 어댑터 dispatch 는 `users` 행에 채워진 컬럼 (`discord_webhook_url` / `kakao_phone`) 기준으로 service 가 분기.
- 템플릿 분리 (`notifier/templates.py`) 검토는 1.5단계 진입 시.

---

## 8. 영역 1 ↔ 영역 2 인터페이스 (수신 측 확정)

영역 1 §9 의 인터페이스를 영역 2 가 다음과 같이 받는다.

```python
# notifier/service.py
def send(new: list[ParsedNotice],
         modified: list[ParsedNotice],
         user_id: int = config.DEFAULT_USER_ID) -> None: ...
```

| 항목 | 보장 / 비보장 |
|---|---|
| 두 리스트 둘 다 비어 있음 | 발생하지 않음 (영역 1 보장). 들어와도 §3.2 누락 규칙으로 안전하지만 service 가 사전 return 하지 않음. |
| `is_active=False` 상태 | 영역 1 보장으로 호출 안 됨. service 가 재확인 안 함. |
| DB 트랜잭션 상태 | 영역 1 보장: 호출 시점에 영역 1 트랜잭션은 *닫혀 있음*. service 가 자체 트랜잭션을 연다. |
| `ParsedNotice` 객체 취급 | 영역 2 는 **읽기만**. mutate 금지 (frozen dataclass 라 컴파일·런타임 모두 차단). |
| `NotificationItem` 추상화 | 1단계는 미사용 — 영역 1 의 `ParsedNotice` 그대로 사용. 1.5단계 카카오 추가 시점에 분리 재검토. |
| 발송 결과 반환 | `None` — 영역 1 으로 결과 안 돌려줌. 이력은 `notifications` 에 직접 기록. |
| 예외 누출 | service 는 의도된 경로 외 예외를 영역 1 으로 누출하지 않으려 하나 (`_post` 는 잡지만 DB·코드 버그는 누출). 영역 1 의 `run_cycle` try/except 가 안전망. |

---

## 9. 검증 체크리스트

- [ ] 빈 webhook (`users.discord_webhook_url IS NULL`) 상태에서 알림 호출 → 로그 1줄, `notifications` 행 (new+modified) 증가, 전부 `status_id=2`.
- [ ] 유효 webhook + Discord 정상 응답 + 본문 ≤ 1900 → Discord 채널에 메시지 1건 도달, `notifications` 행 (new+modified) 만큼 추가, 전부 `status_id=1`.
- [ ] 유효 webhook + Discord 응답 500 → 재시도 3회 로그 후 `status_id=2` 로 (new+modified) 행 INSERT.
- [ ] 메시지 본문 양식 §3.1 와 정확히 일치 — 섹션 누락 규칙·📎·마크다운 링크·footer 형식 포함.
- [ ] `sent_at` 가 모든 행에서 동일 (`SELECT DISTINCT sent_at` 결과 1행).
- [ ] new=2 modified=1 입력 시: notifications 의 type_id 분포 = `{1: 2, 2: 1}`.
- [ ] 메시지 템플릿 상수가 `notifier/discord.py` 안에 있고 `messages` 테이블 SELECT 가 없음.
- [ ] **분할 — 본문 ≤ 1900** → `_build_messages` 결과 길이 1, 페이지 표기 없음, footer 단일 메시지 끝.
- [ ] **분할 — 본문 > 1900** → 결과 길이 ≥ 2, 각 메시지 ≤ 1900, 각 섹션 첫 청크 헤더 `(idx/total)`, 동일 섹션 이어지는 청크 헤더 `(이어서 idx/total)`, footer 는 마지막 청크에만.
- [ ] **분할 — POST 간격** → 메시지 N 개 발송 시 `_post_one` 사이 0.5초 sleep, 단일 메시지 시 sleep 없음.
- [ ] **분할 — 부분 실패** → 첫 청크 200, 두 번째 청크 500 시 `_post_all → False`, `notifications` N+M 행 모두 `status_id=2`, 그래도 첫 청크는 Discord 에 실제 도달했음을 채널 로그로 확인.
- [ ] **5/20 인시던트 재현 회귀** — new=20 mod=12 입력 시 `_build_messages` 가 ≥ 2 청크 반환, 모든 청크 ≤ 1900, Discord 도달 OK.
- [ ] 단일 라인이 LINE_MAX_LEN(1800) 초과 입력 시 `…` 으로 절단되어 한도 안에 들어옴.
