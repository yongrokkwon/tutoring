# 영역 3 — 공지 조회 기술 명세서

**버전**: v1.0
**작성일**: 2026-05-16
**상위 문서**: `docs/source-spec/functional-spec.md` §영역 3, `docs/source-spec/requirements.md` §9
**선행 명세**:
- `area-1-crawler.md` §6.2 (영역 1 이 쓰는 `notices`·`attachments` 를 영역 3 이 읽음)
- `area-4-settings.md` §1 (`web/`·`_base.html`·CSS 공유)
**범위**: Flask 웹페이지의 `/`·`/notices` 라우트. `notices` SELECT + `categories` JOIN + `attachments` EXISTS. Jinja2 렌더링.
**범위 외**: 공지 상세 페이지 / 알림 이력 / 수동 크롤링 / 페이지네이션 / 검색·필터 (모두 TODO).
**상위 결정 반영**:
- [1] 정렬 = `is_pinned DESC, MAX(posted_date, modified_date) DESC, updated_at DESC, duid DESC`. `MAX` 는 SQLite **스칼라 함수** (2 인자 이상).
- [2] 고정 공지는 정렬 1차 키 (`is_pinned DESC`) 로 항상 상단.
- [3] 카테고리 표시 = 평문 (대괄호 없음).
- [4] 빈 DB 안내 = 인라인 단문 `"공지가 없습니다. 잠시 후 다시 확인해주세요."`.
- [5] CSS = `kw_notice/web/static/style.css` 외부 파일.
- [6] 메뉴 active = `request.endpoint` 비교. 설정 메뉴는 `startswith('settings.')` 로 하위 라우트 포함.
- [추가] ✏️ 마크 = `modified_date > posted_date` 인 모든 공지. 알림 발송 여부와 무관.

---

## 1. 모듈 / 파일 구조

```
kw_notice/
├── web/
│   ├── __init__.py             # create_app() — notices.bp 추가 등록 (영역 4 와 함께)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── notices.py          # Blueprint('notices') — / 리다이렉트 + /notices
│   │   └── settings.py         # 영역 4 (변경 없음)
│   ├── static/
│   │   └── style.css           # 간단한 테이블·메뉴·flash CSS (신설)
│   └── templates/
│       ├── _base.html          # 영역 4 가 정의 — 영역 3 도 그대로 상속. 메뉴 active 표시 책임.
│       └── notices/
│           └── index.html      # GET /notices
└── repository/
    └── notices.py              # 영역 1 의 get/insert/update + 영역 3 의 list_recent() 추가
```

**책임 분리 원칙**:
- `routes/notices.py` 는 HTTP·Jinja2 만. SQL 직접 작성 금지.
- `repository/notices.py` 의 `list_recent()` 가 단일 책임: 정렬·JOIN·EXISTS 까지 한 SQL 안에서.
- `_base.html` 은 영역 3 이 새로 만들지 않는다 — 영역 4 정의를 그대로 상속. 영역 3 의 변경 사항은 *오직 메뉴 active 표시 로직* (영역 4 에서는 settings 만 active 였던 자리).

영역 1 의 `repository/categories.py`·`attachments.py` 는 영역 3 이 호출하지 않는다 — 모든 카테고리·첨부 정보는 `list_recent()` 의 단일 SQL 에 묶여 들어옴.

---

## 2. 핵심 함수 시그니처 + 책임

### 2.1 `web/routes/notices.py`

| 시그니처 | 책임 |
|---|---|
| `bp = Blueprint('notices', __name__)` | 모듈 최상단. |
| `@bp.get('/')` `def root() -> Response` | `redirect(url_for('notices.index'))`. functional-spec §영역 3 라우팅 표 그대로. |
| `@bp.get('/notices')` `def index() -> str` | `with db.transaction() as conn: rows = notices_repo.list_recent(conn)` → `render_template('notices/index.html', notices=rows)`. |

내부 helper 없음. 영역 4 보다 단순.

### 2.2 `repository/notices.py` — 영역 3 이 추가하는 함수

