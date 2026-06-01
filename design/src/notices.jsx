/* Area 3 — /notices page */

const PINNED_NOTICES = [
  { duid: 52580, cat: "등록/장학", title: "2026학년도 2학기 국가장학금 1차 신청 안내",                                                  author: "학생복지팀",                 posted: "2026-05-19", modified: "2026-05-19", att: false },
  { duid: 52578, cat: "일반",      title: "정보시스템 서비스 일시 중단 안내",                                                              author: "정보운영팀",                 posted: "2026-05-19", modified: "2026-05-19", att: false },
  { duid: 52577, cat: "일반",      title: "[지능형로봇혁신융합대학사업단] 2026 제어로봇시스템 학술대회(ICROS 2026) 학부생 참가 지원",      author: "지능형로봇혁신공유대학사업단", posted: "2026-05-19", modified: "2026-05-19", att: false },
  { duid: 52576, cat: "학생",      title: "[대학혁신지원사업] 2026 광운대학교 대학원 오픈랩 행사 안내",                                    author: "대학원 교학팀",              posted: "2026-05-19", modified: "2026-05-19", att: false },
  { duid: 52528, cat: "학사",      title: "2026년도 1학기 국제학생증 ISIC발급 지원행사 안내",                                              author: "교육지원팀",                 posted: "2026-05-15", modified: "2026-05-19", att: true },
  { duid: 52525, cat: "일반",      title: "[지능형로봇사업단] 2026 제5회 CO-WEEK 아카데미 수강 신청 안내 (추가모집 ~5.27. 수)",            author: "지능형로봇혁신공유대학사업단", posted: "2026-05-13", modified: "2026-05-19", att: true },
  { duid: 52522, cat: "일반",      title: "[광운대학교 산학협력단] 2026 하계 노원 대학 연합 창업캠프 (모집 마감)",                          author: "산학협력단",                 posted: "2026-05-13", modified: "2026-05-19", att: true },
  { duid: 52520, cat: "일반",      title: "[공학교육혁신센터] 2026학년도 자율주행로봇전문가과정 교육 참가자 모집 안내",                    author: "공학교육혁신센터",           posted: "2026-05-07", modified: "2026-05-19", att: true },
  { duid: 52518, cat: "일반",      title: "[공학교육혁신센터] ★ 2026 MY(Multi-Y)캠퍼스디자인 프로그램 참가자 모집 안내 (~5월 22일까지)",   author: "공학교육혁신센터",           posted: "2026-04-13", modified: "2026-05-19", att: true },
];

const REGULAR_NOTICES = [
  { duid: 10172, cat: "일반",      title: "[현장실습]「2026학년도 하계학기 단기 현장실습」참여 안내",                                       author: "현장실습지원팀",             posted: "2026-05-18", modified: "2026-05-18", att: false },
  { duid: 10171, cat: "일반",      title: "2026 자율전공학부 전공박람회「나의 전공 항로를 개척하라!」개최 안내",                            author: "인제니움대학",               posted: "2026-05-18", modified: "2026-05-18", att: false },
  { duid: 10170, cat: "일반",      title: "2026 하계방학 SAP ERP MM 집중 실무특강 참가자 모집",                                              author: "경영대학",                   posted: "2026-05-18", modified: "2026-05-18", att: false },
  { duid: 10169, cat: "등록/장학", title: "2026학년도 1학기 국가장학금 지급 (예정) 안내 (3차)",                                              author: "학생복지팀",                 posted: "2026-05-18", modified: "2026-05-18", att: false },
  { duid: 10168, cat: "등록/장학", title: "2026년 1학기 거창군 지역출신 대학생 등록금 지원 사업 안내",                                       author: "학생복지팀",                 posted: "2026-05-18", modified: "2026-05-18", att: false },
  { duid: 10167, cat: "국제학생",  title: "한양이엔지(주) 해외 운영지원 채용 안내",                                                          author: "국제교류팀",                 posted: "2026-05-18", modified: "2026-05-18", att: false },
  { duid: 10166, cat: "일반",      title: "행정조교 채용 공고 (교무처 교육지원팀)",                                                          author: "교육지원팀",                 posted: "2026-05-12", modified: "2026-05-18", att: true },
  { duid: 10165, cat: "학생",      title: "[재학생 법정의무교육] 2026 폭력예방교육 수강 안내 (모든 재학생 필수 이수 항목)",                  author: "학생상담센터",               posted: "2026-05-04", modified: "2026-05-18", att: true },
  { duid: 10164, cat: "일반",      title: "(안내사항 수정) [HUSS-글로벌공생] 2026 HUSS 융합캠프(인사이트) AI 경진대회 참가팀 모집 안내",     author: "인문사회융합인재양성사업단",   posted: "2026-05-04", modified: "2026-05-18", att: true },
  { duid: 10163, cat: "일반",      title: "「2026 하나 소셜벤처 유니버시티 5기」 창업 교육 참가자 모집",                                     author: "산학협력단",                 posted: "2026-04-29", modified: "2026-05-18", att: true },
  { duid: 10162, cat: "학사",      title: "2026학년도 하계계절학기 타대학 학점교류 안내 (본교 → 타교)",                                      author: "교육지원팀",                 posted: "2026-04-28", modified: "2026-05-18", att: true },
  { duid: 10161, cat: "등록/장학", title: "2026학년도 1학기 화도 및 동해장학금 2차 신청 안내",                                                author: "학생복지팀",                 posted: "2026-04-24", modified: "2026-05-18", att: false },
];

