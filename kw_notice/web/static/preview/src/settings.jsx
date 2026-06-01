/* Area 4 — /preview/settings (인터랙티브 + 실 POST). */

const FREQ_OPTIONS = [
  { id: "high",   label: "고빈도", sub: "15분마다",        range: "10:00 ~ 17:00" },
  { id: "medium", label: "중빈도", sub: "매시 정각",         range: "10:00 ~ 17:00" },
  { id: "low",    label: "저빈도", sub: "하루 1회",         range: "17:00" },
  { id: "custom", label: "기타",   sub: "직접 등록",        range: "사용자 지정 시각" },
];

function Toggle({ on, onChange }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      onClick={() => onChange(!on)}
      style={{
        display: "inline-block",
        width: 52, height: 32, borderRadius: 999,
        background: on ? "var(--action-blue)" : "#d2d2d7",
        position: "relative",
        transition: "background 160ms ease",
        flex: "0 0 52px",
        border: 0,
        padding: 0,
        cursor: "pointer",
      }}>
      <span style={{
        position: "absolute",
        top: 2, left: on ? 22 : 2,
        width: 28, height: 28, borderRadius: "50%",
        background: "#fff",
        boxShadow: "0 2px 4px rgba(0,0,0,0.15), 0 1px 1px rgba(0,0,0,0.06)",
        transition: "left 160ms cubic-bezier(.3,.7,.4,1.3)",
      }} />
    </button>
  );
}

function FreqOption({ option, checked, onChange }) {
  return (
    <label
      style={{
        display: "grid",
        gridTemplateColumns: "20px auto 1fr",
        alignItems: "center",
        gap: 16,
        padding: "20px 24px",
        cursor: "pointer",
        background: checked ? "rgba(0,102,204,0.03)" : "transparent",
        transition: "background 120ms ease",
      }}>
      <input
        type="radio"
        form="cfg-form"
        name="frequency_mode"
        value={option.id}
        checked={checked}
        onChange={() => onChange(option.id)}
        style={{
          width: 20, height: 20,
          accentColor: "var(--action-blue)",
          margin: 0,
          cursor: "pointer",
        }}
      />
      <span className="ap-body-strong" style={{ fontSize: 18 }}>{option.label}</span>
      <span style={{
        display: "flex",
        flexDirection: "column",
        gap: 2,
        alignItems: "flex-end",
        textAlign: "right",
      }}>
        <span className="ap-caption" style={{ color: "var(--ink-48)" }}>{option.sub}</span>
        <span className="ap-caption" style={{ color: "var(--ink-80)", fontVariantNumeric: "tabular-nums" }}>
          {option.range}
        </span>
      </span>
    </label>
  );
}

function SectionHeader({ kicker, title, hint }) {
  return (
    <div style={{ marginBottom: 16, padding: "0 4px" }}>
      <div className="ap-fine" style={{
        color: "var(--ink-48)",
        letterSpacing: "0.5px",
        textTransform: "uppercase",
        marginBottom: 6,
        fontWeight: 600,
      }}>{kicker}</div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
        <h2 className="ap-tagline" style={{ margin: 0 }}>{title}</h2>
        {hint && <span className="ap-caption" style={{ color: "var(--ink-48)" }}>{hint}</span>}
      </div>
    </div>
  );
}

function CustomTimesCard({ times, urls }) {
  return (
    <div className="ap-card" style={{ padding: "8px 8px" }}>
      {times.length === 0 ? (
        <div style={{ padding: "32px 24px", textAlign: "center", color: "var(--ink-48)" }} className="ap-body">
          등록된 시각이 없습니다.
        </div>
      ) : (
        times.map((c, i) => (
          <React.Fragment key={c.id}>
            <div style={{
              display: "flex", alignItems: "center",
              padding: "16px 20px",
            }}>
              <span style={{
                width: 8, height: 8, borderRadius: "50%",
                background: "var(--action-blue)",
                marginRight: 14,
              }} />
              <span className="ap-body" style={{
                fontSize: 18, fontWeight: 500,
                fontVariantNumeric: "tabular-nums",
                flex: 1,
              }}>{c.t}</span>
              <form method="post" action={urls.times_delete} style={{ margin: 0 }}>
                <input type="hidden" name="id" value={c.id} />
                <button
                  type="submit"
                  style={{
                    background: "transparent",
                    border: 0,
                    color: "var(--action-blue)",
                    fontFamily: "var(--font-body)",
                    fontSize: 15,
                    cursor: "pointer",
                    padding: "6px 10px",
                    borderRadius: 6,
                  }}>삭제</button>
              </form>
            </div>
            {i < times.length - 1 && (
              <div style={{ height: 1, background: "var(--divider-soft)", marginLeft: 42 }} />
            )}
          </React.Fragment>
        ))
      )}
      <div style={{ padding: "12px 16px 8px" }}>
        <a href={urls.times_add} style={{
          display: "block",
          textAlign: "center",
          background: "var(--pearl)",
          color: "var(--action-blue)",
          border: "1px solid rgba(0,0,0,0.04)",
          borderRadius: 12,
          padding: "12px 16px",
          fontFamily: "var(--font-body)",
          fontSize: 15,
          fontWeight: 500,
          textDecoration: "none",
          transition: "background 120ms ease",
        }}
        onMouseEnter={e => e.currentTarget.style.background = "#f3f3f5"}
        onMouseLeave={e => e.currentTarget.style.background = "var(--pearl)"}>
          ＋ 시각 추가
        </a>
      </div>
    </div>
  );
}

