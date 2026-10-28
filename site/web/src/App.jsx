import { useMemo, useState } from "react";
import Header from "./components/Header";
import Card from "./components/Card";
import Reader from "./components/Reader";
import Chat from "./components/Chat";
import ChatPage from "./components/ChatPage";
import { stories, SECTIONS } from "./data/stories";

export default function App() {
  const [active, setActive] = useState(
    () => (typeof location !== "undefined" && location.hash === "#chat" ? "chat" : "news"),
  );
  const [opened, setOpened] = useState(null);

  const byCat = useMemo(() => {
    const map = {};
    for (const s of SECTIONS) map[s.key] = stories.filter((x) => x.cat === s.key);
    return map;
  }, []);

  const news = byCat.news;
  const feed = stories;

  if (active === "chat") {
    return (
      <div id="top">
        <Header active={active} onSelect={setActive} />
        <ChatPage />
      </div>
    );
  }

  return (
    <div id="top">
      <Header active={active} onSelect={setActive} />

      <div className="hero-strip">
        <div className="wrap hero-strip__inner">
          <span className="badge">Учебный макет</span>
          <p>
            Витрина новостей + локальный ИИ-помощник на <code>vicuna:7b</code> через Ollama.
            Площадка для эксперимента по устойчивости LLM к jailbreak-суффиксам (GCG, garak).
          </p>
        </div>
      </div>

      <main className="wrap layout">
        <section>
          <SectionTitle id="news">Главное</SectionTitle>
          <div className="hero">
            <Card story={news[0]} variant="lead" onOpen={setOpened} />
            <div className="hero__stack">
              {news.slice(1).map((s) => (
                <Card key={s.id} story={s} variant="row" onOpen={setOpened} />
              ))}
            </div>
          </div>

          {SECTIONS.filter((s) => s.key !== "news").map((sec) => (
            <section className="band" key={sec.key} id={sec.key}>
              <SectionTitle>{sec.label}</SectionTitle>
              <div className="cards-grid">
                {byCat[sec.key].map((s) => (
                  <Card key={s.id} story={s} onOpen={setOpened} />
                ))}
              </div>
            </section>
          ))}
        </section>

        <aside className="rail">
          <div className="rail__tabs">
            <span className="on">Последние</span>
            <span>Популярные</span>
          </div>
          <ul className="feed">
            {feed.map((s) => (
              <li key={s.id}>
                <button onClick={() => setOpened(s)}>
                  <img src={s.image} alt="" loading="lazy" />
                  <span>
                    <strong>{s.title}</strong>
                    <span className="when">
                      {s.time} · {s.cat}
                    </span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
          <p className="note">
            Тексты выдуманы для макета. Это не сайт Tengrinews и не его материалы.
          </p>
        </aside>
      </main>

      <footer className="foot">
        <div className="wrap">
          QAIRU · AISRA1301 · Assignment 3 · прототип для оценки безопасности LLM. Чат отвечает
          локальной моделью и используется только в учебных целях.
        </div>
      </footer>

      <Reader story={opened} onClose={() => setOpened(null)} />
      <Chat />
    </div>
  );
}

function SectionTitle({ children, id }) {
  return (
    <h2 className="sec-title" id={id}>
      <span>{children}</span>
    </h2>
  );
}