const CATEGORIES = [
  { name: "전체",      count: 286 },
  { name: "일반",      count: 142 },
  { name: "학사",      count:  38 },
  { name: "학생",      count:  24 },
  { name: "등록/장학", count:  29 },
  { name: "국제학생",  count:  18 },
  { name: "국제교류",  count:  14 },
  { name: "봉사",      count:   9 },
  { name: "외부",      count:  12 },
];

function CatPill({ cat }) {
  return (
    <span style={{
      display: "inline-block",
      padding: "3px 10px",
      borderRadius: 6,
      background: "var(--parchment)",
      color: "var(--ink-80)",
      fontFamily: "var(--font-body)",
      fontSize: 12,
      fontWeight: 500,
      whiteSpace: "nowrap",
      letterSpacing: "-0.1px",
    }}>{cat}</span>
  );
}

const td = {
  padding: "14px 18px",
  borderBottom: "1px solid var(--divider-soft)",
  verticalAlign: "middle",
  fontFamily: "var(--font-body)",
  fontSize: 16,
  letterSpacing: "-0.374px",
};

function NoticeRow({ n, pinned }) {
  const wasEdited = n.modified > n.posted;
  return (
    <tr>
      <td style={{ ...td, width: 110, paddingRight: 0 }}>
        <CatPill cat={n.cat} />
      </td>
      <td style={{ ...td, paddingRight: 16 }}>
        <span style={{ display: "inline-flex", alignItems: "center", flexWrap: "wrap" }}>
          {pinned && (
            <span style={{ marginRight: 6, fontSize: 14, lineHeight: 1 }} aria-label="고정">📌</span>
          )}
          <a href={`https://www.kw.ac.kr/ko/life/notice.jsp?BoardMode=view&DUID=${n.duid}`}
             target="_blank"
             rel="noopener"
             style={{
               color: "var(--ink)",
               textDecoration: "none",
               fontSize: 16,
               letterSpacing: "-0.374px",
               fontWeight: pinned ? 500 : 400,
             }}>{n.title}</a>
          {n.att && <span style={{ marginLeft: 8, fontSize: 12 }} aria-label="첨부">📎</span>}
          {wasEdited && <span style={{ marginLeft: 6, fontSize: 12 }} aria-label="수정됨">✏️</span>}
        </span>
      </td>
      <td style={{ ...td, color: "var(--ink-80)", fontSize: 14, whiteSpace: "nowrap" }}>{n.author}</td>
      <td style={{ ...td, color: "var(--ink-48)", fontSize: 13, fontVariantNumeric: "tabular-nums", whiteSpace: "nowrap" }}>
        {wasEdited ? (
          <>
            <div>{n.posted}</div>
            <div>↳ {n.modified}</div>
          </>
        ) : (
          <div>{n.posted}</div>
        )}
      </td>
      <td style={{ ...td, textAlign: "right" }}>
        <a href={`https://www.kw.ac.kr/ko/life/notice.jsp?BoardMode=view&DUID=${n.duid}`}
           className="ap-link"
           target="_blank"
           rel="noopener"
           style={{ fontSize: 14 }}>원문 ↗</a>
      </td>
    </tr>
  );
}

function NoticeTable({ rows, pinned }) {
  return (
    <div className="ap-card">
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <colgroup>
          <col style={{ width: 110 }} />
          <col />
          <col style={{ width: 180 }} />
          <col style={{ width: 130 }} />
          <col style={{ width: 90 }} />
        </colgroup>
        <tbody>
          {rows.map(n => <NoticeRow key={n.duid} n={n} pinned={pinned} />)}
        </tbody>
      </table>
    </div>
  );
}

