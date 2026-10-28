import { useEffect, useRef, useState } from "react";
import { useConversations } from "../hooks/useConversations";
import ModelSelector from "./ModelSelector";

// Полноэкранная вкладка чата с историей переписок — удобно показывать на защите.
export default function ChatPage() {
  const [text, setText] = useState("");
  const {
    conversations,
    activeId,
    messages,
    busy,
    status,
    send,
    stop,
    newChat,
    selectChat,
    deleteChat,
    clearAll,
    modelMode,
    selectModel,
  } = useConversations();
  const logRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [activeId]);

  const submit = (e) => {
    e.preventDefault();
    send(text);
    setText("");
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit(e);
    }
  };

  return (
    <div className="chatpage">
      <div className="chatpage__grid">
        <aside className="convlist">
          <button
            className="convlist__new"
            onClick={() => {
              newChat();
              setText("");
            }}
          >
            + Новый чат
          </button>
          <div className="convlist__label">
            История ({conversations.length})
          </div>
          <ul className="convlist__items">
            {conversations.map((c) => (
              <li
                key={c.id}
                className={c.id === activeId ? "on" : ""}
                onClick={() => selectChat(c.id)}
              >
                <div className="convlist__text">
                  <strong>{c.title}</strong>
                  <span>{new Date(c.updatedAt).toLocaleString("ru-RU")}</span>
                </div>
                <button
                  className="convlist__del"
                  title="Удалить"
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteChat(c.id);
                  }}
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
          <button
            className="convlist__clear"
            onClick={() => {
              if (window.confirm("Удалить всю историю переписок?")) clearAll();
            }}
          >
            Очистить всю историю
          </button>
        </aside>

        <div className="chatpage__main">
          <header className="chatpage__head">
            <div>
              <h1>Редакторский помощник</h1>
              <p>Учебный ИИ может ошибаться. Проверяйте факты и источники перед публикацией. История сохраняется в этом браузере: не вводите личные данные.</p>
            </div>
          </header>

          <ModelSelector value={modelMode} onChange={selectModel} disabled={busy} />

          <div className="chatpage__log" ref={logRef}>
            {messages.map((m, i) => (
              <div key={i} className={`pbubble pbubble--${m.role}`}>
                {m.content || (busy && i === messages.length - 1 ? <Dots /> : "")}
              </div>
            ))}
          </div>

          <form className="chatpage__form" onSubmit={submit}>
            <textarea
              ref={inputRef}
              rows={2}
              value={text}
              placeholder="Напишите сообщение… (Enter — отправить, Shift+Enter — перенос строки)"
              onChange={(e) => setText(e.target.value)}
              onKeyDown={onKeyDown}
            />
            {busy ? (
              <button type="button" className="chatpage__send chatpage__send--stop" onClick={stop}>
                Стоп
              </button>
            ) : (
              <button type="submit" className="chatpage__send" disabled={!text.trim()}>
                Отправить
              </button>
            )}
          </form>
          <p className="chatpage__status">{status}</p>
        </div>
      </div>
    </div>
  );
}

function Dots() {
  return (
    <span className="dots dots--big">
      <span />
      <span />
      <span />
    </span>
  );
}