| 시그니처 | 책임 |
|---|---|
| `list_recent(conn, limit: int = 100) -> list[sqlite3.Row]` | 정렬·JOIN·EXISTS 한 SQL. `sqlite3.Row` 그대로 반환 (view-only 라 별도 dataclass 미작성). 컬럼: `duid, title, author, posted_date, modified_date, is_pinned, url, category_name, has_attachment`. ※ TODO 7 (공지 상세 페이지) 진입 시 detail view 가공이 필요해지면 그 시점에 `NoticeListItem`·`NoticeDetail` 같은 dataclass 도입 검토. |

영역 1 이 정의한 `count/get/insert/update` 와 같은 파일에 위치. 4개 함수 + 신규 1개 = 5개.

### 2.3 `web/__init__.py` — 영역 4 의 함수 확장

영역 4 §2.1 의 `create_app()` 에 한 줄 추가:
```python
from kw_notice.web.routes import notices as notices_routes
app.register_blueprint(notices_routes.bp)
```

다른 변경 없음. `secret_key`·`_base.html`·flash 처리는 영역 4 가 정의한 그대로.

---

## 3. 라우트별 처리 흐름

### 3.1 `GET /`

```
return redirect(url_for('notices.index'))   # 302
```

functional-spec §영역 3 라우팅 표 그대로.

### 3.2 `GET /notices`

```
with db.transaction() as conn:
    rows = notices_repo.list_recent(conn, limit=100)
return render_template('notices/index.html', notices=rows)
```

**트랜잭션 짧음** — SELECT 1회만. 명시적으로 transaction 컨텍스트를 쓰는 이유: `db.connect()` 직접 호출 시 close 누락 위험 회피 (영역 1·2·4 와 동일 패턴). 컨텍스트 매니저 패턴 일관성 목적이지 트랜잭션 시멘틱이 필수인 것은 아님 — SQLite 는 SELECT 를 `BEGIN/COMMIT` 으로 감싸도 무비용. read-only 컨텍스트 분리 (`db.read_only()` 같은 별도 헬퍼) 는 TODO.

---

## 4. SQL — 정렬 기준 명세

```sql
SELECT
    n.duid,
    n.title,
    n.author,
    n.posted_date,
    n.modified_date,
    n.is_pinned,
    n.url,
    c.name AS category_name,
    EXISTS(SELECT 1 FROM attachments a
            WHERE a.notice_duid = n.duid) AS has_attachment
FROM notices n
JOIN categories c ON c.id = n.category_id
ORDER BY
    n.is_pinned DESC,
    MAX(n.posted_date, n.modified_date) DESC,
    n.updated_at DESC,
    n.duid DESC
LIMIT 100;
```

### 4.1 정렬 키별 근거

| 우선순위 | 컬럼 | 근거 |
|---|---|---|
| 1 | `is_pinned DESC` | 고정 공지 항상 상단 (결정 [2]). 광운대 원본 페이지의 표시 순서와 일치. |
| 2 | `MAX(posted_date, modified_date) DESC` | "최근 활동" 기준 — 수정된 공지가 자연스럽게 위로. db-schema.txt 의 권장 정책. |
| 3 | `updated_at DESC` | 같은 날짜 안에서 DB 가 마지막으로 수정한 순서 (수정 감지 시각). |
| 4 | `n.duid DESC` | 결정적 tie-breaker — 같은 시각에 발견된 다건의 안정 정렬. |

### 4.2 SQLite `MAX` 주의

`MAX(col1, col2, ...)` 는 **2개 이상 인자** 가 들어가면 **스칼라 함수** — 각 행마다 인자 중 큰 값 반환. **인자 1개** 면 *집계 함수* 로 해석돼 그룹 최댓값을 반환. 본 명세서의 `MAX(n.posted_date, n.modified_date)` 는 2 인자라 스칼라. `GROUP BY` 없이도 안전. (`max()` 소문자도 동일.)

문자열 비교: `'YYYY-MM-DD'` 형식 (CHECK 제약으로 보장됨) 이라 사전순 비교 = 날짜 순 비교. 그대로 동작.

---

## 5. 데이터 흐름

