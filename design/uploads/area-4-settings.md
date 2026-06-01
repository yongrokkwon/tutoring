# 영역 4 — 설정 관리 기술 명세서

**버전**: v1.3
**작성일**: 2026-05-20
**상위 문서**: `docs/source-spec/functional-spec.md` §영역 4, `docs/source-spec/requirements.md` §4·§9
**선행 명세**: `area-1-crawler.md` §6.1 (영역 1 이 `user_settings`·`user_custom_times` 를 읽음)
**범위**: Flask 웹페이지의 `/settings` 라우트군. `user_settings` UPDATE, `user_custom_times` INSERT/DELETE. 시각 추가 그리드 UI.
**범위 외**: 인증·세션 (1단계 1인 로컬), CSRF (3단계 공개 서비스에서 도입), JS 모달 (TODO), 카카오 채널 컬럼 UI.
**상위 결정 반영**:
- [1] 삭제 입력 = `user_custom_times.id` 단일화 (`time_hhmm` 미지원).
- [2] `is_active` 체크박스 = `'is_active' in request.form` 키 존재 검사.
- [3] CSRF 미적용 (1단계). 3단계 도입은 `requirements.md` §14 에 명시 — 본 구현 시작 전 액션.
- [4] 폼 검증 실패 시 입력값 보존하지 않음 — DB 의 직전 값으로 표시되고 flash 에러 메시지만 별도 전달.
- [5] 시각 일괄 추가. 전체 트랜잭션 — 1건이라도 검증/INSERT 실패면 **전체 거부**.

---

## 1. 모듈 / 파일 구조

```
kw_notice/
├── web/
│   ├── __init__.py             # create_app() — Flask app factory, Blueprint 등록, secret_key
│   ├── routes/
│   │   ├── __init__.py
│   │   └── settings.py         # Blueprint('settings') — 5개 라우트 + 폼 파싱 helper
│   └── templates/
│       ├── _base.html          # 공통 네비게이션 (공지 / 설정), flash 영역
│       └── settings/
│           ├── index.html      # GET /settings 본 페이지
│           └── times_add.html  # GET /settings/times/add 그리드
└── repository/
    └── settings.py             # 영역 1 의 load() + 영역 4 의 쓰기 함수 3개 추가
```

**책임 분리 원칙**:
- `routes/settings.py` 는 HTTP·Jinja2·flash 만 다룬다. SQL 쿼리 직접 작성 금지.
- `repository/settings.py` 는 SQL 만 다룬다. `request.form` 같은 Flask 객체 모름.
- 폼 파싱·검증은 라우트 모듈 안 helper 함수 (영역 4 규모상 별도 forms 모듈 분리는 over-design).
- 템플릿은 표시만 — 검증 로직 없음.

영역 1 의 `repository/notices.py`·`attachments.py` 같은 다른 영역 repository 는 영역 4 가 호출하지 않는다.

> `_base.html` 의 nav 마크업·메뉴 active 표시 로직은 `area-3-viewer.md` §10.3 에서 최종 확정 — 본 구현 시 한 번에 작성.

---

## 2. 핵심 함수 시그니처 + 책임

### 2.1 `web/__init__.py`

| 시그니처 | 책임 |
|---|---|
| `create_app() -> Flask` | Flask 인스턴스 생성, `secret_key` 설정 (flash 용), `routes.settings.bp` Blueprint 등록. 영역 3 의 Blueprint 도 여기서 등록 (영역 3 명세 단계에서 추가). |

`secret_key` 는 환경변수 `KW_NOTICE_SECRET_KEY` 우선, 없으면 `dev-secret-key` 하드코딩 (로컬 1단계 한정 — 본 구현 시 별도 환경 처리). **환경변수 미설정 시 `create_app()` 안에서 stderr 경고 1줄 출력**:
```python
print("WARNING: KW_NOTICE_SECRET_KEY not set, using dev fallback",
      file=sys.stderr)
```
근거: dev fallback 이 운영 환경에 흘러가는 사고를 시동 시점에 즉시 인지.

### 2.2 `web/routes/settings.py`