function NoticesApp() {
  const [activeCat, setActiveCat] = React.useState("전체");
  const [now] = React.useState(() => {
    const d = new Date();
    return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  });

  const filtered = (rows) =>
    activeCat === "전체" ? rows : rows.filter(r => r.cat === activeCat);

  const pinnedRows = filtered(PINNED_NOTICES);
  const regularRows = filtered(REGULAR_NOTICES);
  const total = PINNED_NOTICES.length + REGULAR_NOTICES.length;

  return (
    <PageShell category="공지" activeTab="notices">
      <div className="ap-page-inner">

        {/* Header */}
        <header style={{ display: "flex", alignItems: "flex-end", marginBottom: 28, gap: 16, flexWrap: "wrap" }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="ap-fine" style={{
              color: "var(--ink-48)",
              letterSpacing: "0.5px",
              textTransform: "uppercase",
              marginBottom: 10,
              fontWeight: 600,
            }}>
              광운대학교 · 공지사항
            </div>
            <h1 className="ap-display-lg" style={{ margin: "0 0 10px" }}>공지</h1>
            <p className="ap-lead" style={{ margin: 0, color: "var(--ink-80)" }}>
              광운대 공지 페이지에서 자동 수집된 {total.toLocaleString()}건
            </p>
          </div>
          <span className="ap-caption" style={{ color: "var(--ink-48)" }}>마지막 수집 · {now}</span>
        </header>

        {/* Category filter chips */}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 32 }}>
          {CATEGORIES.map(c => {
            const isActive = activeCat === c.name;
            return (
              <button
                key={c.name}
                onClick={() => setActiveCat(c.name)}
                style={{
                  background: isActive ? "var(--ink)" : "#fff",
                  color: isActive ? "#fff" : "var(--ink-80)",
                  border: `1px solid ${isActive ? "var(--ink)" : "var(--hairline)"}`,
                  borderRadius: 999,
                  padding: "8px 16px",
                  fontFamily: "var(--font-body)",
                  fontSize: 14,
                  fontWeight: isActive ? 600 : 400,
                  letterSpacing: "-0.224px",
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 8,
                  transition: "all 120ms ease",
                }}>
                {c.name}
                <span style={{
                  fontSize: 11,
                  fontVariantNumeric: "tabular-nums",
                  color: isActive ? "rgba(255,255,255,0.6)" : "var(--ink-48)",
                }}>{c.count}</span>
              </button>
            );
          })}
        </div>

        {/* PINNED */}
        {pinnedRows.length > 0 && (
          <section style={{ marginBottom: 32 }}>
            <div style={{ display: "flex", alignItems: "baseline", marginBottom: 14, padding: "0 4px" }}>
              <h2 className="ap-tagline" style={{ margin: 0, display: "inline-flex", alignItems: "center", gap: 8 }}>
                <span>📌</span>
                고정 공지
              </h2>
              <span className="ap-caption" style={{ marginLeft: 10, color: "var(--ink-48)" }}>
                {pinnedRows.length}건 · 페이지 상단 항상 표시
              </span>
            </div>
            <NoticeTable rows={pinnedRows} pinned />
          </section>
        )}

        {/* REGULAR */}
        {regularRows.length > 0 ? (
          <section>
            <div style={{ display: "flex", alignItems: "baseline", marginBottom: 14, padding: "0 4px", gap: 10, flexWrap: "wrap" }}>
              <h2 className="ap-tagline" style={{ margin: 0 }}>최근 공지</h2>
              <span className="ap-caption" style={{ color: "var(--ink-48)" }}>
                최근 활동 순 · {regularRows.length}건
              </span>
              <span style={{ flex: 1 }} />
              <span className="ap-caption" style={{ color: "var(--ink-48)" }}>
                정렬: MAX(작성, 수정) ↓
              </span>
            </div>
            <NoticeTable rows={regularRows} />
          </section>
        ) : pinnedRows.length === 0 && (
          <EmptyState />
        )}

        {/* Footer legend */}
        <div style={{
          display: "flex", alignItems: "center", gap: 20,
          marginTop: 28, padding: "0 4px",
          color: "var(--ink-48)",
          flexWrap: "wrap",
        }} className="ap-caption">
          <span>📌 고정</span>
          <span>📎 첨부 있음</span>
          <span>✏️ 수정됨</span>
          <span>↳ 수정일</span>
          <span style={{ flex: 1 }} />
          <span>정렬: 고정 ↓ · MAX(작성, 수정) ↓ · 수정시각 ↓ · DUID ↓</span>
        </div>
      </div>
    </PageShell>
  );
}

function EmptyState() {
  return (
    <div style={{
      background: "#fff",
      border: "1px solid var(--hairline)",
      borderRadius: 18,
      padding: 64,
      textAlign: "center",
    }}>
      <div style={{
        width: 80, height: 80, borderRadius: "50%",
        background: "var(--parchment)",
        display: "inline-flex", alignItems: "center", justifyContent: "center",
        marginBottom: 20, fontSize: 32,
      }}>📭</div>
      <div className="ap-display-md" style={{ marginBottom: 8 }}>공지가 없습니다</div>
      <p className="ap-body" style={{ color: "var(--ink-80)", margin: 0 }}>
        선택한 카테고리에 해당하는 공지가 없습니다.
      </p>
    </div>
  );
}

Object.assign(window, { NoticesApp });