function FlashBanner({ messages, errorMap }) {
  if (!messages || messages.length === 0) return null;
  return (
    <div style={{
      marginBottom: 28,
      padding: "12px 16px",
      borderRadius: 12,
      background: "#fff4e5",
      border: "1px solid #f0c987",
      color: "#8a4a00",
    }} className="ap-caption">
      {messages.map((m, i) => (
        <div key={i}>{errorMap[m] || m}</div>
      ))}
    </div>
  );
}

function SettingsApp() {
  const preload = window.__PRELOAD__;
  const urls = preload.urls;
  const initial = preload.settings;
  const [mode, setMode] = React.useState(initial.frequency_mode);
  const [active, setActive] = React.useState(initial.is_active);
  const times = initial.custom_times;

  return (
    <PageShell category="설정" activeTab="settings">
      <div className="ap-page-inner">

        <FlashBanner messages={preload.flashes} errorMap={preload.error_messages} />

        {/* Hero */}
        <header style={{ marginBottom: 44 }}>
          <h1 className="ap-display-lg" style={{ margin: "0 0 12px" }}>설정</h1>
          <p className="ap-lead" style={{ margin: 0, color: "var(--ink-80)" }}>
            새 공지를 어떤 빈도로 확인하고 어디로 보낼지 정해주세요.
          </p>
        </header>

        {/* 빈 form — 아래 input/button 들이 form="cfg-form" 으로 연결.
            CustomTimesCard 의 내부 삭제 form 과 nested 되지 않게 분리해두는 트릭. */}
        <form id="cfg-form" method="post" action={urls.save}></form>

        {/* 알림 상태 — 맨 위 */}
        <section style={{ marginBottom: 36 }}>
          <SectionHeader kicker="알림 상태" title="알림 활성화" />
          <div className="ap-card">
            <label style={{
              display: "flex",
              alignItems: "center",
              gap: 20,
              padding: "20px 24px",
              cursor: "pointer",
            }}>
              <Toggle on={active} onChange={setActive} />
              <span style={{ flex: 1 }}>
                <div className="ap-body-strong">새 공지가 올라오면 알릴게요</div>
                <div className="ap-caption" style={{ color: "var(--ink-80)", marginTop: 3 }}>
                  꺼두면 DB 에는 기록되지만 Discord 발송은 건너뜁니다.
                </div>
              </span>
              {active && <input form="cfg-form" type="hidden" name="is_active" value="1" />}
            </label>
          </div>
        </section>

        {/* 주기 */}
        <section style={{ marginBottom: mode === "custom" ? 16 : 36 }}>
          <SectionHeader kicker="주기" title="언제 확인할까요" hint="평일 10:00 – 17:00 안에서만 동작합니다" />
          <div className="ap-card">
            {FREQ_OPTIONS.map((o, i) => (
              <React.Fragment key={o.id}>
                <FreqOption option={o} checked={mode === o.id} onChange={setMode} />
                {i < FREQ_OPTIONS.length - 1 && (
                  <div style={{ height: 1, background: "var(--divider-soft)", margin: "0 24px" }} />
                )}
              </React.Fragment>
            ))}
          </div>
        </section>

        {/* 사용자 지정 시각 — 기타일 때만, 주기 카드 바로 아래에 인접 배치 */}
        {mode === "custom" && (
          <section style={{ marginBottom: 36 }}>
            <SectionHeader
              kicker="사용자 지정 시각"
              title={times.length > 0 ? `등록된 시각 ${times.length}건` : "등록된 시각이 없습니다"}
              hint="15분 단위, 운영시간 내에서 등록 가능"
            />
            <CustomTimesCard times={times} urls={urls} />
          </section>
        )}

        {/* 저장 */}
        <div style={{
          display: "flex",
          gap: 12,
          justifyContent: "space-between",
          alignItems: "center",
          marginTop: 12,
          marginBottom: 52,
          padding: "0 4px",
          flexWrap: "wrap",
        }}>
          <span className="ap-caption" style={{ color: "var(--ink-48)" }}>
            변경 사항은 다음 분 (최대 60초) 안에 크롤러에 반영됩니다.
          </span>
          <button type="submit" form="cfg-form" className="ap-btn-primary" style={{ minWidth: 120 }}>저장</button>
        </div>

        {/* 발송 테스트 */}
        <section id="test-send">
          <SectionHeader kicker="발송 테스트" title="지금 한 번 보내볼까요" />
          <div className="ap-card" style={{ padding: 28 }}>
            <p className="ap-body" style={{ margin: "0 0 8px", color: "var(--ink-80)" }}>
              운영시간과 알림 활성화 설정을 무시하고, 최신 공지 <b>1건</b>을 Discord 로 즉시 발송합니다.
            </p>
            <p className="ap-caption" style={{ margin: "0 0 20px", color: "var(--ink-48)" }}>
              <code style={{
                fontFamily: "var(--font-mono)",
                background: "var(--parchment)",
                padding: "2px 6px",
                borderRadius: 4,
                fontSize: 12,
              }}>notifications</code> 이력에는 기록되지 않습니다.
            </p>
            <form method="post" action={urls.test_send} style={{ margin: 0 }}>
              <button type="submit" className="ap-btn-secondary">발송 테스트</button>
            </form>
          </div>
        </section>

      </div>
    </PageShell>
  );
}

Object.assign(window, { SettingsApp });