| 시그니처 | 책임 |
|---|---|
| `bp = Blueprint('settings', __name__)` | 모듈 최상단. URL prefix 없음. |
| `@bp.get('/settings')` `def index() -> str` | DB 로드 → `settings/index.html` 렌더. |
| `@bp.post('/settings')` `def save() -> Response` | 폼 검증 → `repository.settings.update` → redirect `/settings`. 검증 실패 시 flash + redirect. |
| `@bp.get('/settings/times/add')` `def times_add_grid() -> str` | 15분 단위 그리드 + 기존 등록 시각 set → `settings/times_add.html` 렌더. |
| `@bp.post('/settings/times/add')` `def times_add_save() -> Response` | 다중 시각 검증 → `add_custom_times` (executemany, 전체 트랜잭션) → redirect `/settings`. 1건 실패 시 전체 거부 + flash. |
| `@bp.post('/settings/times/delete')` `def times_delete() -> Response` | `id` 정수 변환 → `delete_custom_time` → redirect `/settings`. |
| `@bp.post('/settings/test-send')` `def test_send() -> Response` | 운영시간·is_active 무관하게 Discord 알림을 즉시 1회 발송 (테스트). DB 최신 1건을 `ParsedNotice` 로 wrap → `DiscordChannel._build_messages` + `_post_all` 직접 호출 (영역 2 의 `service.send()` **비경유** — `notifications` 이력 INSERT 안 함, 실 통계 오염 방지). 단건이라 분할은 일어나지 않지만 prod 와 동일 경로 사용. 결과를 flash 로 통지 후 redirect `/settings`. |

**모듈 상수**:
```python
FREQUENCY_NAME_TO_ID = {
    'custom': 0,
    'high':   1,
    'medium': 2,
    'low':    3,
}
GRID_INTERVAL_MIN = 15
```

**내부 helper (단일 책임)**:

| 시그니처 | 책임 |
|---|---|
| `_parse_frequency_mode(form) -> int \| None` | 텍스트 → ID. 매핑 실패면 `None`. |
| `_parse_is_active(form) -> bool` | `'is_active' in form` ([2] 결정). |
| `_parse_selected_times(form) -> list[str]` | `form.getlist('time')` 그대로 반환. 정렬·중복 제거 X — 검증이 책임. |
| `_validate_times(candidates: list[str], existing: set[str]) -> tuple[list[str] \| None, str \| None]` | 정상이면 `(times_sorted, None)`, 실패면 `(None, "에러 메시지")`. 첫 실패 시 즉시 반환 ([5] 결정). |
| `_grid_times() -> list[str]` | `['10:00', '10:15', ..., '17:00']` 29개. (high 모드 발동 시각과 동일.) |

### 2.3 `repository/settings.py` — 영역 4 가 추가하는 함수

영역 1 의 `load(conn, user_id)` 는 그대로 유지. 다음 3개 추가:

| 시그니처 | 책임 |
|---|---|
| `update(conn, user_id, frequency_mode: int, is_active: bool) -> None` | `UPDATE user_settings SET frequency_mode=?, is_active=?, updated_at=datetime('now') WHERE user_id=?`. |
| `add_custom_times(conn, user_id, times: list[str]) -> None` | `executemany` 로 N행 일괄 INSERT. UNIQUE 위반은 호출자(라우트)가 try/except 로 잡아 flash. |
| `delete_custom_time(conn, user_id, custom_time_id: int) -> None` | `DELETE FROM user_custom_times WHERE id=? AND user_id=?`. 존재 여부 검증 안 함 — `WHERE` 매치 0건은 무오류. |
| `list_custom_times_with_id(conn, user_id) -> list[tuple[int, str]]` | 삭제 폼에 필요한 `(id, time_hhmm)` 쌍을 시각순으로 반환. 영역 1 의 `UserSettings.custom_times` (`tuple[str, ...]`) 는 스케줄러 trigger 용으로 id 가 불필요해 그대로 유지 — 영역 4 만 id 가 필요해 별도 함수 분리. |

---

## 3. 라우트별 처리 흐름

