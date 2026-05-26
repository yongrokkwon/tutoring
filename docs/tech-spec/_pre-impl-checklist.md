# 본 구현 시작 전 체크리스트

**작성일**: 2026-05-16
**용도**: 영역 1·2·4·3 명세서 v1.0 확정 후, 본 구현 (`reference/` 가 아닌 새 코드) 착수 전 일괄 처리할 액션 모음.
**사용법**: 위에서부터 순서대로 처리. 각 항목 완료 시 체크박스 표시. 출처 명세서·섹션 표기는 변경 의도 추적용.

---

## 1. ERD / DB 스키마 변경

`docs/source-spec/db-schema.txt` (DBDiagram DSL) 와 본 구현의 `schema.sql` / `seeds.sql` 에 동일하게 반영.

### 1.1 `notices` 테이블
- [ ] 컬럼 추가: `url TEXT NOT NULL` — 원문 URL.
  - 출처: `area-1-crawler.md` §10.1
  - 영향: 영역 1 §6.2 INSERT/UPDATE 에 `url` 포함, 영역 3 §4 SELECT 에 `n.url`.

### 1.2 `categories` 테이블 — source of truth 승격
- [ ] 컬럼 추가: `name TEXT NOT NULL UNIQUE`.
- [ ] 시드 변경: `(id)` 11행 → `(id, name)` 11행
  (0='일반', 1='학사', 2='학생', 3='봉사', 4='등록/장학', 5='입학',
   6='시설', 7='병무', 8='외부', 9='국제교류', 10='국제학생').
  - 출처: `area-1-crawler.md` §10.2

### 1.3 `messages` 테이블 시드 — 도메인 콘텐츠 전용으로 한정
- [ ] `ui.label.category.0` ~ `ui.label.category.10` (11행) **유지**.
- [ ] `ui.label.frequency.0` ~ `ui.label.frequency.3` (4행) **유지**.
- [ ] `notification.*` 로 시작하는 키 시드에서 **제거** (`notification.discord.header.new`, `.line.new`, `.footer`, `.line.modified` 등).
- [ ] `error.*` 시스템 메시지 시드는 **넣지 않음** — flash 에러는 코드 상수 (`area-4-settings.md` §6 `ERROR_MESSAGES`).
  - 출처: `area-2-notifier.md` §7.1, `area-4-settings.md` §6, `area-4-settings.md` §8.3
- [ ] `db-schema.txt` 의 `messages` 테이블 Note 갱신:
  > `messages` = 사용자에게 표시되는 **도메인 콘텐츠** (UI 라벨·카테고리명) 전용.
  > 알림 템플릿·flash 에러 등 **시스템 메시지** 는 코드 상수로 보유.
  - 출처: `area-4-settings.md` §8.3

### 1.4 `notification_*` 매핑 테이블 + 코드 상수 — 시드 유지 + ID 정합성 검증
- [ ] DB 시드 변경 없음. ID 는 코드 상수로 보유. `db-schema.txt` 시드 와 다음 코드 상수의 ID 값 **일치** 확인:
  - `notifier/discord.py`: `CHANNEL_DISCORD = 1`
  - `repository/notifications.py`: `TYPE_NEW=1`, `TYPE_MODIFIED=2`, `STATUS_SUCCESS=1`, `STATUS_FAILED=2`
  - `web/routes/settings.py`: `FREQUENCY_NAME_TO_ID = {'custom':0, 'high':1, 'medium':2, 'low':3}`
- [ ] 검증 방법: **(b) 주석 채택** — 각 상수 정의 위치에 다음 형식 주석:
  ```python
  # seeds.sql 의 (table, id) 와 동기 필요
  ```
  근거: 1단계는 테스트 프레임워크 미도입 (`docs/source-spec/requirements.md` §11 미정). 주석은 비용 0, 1단계 검증력 충분. 단위 테스트는 TODO 21.
  - 출처: `area-2-notifier.md` §7.2, §2.5, `area-4-settings.md` §2.2, 사용자 결정

### 1.5 [추가 B] 영역 1 §10 정합성 — **검증 완료**
다음 3개 결정이 영역 1 명세서에 실제로 박혀있는지 본 checklist 작성 시점에 검증:
- [x] `notices.url NOT NULL` 추가 — area-1 §10.1 (라인 388-390) 박힘.
- [x] `categories` source of truth + `messages` 의 카테고리 라벨 키 UI 전용 — area-1 §10.2 (라인 392-398) 박힘.
- [x] parser 가 `conn` 받지 않음 (`category_id=None`, classifier 가 매핑) — area-1 §2.4 (라인 97) + 데이터 흐름 (라인 181) 박힘.