```
[브라우저] ── GET / ────────────────────────────────┐
                                                   ▼
                              routes.notices.root
                                       │
                                       ▼
                              302 redirect /notices

[브라우저] ── GET /notices ─────────────────────────┐
                                                   ▼
                              routes.notices.index
                                       │
                                       ▼ db.transaction() open
                              notices_repo.list_recent(conn, 100)
                                       │  단일 SELECT (JOIN categories + EXISTS attachments)
                                       ▼  list[Row]
                              db.transaction() close
                                       │
                                       ▼
                              render_template notices/index.html
                                       │
                                       ▼
                              HTML 응답
```

**단일 SELECT 원칙**: 카테고리명·첨부 유무를 모두 한 쿼리에서 해결 → N+1 회피. 100건 × 2회 추가 쿼리가 일어나지 않음.

---

## 6. 표시 컬럼 + 부가 마크

### 6.1 컬럼 (functional-spec §영역 3 출력 그대로)

| 컬럼 | 내용 |
|---|---|
| 카테고리 | `category_name` (평문, 대괄호 없음). |
| 제목 | `📌 ` (조건부) + `title` + ` 📎` (조건부) + ` ✏️` (조건부). |
| 작성자 | `author`. |
| 일자 | `posted_date == modified_date` → `작성: {posted_date}`; 아니면 → `작성: {posted_date} / 수정: {modified_date}`. |
| 원문 | `<a href="{url}" target="_blank" rel="noopener">원문</a>`. |

### 6.2 부가 마크

| 마크 | 조건 | 위치 |
|---|---|---|
| 📌 | `is_pinned == 1` | 제목 앞 (공백 1칸 뒤). |
| 📎 | `has_attachment == 1` (`EXISTS attachments` 결과) | 제목 뒤 (공백 1칸 앞). |
| ✏️ | `modified_date > posted_date` | 📎 뒤 (있으면) / 제목 뒤 (없으면). **알림 발송 여부와 무관하게 표시** — 첫 실행 이전에 수정됐던 공지도 포함 (영역 1 의 첫 실행 정책에 따라 알림은 안 갔지만 DB 의 `modified_date` 는 저장됨). |

### 6.3 원칙 — 매체별 가공 격리

`category_name` 은 `ParsedNotice` 가 보유한 값 (대괄호 없는 한글명, 영역 1 §4.2). **표시 매체별 가공은 그 영역 안에서만**:
- 영역 2 (Discord 평문) → `[{category_name}]` 로 대괄호 부여.
- 영역 3 (HTML 표) → 컬럼 자체가 구분이므로 평문 그대로.

영역 3 가 영역 2 의 가공 로직을 import 하지 않는다.

---

## 7. 카테고리 / 첨부 / URL — 영역 1 결정과의 연결

| 항목 | 영역 1 에서 정의 | 영역 3 의 사용 |
|---|---|---|
| `categories.name` | 결정 [1] (source of truth, §10.2). | `JOIN categories c ON c.id = n.category_id` 으로 표시명 확보. |
| `notices.url` | 결정 [2] (NOT NULL 컬럼, §10.1). | 원문 링크 `<a href="...">`. |
| `attachments` 행 존재 = 첨부 마크 | 영역 1 §1 (`has_attachment` 컬럼 없음, EXISTS 로 판정). | `EXISTS(SELECT 1 FROM attachments ...)` 으로 동일 판정. |

영역 1 의 ERD 동기화 액션 (§10) 이 본 구현 시작 전 반영되어야 영역 3 SQL 이 동작한다.

---

## 8. 에러 처리 위치와 정책

| 발생 지점 | 정책 |
|---|---|
| DB 조회 실패 | 1단계 명세 범위 외 (functional-spec §영역 3 ④). `try/except` 로 잡고 `print` 로그 + Flask 기본 500 페이지. `try/except` 위치: `routes.notices.index` 안 단일 try/except 블록. |
| `notices` 가 비어 있음 / N < 100 | 정상 동작. 템플릿에서 `{% if notices %}` 분기. 0 건이면 인라인 안내 표시 (§6.4 빈 상태). |
| `categories.id` 가 `JOIN` 으로 매칭 실패 (시드 누락 등) | 영역 1 의 classifier 가 매핑 실패 행을 INSERT 안 함 (영역 1 §2.5) → DB 에 도달하지 않음. `INNER JOIN` 으로 안전. 잘못된 데이터가 들어와 있어도 그 행만 결과에서 사라짐. |
| URL 컬럼 NULL | 영역 1 §10.1 `NOT NULL` 제약으로 발생 불가. 발생 시 INSERT 가 먼저 깨짐. |
| Jinja 렌더링 실패 | Flask 기본 500. |

