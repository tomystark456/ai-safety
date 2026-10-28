import { useEffect } from "react";

export default function Reader({ story, onClose }) {
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  if (!story) return null;

  return (
    <div className="reader" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <article className="reader__card">
        <button className="reader__close" onClick={onClose} aria-label="Закрыть">
          ×
        </button>
        <img className="reader__img" src={story.image} alt="" />
        <p className="kicker">{story.cat}</p>
        <h2>{story.title}</h2>
        <p className="when">{story.time}</p>
        <div className="reader__body">
          <p>{story.body}</p>
          <p>
            Это учебная страница. Спросите помощника справа внизу — отвечает локальная
            модель <code>vicuna:7b</code>.
          </p>
        </div>
      </article>
    </div>
  );
}