→ 영역 1 명세서 v1.1 보강 불필요.

---

## 2. source-spec 갱신

### 2.1 `docs/source-spec/functional-spec.md`
- [x] §영역 2 ① 양식의 수정 공지 라인 `(작성일) → (수정일)` — **사용자 처리 완료** (2026-05-16).
- [ ] §영역 3 처리흐름 ① 정렬 기준 갱신:
  현재:
  > 정렬: 1차 작성일 DESC, 2차 DUID DESC
  교체:
  > 정렬: 1차 `is_pinned` DESC, 2차 `MAX(posted_date, modified_date)` DESC, 3차 `updated_at` DESC, 4차 DUID DESC.
  > `MAX` 는 SQLite 의 스칼라 함수 (2 인자, 집계 아님).
  - 출처: `area-3-viewer.md` §11.1

### 2.2 `docs/source-spec/requirements.md`
- [ ] §14 (또는 §10 3단계 항목) 추가:
  ```
  - 영역 4 라우트 전체에 CSRF 토큰 검증 추가 (Flask-WTF 또는 직접 구현).
  - SQLite WAL 모드 검토 (Flask 와 스케줄러를 별도 프로세스로 분리하는 시점).
  ```
  - 출처: `area-4-settings.md` §8.1

### 2.3 `docs/source-spec/db-schema.txt` 위치 확인
- [ ] `~/Downloads/db-schema.txt` 가 `docs/source-spec/db-schema.txt` 로 이동되었는지 확인.
  - 출처: 사용자 통지 (영역 3 결정 [7]). 미완 시 이동 후 §1.1~§1.3 의 DBDiagram 변경 적용.

### 2.4 `docs/source-spec/db-schema.txt` `notices` 테이블 정렬 Note 갱신
- [ ] 현재 Note:
  > 정렬은 코드 레벨: `ORDER BY max(posted_date, modified_date) DESC, updated_at DESC, duid DESC`
  → 영역 3 §4 와 어긋남 (`is_pinned DESC` 1차 키 누락).
- [ ] 교체:
  > 정렬은 코드 레벨:
  > `ORDER BY is_pinned DESC, MAX(posted_date, modified_date) DESC, updated_at DESC, duid DESC`
  > `MAX` 는 SQLite 의 스칼라 함수 (2 인자).
  - 출처: `area-3-viewer.md` §4, §11.1

---

## 3. 명세서 간 cross-reference

### 3.1 `area-4-settings.md` §1 (또는 §2) 에 nav cross-ref 한 줄 추가
- [ ] 다음 문장 추가:
  > nav 마크업 (메뉴 active 표시 로직 포함) 은 `area-3-viewer.md` §10.3 에서 최종 확정.
  - 출처: `area-3-viewer.md` §10.3, 영역 3 검토 결정 [2]

### 3.2 inline 경로 통일 (선택 — 미실행)
영역 1·2 명세서 본문 안 `functional-spec §...`·`requirements §...` inline 참조는 v1.0 헤더 통일 시 surgical 원칙으로 미수정. 본 구현 시 코드 주석·README 작성 시 일관되게 `docs/source-spec/` 경로 사용. 명세서 본문 갱신은 *불필요*.

---

## 4. 환경 설정

### 4.1 `KW_NOTICE_SECRET_KEY` 환경변수 처리
- [ ] `web/__init__.py` `create_app()` 에 다음 로직 포함:
  ```python
  secret = os.environ.get("KW_NOTICE_SECRET_KEY")
  if not secret:
      print("WARNING: KW_NOTICE_SECRET_KEY not set, using dev fallback",
            file=sys.stderr)
      secret = "dev-secret-key"
  app.secret_key = secret
  ```
  - 출처: `area-4-settings.md` §2.1, §8.2

### 4.2 `.env` / `python-dotenv` — 도입 결정 완료 (**도입함**)
- [x] 도입 채택 — 사용자 결정.
- [ ] `requirements.txt` 에 `python-dotenv>=1.0,<2.0` 추가.
- [ ] `.gitignore` 에 `.env` 추가 (기존 reference/.gitignore 에는 이미 있음 — 본 구현 시 동일 적용).
- [ ] `.env.example` 신규 생성 (커밋 대상). 초기 내용:
  ```
  KW_NOTICE_SECRET_KEY=
  ```
