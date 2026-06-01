/* shared nav + helpers — exported to window for page scripts */

function GlobalNav({ active }) {
  return (
    <div className="ap-global-nav">
      <a href="./index.html" className="logo">KW · Notice</a>
      <a href="./index.html" style={active === "notices" ? { color: "#fff", fontWeight: 600 } : null}>공지</a>
      <a href="./settings.html" style={active === "settings" ? { color: "#fff", fontWeight: 600 } : null}>설정</a>
      <span className="grow" />
      <a href="./settings.html#test-send">테스트 발송</a>
    </div>
  );
}

function SubNav({ category, activeTab }) {
  return (
    <div className="ap-sub-nav">
      <span className="cat">{category}</span>
      <span className="grow" />
      <a href="./index.html" className={activeTab === "notices" ? "active" : ""}>공지</a>
      <a href="./settings.html" className={activeTab === "settings" ? "active" : ""}>설정</a>
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