### 3.1 `GET /settings`

```
load(conn, user_id=1)
  → UserSettings(frequency_mode, is_active, custom_times)
  ↓
render_template('settings/index.html',
    settings=...,
    frequency_id_to_name={v:k for k,v in FREQUENCY_NAME_TO_ID.items()})
  ↓
HTML
```

템플릿 표시 항목:
- 4개 라디오 버튼 (`high`/`medium`/`low`/`custom`). `settings.frequency_mode` 와 일치하는 항목 `checked`.
- `is_active` 체크박스 — `settings.is_active==True` 면 `checked`.
- `frequency_mode == 0(custom)` 일 때 custom_times 영역 표시:
  - 라우트가 `list_custom_times_with_id(conn, uid)` 호출 → 템플릿에 `(id, time_hhmm)` 쌍 리스트 전달.
  - **비어 있음** → 인라인 단문 `"등록된 시각이 없습니다"` + `[+ 시각 추가]` 버튼만.
  - **있음** → 시각 목록 (각 행 우측 `[삭제]` 버튼, hidden `<input name="id" value="{custom_time.id}">`) + `[+ 시각 추가]` 버튼.
- `frequency_mode != 0` 이면 custom_times 영역 자체 미렌더.
- flash 메시지 표시는 `_base.html` 이 `{% with messages = get_flashed_messages() %}` 블록으로 처리 — 모든 페이지에서 자동 표시 (영역 3 페이지에서도 동일).

### 3.2 `POST /settings`

```
mode_id = _parse_frequency_mode(request.form)
is_active = _parse_is_active(request.form)

if mode_id is None:
    flash("error.invalid_frequency_mode")     # 메시지 본문은 코드 상수
    return redirect(url_for('settings.index'))

with db.transaction() as conn:
    settings_repo.update(conn, DEFAULT_USER_ID, mode_id, is_active)

return redirect(url_for('settings.index'))    # PRG
```

**검증 실패 정책 (결정 [4])**: 폼 입력값을 redirect 후 GET 에서 다시 채우지 않는다. DB 의 직전 값이 자동으로 그대로 표시됨. 사용자 친화성보다 단순함을 택함.

### 3.3 `GET /settings/times/add`

```
load(conn, user_id=1)
  → 등록된 시각 set
  ↓
grid = _grid_times()    # 29개
  ↓
render_template('settings/times_add.html',
    grid=grid,
    registered={set of HH:MM})
  ↓
HTML
```

템플릿 동작:
- 7행 × 4열 그리드 + 마지막 `17:00`.
- 이미 등록된 시각은 `disabled` 또는 시각적으로 구분 (CSS 클래스 `.registered`).
- 체크박스 `<input type="checkbox" name="time" value="HH:MM">` 다중 선택.
- 키보드 입력 없음 — 텍스트 input 미사용 (functional-spec §영역 4 GET /settings/times/add).

### 3.4 `POST /settings/times/add`

```
candidates = _parse_selected_times(request.form)   # form.getlist('time')

if not candidates:
    flash("error.no_time_selected")
    return redirect(url_for('settings.times_add_grid'))

with db.transaction() as conn:
    existing = {r.time_hhmm for r in load(conn, uid).custom_times}
    valid, err = _validate_times(candidates, existing)
    if err:
        flash(err)
        return redirect(url_for('settings.times_add_grid'))
    try:
        settings_repo.add_custom_times(conn, uid, valid)
    except sqlite3.IntegrityError:
        # race condition — 단일 사용자라 사실상 도달 안 함.
        flash("error.time_conflict")
        return redirect(url_for('settings.times_add_grid'))

return redirect(url_for('settings.index'))
```

**검증·INSERT 모두 같은 트랜잭션** — 1건 실패면 전체 rollback ([5] 결정).

### 3.5 `POST /settings/times/delete`

```
try:
    cid = int(request.form['id'])
except (KeyError, ValueError):
    return redirect(url_for('settings.index'))   # 조용히 무시 (idempotent)

with db.transaction() as conn:
    settings_repo.delete_custom_time(conn, DEFAULT_USER_ID, cid)

return redirect(url_for('settings.index'))
```