- [ ] `kw_notice/__init__.py` **또는** `web/__init__.py` 최상단에서 `from dotenv import load_dotenv; load_dotenv()` 호출.
  - 출처: `area-4-settings.md` §8.2, 본 checklist 사용자 결정

### 4.3 venv + requirements.txt
- [ ] `requirements.txt` 최종 작성 (모든 의존성에 **메이저 버전 상한** 핀):
  ```
  requests>=2.31,<3.0
  beautifulsoup4>=4.12,<5.0
  Flask>=3.0,<4.0
  python-dotenv>=1.0,<2.0
  ```
  - 근거: 1단계 안정성. 메이저 버전 jump 가 학습 중에 들어오는 사고 방지.
  - 출처: `docs/source-spec/requirements.md` §11-1, `reference/requirements.txt`

---

## 5. 기타 미해결

### 5.1 영역 4 nav 마크업 위치 확정
- [x] 위 §3.1 와 동일 — `_base.html` 작성 시 `area-3-viewer.md` §10.3 의 Jinja 스니펫 그대로 사용. **슬라이스 4 검증 §12.5 에서 적용 확인 완료.**

### 5.2 USER_AGENT ASCII 제약
- [x] `config.USER_AGENT` 는 ASCII 만 (HTTP 헤더 latin-1 제약). 슬라이스 1 §⑧ 확인.
- [x] User-Agent 에 연락처 (이메일) 포함 — `contact: oyo260325@gmail.com`.

### 5.3 1단계 단일 프로세스 전제 — 진입점 방식 결정 완료 (**단일 진입점**)
- [x] 결정: `main.py run` 단일 진입점. 사용자 결정.
- [x] 구현 방식 적용:
  - 스케줄러: `threading.Thread(target=scheduler.run_forever, daemon=True).start()` — 백그라운드.
  - 메인 스레드: `app.run(host="127.0.0.1", port=5002, debug=False)`. (포트는 환경에 따라 5000→5001→5002 로 회피 — macOS AirPlay 충돌.)
  - SQLite 기본 격리로 충분 — `db.transaction()` 이 매 호출마다 새 connection.
  - 라이브 동작: 슬라이스 3 검증에서 `GET /`·`/settings`·`/notices` 200/302 확인.
- [ ] 별도 프로세스 + WAL 분리는 3단계 (TODO 18, §6 참조).
  - 출처: `area-4-settings.md` §9, `area-4-settings.md` §8.1, 사용자 결정

### 5.4 검증 — 본 구현 후 영역별 §10·§11·§12 체크리스트 일괄 실행
- [x] 영역 1 §7 검증 체크리스트 (8 항목) → 11/11 sub-check 통과 (trigger 4 케이스 분리)
- [x] 영역 2 §9 검증 체크리스트 (7 항목) → 7/7 통과
- [x] 영역 4 §10 검증 체크리스트 (4 그룹, 15 항목) → 18/18 sub-check 통과
- [x] 영역 3 §12 검증 체크리스트 (6 그룹, 13 항목) → 18/18 sub-check 통과

**총 54/54 통과** (2026-05-16 일괄 실행 결과). 슬라이스 단위 독립 구현이 통합 후 회귀 없이 동작 확인.
  - 출처: 각 명세서

---

## 6. TODO 처리 (본 구현 *후* — 1.5단계·3단계로 미룬 것)

본 checklist 가 *처리* 항목이 아니라 *향후 작업 위치* 를 추적하기 위한 목록.

