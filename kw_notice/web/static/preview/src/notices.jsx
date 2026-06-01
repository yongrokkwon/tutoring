/* Area 3 — /preview/ 공지 페이지. 데이터는 window.__PRELOAD__.notices 에서. */

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
  const wasEdited = n.modified_date > n.posted_date;
  return (
    <tr>
      <td style={{ ...td, width: 110, paddingRight: 0 }}>
        <CatPill cat={n.category_name} />
      </td>
      <td style={{ ...td, paddingRight: 16 }}>
        <span style={{ display: "inline-flex", alignItems: "center", flexWrap: "wrap" }}>
          {pinned && (
            <span style={{ marginRight: 6, fontSize: 14, lineHeight: 1 }} aria-label="고정">📌</span>
          )}
          <a href={n.url}
             target="_blank"
             rel="noopener"
             style={{
               color: "var(--ink)",
               textDecoration: "none",
               fontSize: 16,
               letterSpacing: "-0.374px",
               fontWeight: pinned ? 500 : 400,
             }}>{n.title}</a>
          {n.has_attachment && <span style={{ marginLeft: 8, fontSize: 12 }} aria-label="첨부">📎</span>}
          {wasEdited && <span style={{ marginLeft: 6, fontSize: 12 }} aria-label="수정됨">✏️</span>}
        </span>
      </td>
      <td style={{ ...td, color: "var(--ink-80)", fontSize: 14, whiteSpace: "nowrap" }}>{n.author}</td>
      <td style={{ ...td, color: "var(--ink-48)", fontSize: 13, fontVariantNumeric: "tabular-nums", whiteSpace: "nowrap" }}>
        {wasEdited ? (
          <>
            <div>{n.posted_date}</div>
            <div>↳ {n.modified_date}</div>
          </>
        ) : (
          <div>{n.posted_date}</div>
        )}
      </td>
      <td style={{ ...td, textAlign: "right" }}>
        <a href={n.url}
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

function buildCategories(all) {
  const counts = new Map();
  all.forEach(n => counts.set(n.category_name, (counts.get(n.category_name) || 0) + 1));
  const rest = [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([name, count]) => ({ name, count }));
  return [{ name: "전체", count: all.length }, ...rest];
}

function NoticesApp() {
  const all = window.__PRELOAD__.notices;
  const lastFetched = window.__PRELOAD__.last_fetched_at;
  const [activeCat, setActiveCat] = React.useState("전체");
  const categories = React.useMemo(() => buildCategories(all), [all]);

  const filtered = (rows) =>
    activeCat === "전체" ? rows : rows.filter(r => r.category_name === activeCat);

  const pinnedAll = all.filter(n => n.is_pinned);
  const regularAll = all.filter(n => !n.is_pinned);
  const pinnedRows = filtered(pinnedAll);
  const regularRows = filtered(regularAll);
  const total = all.length;

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
          {lastFetched && (
            <span className="ap-caption" style={{ color: "var(--ink-48)" }}>마지막 수집 · {lastFetched}</span>
          )}
        </header>

        {/* Category filter chips */}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 32 }}>
          {categories.map(c => {
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