functional-spec §영역 4 POST /settings/times/delete: "존재하지 않는 ID: 무시". 그대로 따름.

### 3.6 `POST /settings/test-send`

```
with db.transaction() as conn:
    webhook = users_repo.get_discord_webhook(conn, uid)
    if webhook is None:
        flash("error.test_send_no_webhook"); return redirect /settings

    rows = list_recent(conn, limit=1)
    if not rows:
        flash("error.test_send_no_notices"); return redirect /settings
    cat = categories.name_to_id 역방향 — `categories.name`

item = ParsedNotice(...)   # 실 데이터로 wrap
channel = DiscordChannel(webhook)
messages = channel._build_messages([item], [], datetime.now())  # 단건이라 항상 길이 1
ok = channel._post_all(messages)

flash("success.test_send_ok" if ok else "error.test_send_failed")
return redirect /settings
```

**설계 결정**:
- **영역 2 `service.send()` 비경유** — `notifications` 이력 INSERT 안 함. 테스트 발송이 실 통계 오염 0.
- **운영시간·`is_active` 무시** — 사용자가 *지금* 발송을 확인하려는 의도이므로 영역 1 의 조건들 모두 우회.
- **최신 1건만** — 본질은 "동작 확인". 다건 발송은 over-spec.
- **flash 카테고리 미사용** — 메시지 텍스트로 성공/실패 구분 (영역 2 결정 [1] 의 하드코딩 일관). `_base.html` 의 flash dict lookup 그대로.

---

## 4. 폼 입력·검증 사양

### 4.1 POST `/settings`

| 필드 | 타입 | 검증 | 실패 시 |
|---|---|---|---|
| `frequency_mode` | text 'high'\|'medium'\|'low'\|'custom' | `FREQUENCY_NAME_TO_ID` 키에 존재 | flash + redirect (DB 미변경) |
| `is_active` | 키 존재 여부 | 키 있음 → True, 없음 → False. 값 검사 안 함. | — |

### 4.2 POST `/settings/times/add`

다중 시각. `form.getlist('time')` 으로 0~29 개 수집.

검증 (`_validate_times`), **첫 실패에서 즉시 중단**:

| # | 규칙 | 에러 키 |
|---|---|---|
| 1 | 1개 이상 선택 | `error.no_time_selected` |
| 2 | 각 항목이 `r'\d{2}:\d{2}'` 패턴 | `error.invalid_time_format` |
| 3 | `10:00 ≤ t ≤ 17:00` | `error.time_out_of_range` |
| 4 | 분이 `{0, 15, 30, 45}` | `error.time_not_aligned` |
| 5 | `existing` 와 교집합 없음 (DB 의 기등록 시각) | `error.time_duplicated` |
| 6 | candidates 내부 중복 없음 (사용자가 같은 값 두 번 보낸 경우) | `error.time_duplicated` |
| 7 | _(TODO 13)_ 등록 후 인접 시각 간격 ≥ 5분 | `error.time_too_close` |

검증 통과 시 정렬된 리스트 반환.

검증은 **첫 번째 실패에서 즉시 중단**되므로 여러 종류 실패가 섞이면 첫 에러만 사용자에게 표시된다. 모든 실패를 한 번에 일괄 표시하는 UX 는 TODO.

`existing` 와 `candidates` 의 5분 인접 규칙 (행 7) — 1단계 그리드가 15분 단위이므로 자동 충족이라 구현체에는 미반영. 미래에 그리드가 더 촘촘해지면(TODO 13, JS 모달 UI) 행 7 검증을 활성화한다. 표에 남겨두는 이유 = 그리드 단위 변경 시 자동으로 떠올리게 하기 위함.

### 4.3 POST `/settings/times/delete`

| 필드 | 타입 | 검증 | 실패 시 |
|---|---|---|---|
| `id` | int | `int(...)` 변환 가능 | redirect (조용히 무시) |

---

## 5. 데이터 흐름 (정적)