| TODO 번호 | 내용 | 처리 단계 | 출처 |
|---|---|---|---|
| 1 | 재시도 가치 있는 에러 (5xx, 타임아웃) 한정 + 지수 백오프 — 영역 1·2 양쪽 HTTP 재시도에 일괄 적용 | 1단계 후 | `area-1` §8, `area-2` §5, requirements §14-1 |
| 2 | 크롤링 연속 N회 실패 시 Discord 운영자 알림 | 1단계 후 | `area-1` §8, requirements §14-2 |
| 3 | 첫 실행 정책에 수정일 기준 추가 | 1단계 후 | `area-1` §8, requirements §14-3 |
| 4 | 발송 실패 케이스 다음 사이클 자동 재시도 | 1단계 후 | `area-2` §5, requirements §14-4 |
| 5 | 메시지 길이 초과 시 자동 분할 | 1단계 후 | `area-2` §3.3, requirements §14-5 |
| 6 | 발송 시각 푸터 한국어 친화 형식 | 1단계 후 | requirements §14-6 |
| 7 | 공지 상세 화면 + `NoticeDetail` dataclass 도입 | 1단계 후 | `area-3` §2.2 메모, requirements §14-7 |
| 8 | 알림 발송 이력 화면 | 1단계 후 | requirements §14-8 |
| 9 | 페이지네이션 (100건 초과) | 1단계 후 | requirements §14-9 |
| 10 | 카테고리 필터링 UI + 필터 0건 안내 | 1단계 후 | `area-3` §6 빈 상태 메모, requirements §14-10 |
| 11 | 제목 검색 + 검색 0건 안내 | 1단계 후 | requirements §14-11 |
| 12 | Bootstrap / Tailwind 도입 | 1단계 후 | requirements §14-12 |
| 13 | JS 모달 시각 추가 UI + 5분 인접 검증 활성화 | 1단계 후 | `area-4` §4.2 행 7 메모, requirements §14-13 |
| 14 | 크롤링까지 멈추는 별도 플래그 | 1단계 후 | requirements §14-14 |
| 15 | 일괄 실패 표시 UX (`_validate_times` 다중 실패) | 1단계 후 | `area-4` §4.2 |
| 16 | 카카오 알림톡 채널 + `NotificationItem` 분리 검토 | 1.5단계 | `area-2` §7.3, requirements §10 |
| 17 | CSRF 보호 (Flask-WTF) | 3단계 | `area-4` §8.1, 위 §2.2 |
| 18 | SQLite WAL 모드 / 멀티프로세스 분리 | 3단계 | `area-4` §9, 위 §2.2 |
| 19 | read-only DB 컨텍스트 헬퍼 (`db.read_only()`) | 1단계 후 | `area-3` §3.2 |
| 20 | `notifications.status = skipped` 별도 상태 | 1.5단계 | `area-2` §5 빈 webhook TODO |
| 21 | ID 정합성 단위 테스트 + 테스트 프레임워크 (pytest 등) 도입 | 1단계 후 | 본 checklist §1.4 |
| 22 | HTTP 성공 + DB INSERT 실패 케이스 보상 (outbox / 보상 트랜잭션) | 3단계 | `area-2` §4 |

---

## 7. 본 checklist 의 종료 조건

**§1·§2·§3·§4 의 모든 체크박스 + §5.3 진입점 방식 결정 완료** 시 본 구현 착수 가능.
§5.3 외 §5 항목은 본 구현 *작업 항목* (실행 가이드), §6 은 본 구현 *후* 의 추적 목록.

---

## 8. 본 구현 시작 시 작업 순서 (슬라이스)

본 checklist §7 종료 조건 충족 후, 다음 순서로 진행:

| # | 작업 | 멈춤 지점 |
|---|---|---|
| 1 | 본 checklist §1·§2·§3·§4 처리 (DB·source-spec·cross-ref·환경) | §7 종료 조건 충족 확인 후 진행 |
| 2 | `requirements.txt` + `.env.example` + `.gitignore` 작성 | — |
| 3 | `schema.sql` + `seeds.sql` 정리 (영역 1 §10 결정 반영본) | — |
| 4 | **슬라이스 1**: 영역 1 (공지 수집) 구현. `main.py run` 의 스케줄러 스레드. | 슬라이스 1 검증 체크리스트 (area-1 §7) 확인 요청 |
| 5 | **슬라이스 2**: 영역 2 (알림 발송) 구현. | 슬라이스 2 검증 체크리스트 (area-2 §9) 확인 요청 |
| 6 | **슬라이스 3**: 영역 4 (설정 관리) 구현. Flask 앱 등장. | 슬라이스 3 검증 체크리스트 (area-4 §10) 확인 요청 |
| 7 | **슬라이스 4**: 영역 3 (공지 조회) 구현. | 슬라이스 4 검증 체크리스트 (area-3 §12) 확인 요청 |
| 8 | 본 checklist §5 본 구현 작업 항목 (USER_AGENT, 단일 프로세스 진입점 등) 마무리 | — |
| 9 | §5.4 전 영역 검증 체크리스트 일괄 재실행 | 본 구현 완료 보고 |

**원칙**: 각 슬라이스 끝나면 멈추고 검증 체크리스트 확인 요청. 다음 슬라이스 자동 진행 금지.
