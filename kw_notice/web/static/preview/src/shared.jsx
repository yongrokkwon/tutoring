/* shared nav + helpers — design/src/shared.jsx 기반.
   링크 URL 은 window.__PRELOAD__.urls 로 서버에서 주입. */

function GlobalNav({ active }) {
  const urls = window.__PRELOAD__.urls;
  return (
    <div className="ap-global-nav">
      <a href={urls.notices} className="logo">KW · Notice</a>
      <a href={urls.notices} style={active === "notices" ? { color: "#fff", fontWeight: 600 } : null}>공지</a>
      <a href={urls.settings} style={active === "settings" ? { color: "#fff", fontWeight: 600 } : null}>설정</a>
      <span className="grow" />
    </div>
  );
}

function SubNav({ category, activeTab }) {
  const urls = window.__PRELOAD__.urls;
  return (
    <div className="ap-sub-nav">
      <span className="cat">{category}</span>
      <span className="grow" />
      <a href={urls.notices} className={activeTab === "notices" ? "active" : ""}>공지</a>
      <a href={urls.settings} className={activeTab === "settings" ? "active" : ""}>설정</a>
    </div>
  );
}

function PageShell({ category, activeTab, children }) {
  return (
    <>
      <GlobalNav active={activeTab} />
      <main className="ap-page">{children}</main>
    </>
  );
}

Object.assign(window, { GlobalNav, SubNav, PageShell });