**로그 매체**: `print` (requirements §11-3).

---

## 9. 영역 3가 다루는 DB 스키마 (발췌)

### 9.1 읽기 (쓰기 없음)

```sql
-- 메인 쿼리 (§4 그대로)
SELECT n.*, c.name, EXISTS(...) FROM notices n
JOIN categories c ON c.id = n.category_id
ORDER BY n.is_pinned DESC, MAX(n.posted_date, n.modified_date) DESC,
         n.updated_at DESC, n.duid DESC
LIMIT 100;
```

### 9.2 영역 3가 *건드리지 않는* 테이블

`users`, `user_settings`, `user_custom_times`, `notifications`, `notification_*`,
`frequency_modes`, `messages`. — `messages` 도 영역 3 가 SELECT 하지 않음 (UI 라벨 동적 조회는 1단계 미사용, 모든 텍스트는 템플릿 안 한글 리터럴 또는 코드 상수).

---

## 10. 영역 3 ↔ 다른 영역 인터페이스

### 10.1 데이터 의존 (단방향 읽기)

| 데이터 | 쓰는 영역 | 읽는 영역 3 |
|---|---|---|
| `notices.*` | 영역 1 (INSERT/UPDATE) | 메인 쿼리. |
| `attachments` 행 존재 | 영역 1 (placeholder INSERT / DELETE) | EXISTS 절. |
| `categories.id, name` | (시드 + ERD §10.2) | JOIN. |

영역 3 은 어느 영역과도 함수 호출 인터페이스를 공유하지 않는다.

### 10.2 Flask 앱 자원 공유 (영역 4 와)

| 자원 | 정의 영역 | 사용 |
|---|---|---|
| `create_app()` Flask 인스턴스 | 영역 4 §2.1 | 영역 3 이 Blueprint 등록만 추가 (§2.3). |
| `_base.html` 네비게이션 | 영역 4 §1 | 영역 3 의 모든 페이지가 상속. |
| `flash` 메커니즘 | 영역 4 §1 / §3.1 | 영역 3 는 flash 발생 케이스가 없지만 (사용자 입력 폼 없음), 메뉴 자체는 자동 표시. |
| `static/style.css` | 영역 3 §1 (신설) | 영역 4 의 페이지에서도 동일 적용. 본 명세 단계에 통합. |

### 10.3 메뉴 active 표시 로직 (`_base.html`)

```jinja
<nav>
  <a href="{{ url_for('notices.index') }}"
     class="{{ 'active' if request.endpoint == 'notices.index' else '' }}">
    공지
  </a>
  <a href="{{ url_for('settings.index') }}"
     class="{{ 'active' if request.endpoint and request.endpoint.startswith('settings.') else '' }}">
    설정
  </a>
</nav>
```

- `notices.index` 는 단일 엔드포인트라 `==` 비교.
- `settings.*` 는 `index` 외 `save`, `times_add_grid`, `times_add_save`, `times_delete` 가 있어 `startswith('settings.')` 로 하위 라우트 모두 포함 (결정 [6]).

`_base.html` 은 영역 4 가 만든 파일이지만 위 nav 부분은 영역 3 명세 단계에서 확정 — 본 구현 시 한 번에 작성.

### 10.4 CSS 시각적 요구사항 (본 구현 자유, 충족 필수)

`static/style.css` 의 구체 룰은 본 구현에 위임하되, 다음 5개 시각적 요구사항을 충족해야 한다:

- **테이블**: 행 구분이 가능 (zebra 줄무늬 또는 행 사이 border).
- **메뉴 `.active`**: 시각적으로 명확히 구분 (밑줄 / 배경색 / 굵게 — 어느 방식이든).
- **flash 메시지**: 일반 콘텐츠와 시각적으로 분리 (테두리 / 배경색 강조).
- **빈 상태 안내**: 가운데 정렬 또는 충분한 padding 으로 *데이터가 비어 있다* 임이 한눈에 보이게.
- **부가 마크 (📌·📎·✏️)**: 제목과 줄바꿈 없이 한 줄에 묶이게 (white-space / 적절한 inline 처리).

---

## 11. 본 구현 시작 전 동기화 액션 (영역 3 추가분)

영역 3 명세 결정에 따라 source 문서 한 곳에 갱신 필요.

### 11.1 `docs/source-spec/functional-spec.md` §영역 3 처리흐름 ① 갱신
현재:
> 정렬: 1차 작성일 DESC, 2차 DUID DESC

다음으로 교체:
> 정렬: 1차 `is_pinned` DESC, 2차 `MAX(posted_date, modified_date)` DESC, 3차 `updated_at` DESC, 4차 DUID DESC.
> `MAX` 는 SQLite 의 스칼라 함수 (2 인자, 집계 아님).

### 11.2 추가 ERD/source 액션 없음
- 영역 3 은 스키마 변경 추가 없음.
- 영역 1 의 §10 (notices.url, categories.name) + 영역 4 의 §8 액션이 그대로 본 구현 전 반영되어야 영역 3 SQL 이 동작. 이를 위해 영역 3 검토 통과 후 별도 `_pre-impl-checklist.md` 에 일괄 집계.

---

## 12. 검증 체크리스트

### 12.1 라우팅
- [ ] `GET /` → 302 redirect `/notices`.
- [ ] `GET /notices` → 200 + HTML.

### 12.2 정렬
- [ ] 고정 공지 5건 + 일반 95건 → 고정 5건이 상단, 일반 95건 그 다음 (총 100건).
- [ ] 같은 우선순위 안에서 `MAX(posted, modified) DESC` 순.
- [ ] `posted = 2026-05-15, modified = 2026-05-20` 공지가 `posted = 2026-05-18, modified = 2026-05-18` 공지보다 위.
- [ ] 모두 같은 날짜인 동률 → `updated_at DESC, duid DESC` 로 결정적 정렬.

### 12.3 표시
- [ ] 카테고리 표시 = 평문 ("국제학생", 대괄호 없음).
- [ ] `is_pinned=1` → `📌 ` 가 제목 앞.
- [ ] `attachments` 행 있는 공지 → ` 📎` 가 제목 뒤.
- [ ] `modified_date > posted_date` → ` ✏️` 표시 + 일자 컬럼 `작성: A / 수정: B`.
- [ ] `modified_date == posted_date` → ✏️ 없음, 일자 컬럼 `작성: A`.
- [ ] 원문 링크 `target="_blank"` + `rel="noopener"`.

### 12.4 빈 상태
- [ ] DB 가 비어 있음 → "공지가 없습니다. 잠시 후 다시 확인해주세요." 인라인 표시. 테이블 헤더는 안 그려도 됨 / 그려도 됨 (구현 선택).

### 12.5 메뉴 active
- [ ] `/notices` 접근 → "공지" 메뉴에 `.active`.
- [ ] `/settings` 접근 → "설정" 메뉴에 `.active`.
- [ ] `/settings/times/add` 접근 → "설정" 메뉴에 `.active` (startswith 적용).

### 12.6 N+1 회피
- [ ] 100건 표시 시 DB 쿼리 1회만 (메인 SELECT). 카테고리·첨부 추가 쿼리 없음.

### 12.7 고정 공지 비중 (1단계는 *관찰 항목*, 본 구현 후 표시 결정용)
- [ ] 광운대 페이지 특성상 `is_pinned=1` 공지가 50~70건 분포 (area-1 §4.2 비고). LIMIT 100 안에서 고정이 절반 이상을 차지해 일반 공지 가시성이 떨어지는지 *관찰만*.
- 1단계 처리 안 함 — 페이지네이션 (TODO 9) / 카테고리 필터 (TODO 10) 도입 시점에 **고정 공지 별도 섹션 분리** 검토 (예: 페이지 상단 고정 N건 + 일반 N건 분리 표시).