```
[브라우저] ── GET /settings ─────────────────────────┐
                                                    ▼
                                routes.settings.index
                                          │
                                          ▼
                          repository.settings.load(uid)
                                          │
                                          ▼
                              Jinja2 index.html 렌더
                                          │
                                          ▼
                                       HTML 응답

[브라우저] ── POST /settings ────────────────────────┐
                                                    ▼
                                  routes.settings.save
                                          │
                                          ▼
                        _parse_frequency_mode / _parse_is_active
                                          │
                            ┌─────────────┴─────────────┐
                            │ 검증 실패                  │ 통과
                            ▼                           ▼
                       flash("error...")        repository.settings.update
                       redirect /settings        (Tx — 1 UPDATE)
                                                        │
                                                        ▼
                                                redirect /settings (PRG)

[브라우저] ── POST /settings/times/add ──────────────┐
                                                    ▼
                                routes.settings.times_add_save
                                          │
                                          ▼ Tx open
                              load → existing set
                              _validate_times(candidates, existing)
                                          │
                            ┌─────────────┴─────────────┐
                            │ 실패                       │ 통과
                            ▼                           ▼
                       flash(err)               add_custom_times (executemany)
                       Tx close (rollback)       │
                       redirect /settings/times/add  │
                                                 ▼ Tx commit
                                                redirect /settings
```

**영역 1 으로의 즉시성**: 변경 commit 직후, 영역 1 의 스케줄러는 다음 분의 `settings_repo.load()` 재조회에서 새 값을 읽음. 최대 지연 ≤ 60초.

---

## 6. 에러 처리 위치와 정책

| 발생 지점 | 정책 |
|---|---|
| `frequency_mode` 알 수 없는 값 | `_parse_frequency_mode → None` → flash `error.invalid_frequency_mode` + redirect `/settings`. DB 미변경. |
| `is_active` 키 자체 없음 | False 로 해석 (정상 흐름). 에러 아님. |
| 시각 검증 실패 (§4.2 의 6 규칙) | flash 에러 키 + redirect `/settings/times/add`. **전체 트랜잭션 rollback** ([5]). |
| 시각 INSERT 시 UNIQUE 위반 | `sqlite3.IntegrityError` catch → flash `error.time_conflict` + redirect. 단일 사용자라 실제 도달 ≈ 0%. |
| `times/delete` `id` 누락/형식 오류 | 조용히 redirect `/settings`. 사용자 메시지 없음. |
| 존재하지 않는 `id` 삭제 | `DELETE ... WHERE id=? AND user_id=?` 가 0행 매치 → 무오류. functional-spec 정책 그대로. |
| DB 예외 (UPDATE/INSERT/DELETE) | 1단계 명세 범위 외. Flask 기본 500 응답. |
| CSRF | 1단계 미적용 ([3]). POST 가 외부 도메인에서 와도 받음. |

**flash 메시지 본문**: 코드 안 상수 dict (영역 2 의 템플릿 하드코딩 결정 [1] 과 동일 원칙). `messages` 테이블 SELECT 하지 않음.

```python
ERROR_MESSAGES = {
    'error.invalid_frequency_mode': '주기 모드 값이 올바르지 않습니다.',
    'error.no_time_selected':       '시각을 1개 이상 선택해주세요.',
    'error.invalid_time_format':    '시각 형식이 올바르지 않습니다.',
    'error.time_out_of_range':      '운영시간(10:00~17:00) 내 시각만 등록할 수 있습니다.',
    'error.time_not_aligned':       '15분 단위로만 등록할 수 있습니다.',
    'error.time_duplicated':        '이미 등록된 시각이 포함되어 있습니다.',
    'error.time_conflict':          '시각 등록 중 충돌이 발생했습니다. 다시 시도해주세요.',
    'error.test_send_no_webhook':   'Discord 웹훅 URL 이 설정되어 있지 않습니다.',
    'error.test_send_no_notices':   '보낼 공지가 없습니다. 먼저 크롤링이 동작했는지 확인하세요.',
    'error.test_send_failed':       '발송 테스트 실패 — Discord 웹훅 응답 오류. 로그 확인 필요.',
    'success.test_send_ok':         '발송 테스트 성공 — Discord 채널을 확인해주세요.',
}
```

