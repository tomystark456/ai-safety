import { useEffect, useRef, useState } from "react";
import { useChat } from "../hooks/useChat";
import ModelSelector from "./ModelSelector";

export default function Chat() {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const { messages, busy, status, send, stop, reset, modelMode, selectModel } = useChat();
  const logRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [messages]);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

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
    <>
      <button
        className={`chat-fab ${open ? "chat-fab--hidden" : ""}`}
        onClick={() => setOpen(true)}
      >
        <span className="chat-fab__dot" />
        Чат с помощником
      </button>

      <section className={`chat ${open ? "chat--open" : ""}`} aria-hidden={!open}>
        <header className="chat__head">
          <div>
            <strong>Редакторский помощник</strong>
            <small>Учебный ИИ: проверяйте факты, не вводите личные данные</small>
          </div>
          <div className="chat__actions">
            <button
              className="chat__new"
              onClick={() => {
                reset();
                setText("");
                inputRef.current?.focus();
              }}
              disabled={messages.length <= 1 && !busy}
              title="Новый чат — очистить контекст"
            >
              + Новый чат
            </button>
            <button className="chat__x" onClick={() => setOpen(false)} aria-label="Свернуть">
              ×
            </button>
          </div>
        </header>

        <ModelSelector value={modelMode} onChange={selectModel} disabled={busy} />

        <div className="chat__log" ref={logRef}>
          {messages.map((m, i) => (
            <div key={i} className={`bubble bubble--${m.role}`}>
              {m.content || (busy && i === messages.length - 1 ? <Dots /> : "")}
            </div>
          ))}
        </div>

        <form className="chat__form" onSubmit={submit}>
          <textarea
            ref={inputRef}
            rows={2}
            value={text}
            placeholder="Напишите сообщение…"
            onChange={(e) => setText(e.target.value)}
            onKeyDown={onKeyDown}
          />
          {busy ? (
            <button type="button" className="chat__send chat__send--stop" onClick={stop}>
              Стоп
            </button>
          ) : (
            <button type="submit" className="chat__send" disabled={!text.trim()}>
              Отправить
            </button>
          )}
        </form>
        <p className="chat__status">{status}</p>
      </section>
    </>
  );
}

function Dots() {
  return (
    <span className="dots">
      <span />
      <span />
      <span />
    </span>
  );
}
