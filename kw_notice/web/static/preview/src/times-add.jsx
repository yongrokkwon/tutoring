/* Area 4 — /preview/settings/times/add (인터랙티브 그리드 + 실 POST). */

function TimesAddApp() {
  const preload = window.__PRELOAD__;
  const urls = preload.urls;
  const grid = preload.grid;
  const registered = React.useMemo(() => new Set(preload.registered), [preload.registered]);
  const [selected, setSelected] = React.useState(new Set());
  const formRef = React.useRef(null);

  const toggle = (t) => {
    if (registered.has(t)) return;
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

        {preload.flashes && preload.flashes.length > 0 && (
          <div style={{
            marginBottom: 28,
            padding: "12px 16px",
            borderRadius: 12,
            background: "#fff4e5",
            border: "1px solid #f0c987",
            color: "#8a4a00",
          }} className="ap-caption">
            {preload.flashes.map((m, i) => (
              <div key={i}>{preload.error_messages[m] || m}</div>
            ))}
          </div>
        )}

        {/* Header */}
        <header style={{ marginBottom: 36 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
            <a href={urls.settings} className="ap-link" style={{ fontSize: 14 }}>← 설정으로</a>
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
            추가할 시각을 골라주세요. 15분 단위, 운영시간 내 {grid.length}칸 중 선택할 수 있습니다.
          </p>
        </header>

        <form ref={formRef} method="post" action={urls.times_add_save}>
          {[...selected].map(t => <input key={t} type="hidden" name="time" value={t} />)}

          {/* Grid */}
          <div className="ap-card" style={{ padding: 28 }}>
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(7, 1fr)",
              gap: 10,
            }}>
              {grid.map(t => {
                const isReg = registered.has(t);
                const isSel = selected.has(t);
                return (
                  <button
                    type="button"
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
            <a href={urls.settings} className="ap-btn-secondary" style={{ textDecoration: "none" }}>취소</a>
            <button
              type="submit"
              className="ap-btn-primary"
              disabled={selected.size === 0}>
              선택한 {selected.size}건 추가
            </button>
          </div>
        </form>

      </div>
    </PageShell>
  );
}

Object.assign(window, { TimesAddApp });