dict 이름은 `ERROR_MESSAGES` 유지 (surgical) 하지만 성공 메시지 키 (`success.*`) 도 같은 dict 에 포함. 1단계 minimal.

---

## 7. 영역 4가 다루는 DB 스키마 (발췌)

### 7.1 읽기

```sql
SELECT frequency_mode, is_active FROM user_settings WHERE user_id = :uid;
SELECT id, time_hhmm FROM user_custom_times
 WHERE user_id = :uid ORDER BY time_hhmm;
```

### 7.2 쓰기

```sql
UPDATE user_settings
   SET frequency_mode = :mode,
       is_active      = :active,
       updated_at     = datetime('now')
 WHERE user_id = :uid;

INSERT INTO user_custom_times (user_id, time_hhmm) VALUES (:uid, :t);
-- executemany 로 N행 묶음.

DELETE FROM user_custom_times WHERE id = :id AND user_id = :uid;
```

### 7.3 영역 4가 *건드리지 않는* 테이블

`attachments`, `messages`, `notifications`, `frequency_modes`, `notification_*`. — `frequency_modes` 의 `name` 컬럼도 영역 4 는 SELECT 하지 않고 코드 상수 `FREQUENCY_NAME_TO_ID` 만 사용.

**예외 (§3.6 테스트 발송 도입으로 추가)**:
- `users` — `discord_webhook_url` SELECT (테스트 발송용 채널 조회).
- `notices` + `categories` — `notices_repo.list_recent(limit=1)` 호출 (테스트 발송용 최신 공지 1건).
- 모두 *읽기 전용*. 쓰기는 여전히 0.

---

## 8. ERD / source-spec 동기화 액션 (본 구현 시작 전)

영역 4 는 **스키마 변경 없음**. 다만 source 문서 한 곳에 추가 작업이 필요:

### 8.1 `docs/source-spec/requirements.md` §14 (또는 §10 3단계 항목) 추가
```
- 영역 4 라우트 전체에 CSRF 토큰 검증 추가 (Flask-WTF 또는 직접 구현).
- SQLite WAL 모드 검토 (Flask 와 스케줄러를 별도 프로세스로 분리하는 시점).
```
근거: 1단계는 로컬 1인 + 단일 프로세스라 미적용. 3단계 공개 서비스 / 멀티프로세스 진입 시 필수.

### 8.2 본 구현 시 secret_key 외부화
- `KW_NOTICE_SECRET_KEY` 환경변수 우선, 미설정 시 `dev-secret-key` 하드코딩 + stderr 경고 (§2.1).
- `.env` 와 `requirements.txt` 의 `python-dotenv` 도입은 본 구현 시 결정.

### 8.3 `db-schema.txt` messages 테이블 Note 갱신
현재 Note 가 "UI 라벨 + 시스템 메시지 + 알림 템플릿 모두 포함" 인데, 영역 2 결정 [1] + 영역 4 §6 정책에 따라 다음으로 교체:
> `messages` = 사용자에게 표시되는 **도메인 콘텐츠** (UI 라벨·카테고리명) 전용.
> 알림 템플릿·flash 에러 등 **시스템 메시지** 는 코드 상수로 보유.

---

## 9. 영역 4 ↔ 영역 1 인터페이스 (단방향)

영역 4 와 영역 1 은 **함수 호출 인터페이스를 공유하지 않는다**. DB 테이블을 통한 비동기 인터페이스.

| 항목 | 영역 4 (쓰기) | 영역 1 (읽기) |
|---|---|---|
| `user_settings.frequency_mode` | UPDATE | 매 분 `load()` 재조회로 발동 시각 집합 재계산 |
| `user_settings.is_active` | UPDATE | 사이클 결과 알림 호출 여부 결정 |
| `user_custom_times` | INSERT / DELETE | `custom` 모드일 때 발동 시각 집합으로 사용 |

