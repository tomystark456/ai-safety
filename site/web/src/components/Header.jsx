import { SECTIONS } from "../data/stories";

export default function Header({ active, onSelect }) {
  return (
    <header className="top">
      <div className="wrap top-row">
        <a className="logo" href="#top" onClick={() => onSelect("news")}>
          TENGRI<span>DEMO</span>
        </a>
        <nav className="sections">
          {SECTIONS.map((s) => (
            <button
              key={s.key}
              className={active === s.key ? "on" : ""}
              onClick={() => onSelect(s.key)}
            >
              {s.label.toUpperCase()}
            </button>
          ))}
          <button
            className={"tab-chat" + (active === "chat" ? " on" : "")}
            onClick={() => onSelect("chat")}
          >
            ЧАТ
          </button>
        </nav>
        <div className="meta">
          учебный макет · Vicuna · 3 режима
        </div>
      </div>
    </header>
  );
}
