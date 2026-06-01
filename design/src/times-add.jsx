/* Area 4 — /settings/times/add page (interactive grid) */

const REGISTERED_TIMES = new Set(["10:00", "12:00", "15:15", "16:15"]);

function buildGrid() {
  const grid = [];
  for (let h = 10; h <= 17; h++) {
    for (let m = 0; m < 60; m += 15) {
      if (h === 17 && m > 0) break;
      grid.push(`${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`);
    }
  }
  return grid;
}

function TimesAddApp() {
  const grid = React.useMemo(buildGrid, []);
  const [selected, setSelected] = React.useState(new Set());

  const toggle = (t) => {
    if (REGISTERED_TIMES.has(t)) return;
    setSelected(s => {
      const next = new Set(s);
      if (next.has(t)) next.delete(t);
      else next.add(t);
      return next;
    });
  };

  return (
    <PageShell category="설정" activeTab="settings">
      <div className="ap-page-inner--narrow">

        {/* Header */}
        <header style={{ marginBottom: 36 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
            <a href="./settings.html" className="ap-link" style={{ fontSize: 14 }}>← 설정으로</a>
          </div>
          <div className="ap-fine" style={{
            color: "var(--ink-48)",
            letterSpacing: "0.5px",
            textTransform: "uppercase",
            marginBottom: 10,
            fontWeight: 600,
          }}>
            설정 / 사용자 지정 시각
          </div>
          <h1 className="ap-display-lg" style={{ margin: "0 0 12px" }}>시각 추가</h1>
          <p className="ap-lead" style={{ margin: 0, color: "var(--ink-80)" }}>
            추가할 시각을 골라주세요. 15분 단위, 운영시간 내 29칸 중 선택할 수 있습니다.
          </p>
        </header>

        {/* Grid */}
        <div className="ap-card" style={{ padding: 28 }}>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(7, 1fr)",
            gap: 10,
          }}>
            {grid.map(t => {
              const isReg = REGISTERED_TIMES.has(t);
              const isSel = selected.has(t);
              return (
                <button
                  key={t}
                  onClick={() => toggle(t)}
                  disabled={isReg}
                  style={{
                    position: "relative",
                    padding: "16px 8px",
                    borderRadius: 12,
                    textAlign: "center",
                    cursor: isReg ? "not-allowed" : "pointer",
                    background: isSel ? "var(--action-blue)" : isReg ? "var(--parchment)" : "#fff",
                    color: isSel ? "#fff" : isReg ? "var(--ink-48)" : "var(--ink)",
                    border: `1px solid ${isSel ? "var(--action-blue)" : "var(--hairline)"}`,
                    fontFamily: "var(--font-body)",
                    fontSize: 16,
                    fontVariantNumeric: "tabular-nums",
                    fontWeight: isSel ? 600 : 500,
                    letterSpacing: "-0.374px",
                    transition: "all 120ms ease",
                  }}>
                  <div>{t}</div>
                  {isReg && (
                    <div className="ap-fine" style={{ color: "var(--ink-48)", marginTop: 3 }}>등록됨</div>
                  )}
                </button>
              );
            })}
          </div>

          <div style={{
            display: "flex", alignItems: "center", gap: 24,
            marginTop: 24,
            paddingTop: 20,
            borderTop: "1px solid var(--divider-soft)",
            color: "var(--ink-48)",
            flexWrap: "wrap",
          }} className="ap-caption">
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ display: "inline-block", width: 14, height: 14, borderRadius: 4, background: "var(--action-blue)" }} />
              선택됨
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ display: "inline-block", width: 14, height: 14, borderRadius: 4, background: "var(--parchment)", border: "1px solid var(--hairline)" }} />
              등록됨 (선택 불가)
            </span>
            <span style={{ flex: 1 }} />
            <span className="ap-body-strong" style={{
              color: selected.size > 0 ? "var(--action-blue)" : "var(--ink-48)",
              fontSize: 15,
            }}>{selected.size}건 선택</span>
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: "flex", gap: 12, justifyContent: "flex-end", marginTop: 28 }}>
          <a href="./settings.html" className="ap-btn-secondary" style={{ textDecoration: "none" }}>취소</a>
          <button
            className="ap-btn-primary"
            disabled={selected.size === 0}
            onClick={() => {
              alert(`${selected.size}건 추가됨\n` + [...selected].sort().join(", "));
              window.location.href = "./settings.html";
            }}>
            선택한 {selected.size}건 추가
          </button>
        </div>

      </div>
    </PageShell>
  );
}

Object.assign(window, { TimesAddApp });