**동기화 지연**: SQLite 트랜잭션 commit 직후 다음 영역 1 분 단위 tick (≤ 60초) 에서 반영. 영역 4 가 영역 1 에 별도 신호 보내지 않음 (functional-spec §영역 1 ⑥의 "매 루프 1분마다 재조회" 원칙).

**동시성**: 1단계는 **단일 프로세스** 전제 (Flask 와 영역 1 스케줄러가 같은 Python 프로세스 안). 영역 4 의 트랜잭션과 영역 1 의 SELECT 는 같은 프로세스 안에서 순차 직렬화되므로 SQLite 락 경합 자체가 발생하지 않는다. 3단계에서 Flask·스케줄러를 별도 프로세스로 분리하면 WAL 모드 도입 필요 (TODO — `docs/source-spec/requirements.md` §14 추가 항목, §8.1 참조).

---

## 10. 검증 체크리스트

### 10.1 GET /settings
- [ ] DB `user_settings(2, 1)` 상태에서 GET → medium 라디오 checked, is_active 체크박스 checked.
- [ ] `frequency_mode=0` (custom) + custom_times 3건 상태 → 시각 목록 3행 + `[+ 시각 추가]` 버튼 표시.
- [ ] `frequency_mode != 0` 상태 → custom_times 영역 자체 미렌더.

### 10.2 POST /settings
- [ ] `frequency_mode=high` + `is_active=on` → DB 가 `(1, 1)` 로 UPDATE, redirect /settings, GET 시 high 라디오 checked.
- [ ] `is_active` 키 없는 폼 → DB 의 `is_active` 가 0 으로 UPDATE.
- [ ] `frequency_mode=invalid` → DB 미변경, flash 에러 메시지 표시.

### 10.3 POST /settings/times/add
- [ ] 1개 시각 (10:00) 선택 → INSERT 1행, redirect /settings.
- [ ] 3개 시각 (10:00, 13:00, 16:30) 선택 → INSERT 3행 (executemany), redirect /settings.
- [ ] 운영시간 밖 (09:45) 강제 폼 전송 → DB 미변경, flash `error.time_out_of_range`.
- [ ] 15분 미정렬 (10:07) 강제 폼 전송 → DB 미변경, flash `error.time_not_aligned`.
- [ ] 기존 등록 시각 (10:00) 다시 선택 → DB 미변경, flash `error.time_duplicated`.
- [ ] 2개 시각 (10:00, 10:00) 중복 전송 → DB 미변경, flash `error.time_duplicated`.
- [ ] 2개 시각 중 1개만 잘못 (10:00 정상 + 09:45 운영시간 밖) → **전체 거부**, DB 미변경 ([5]).

### 10.4 POST /settings/times/delete
- [ ] 존재하는 id 삭제 → DELETE 1행, redirect /settings.
- [ ] 존재하지 않는 id 삭제 → redirect /settings, 오류 메시지 없음.
- [ ] `id` 누락 폼 → redirect /settings, 오류 메시지 없음.

### 10.5 영역 1 연동
- [ ] frequency_mode 변경 후 60초 내 영역 1 의 `trigger_times` 가 새 모드로 재계산되어 다음 발동 시각이 바뀜.
- [ ] `is_active=0` 설정 후 사이클 발동 시 알림 호출 없음 (영역 1 §3 ⑥).

### 10.6 CSRF (의도된 부재)
- [ ] 외부 도메인에서 POST /settings 가 정상 처리됨 — 1단계 의도. 3단계 도입 시 이 항목 반전 필요.

### 10.7 POST /settings/test-send (§3.6)
- [ ] 유효 webhook + notices ≥ 1건 → Discord 메시지 실 도달 + flash `success.test_send_ok` + `notifications` 행 **무변화** (영역 2 service 비경유).
- [ ] webhook NULL → flash `error.test_send_no_webhook` + 발송 시도 없음.
- [ ] notices 0건 (이론) → flash `error.test_send_no_notices`. 1단계는 검증 데이터로 시뮬.
- [ ] 의도적 invalid URL → flash `error.test_send_failed`.
- [ ] 토요일·운영시간 밖 호출에도 정상 발송 (운영시간 우회 확인).
