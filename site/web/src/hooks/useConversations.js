import { useCallback, useEffect, useRef, useState } from "react";
import { GREETING, streamChat } from "../lib/chat";
import { preferredMode, rememberMode, validMode } from "../lib/modelModes";

const STORE_KEY = "tengri-chats-v1";

const newId = () =>
  (typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : String(Date.now()) + Math.random().toString(16).slice(2));

function freshConversation(modelMode = preferredMode()) {
  const now = Date.now();
  return {
    id: newId(),
    title: "Новый чат",
    messages: [GREETING],
    modelMode,
    createdAt: now,
    updatedAt: now,
  };
}

// Заголовок чата — первая реплика пользователя, обрезанная.
function titleFrom(messages) {
  const firstUser = messages.find((m) => m.role === "user");
  if (!firstUser) return "Новый чат";
  const t = firstUser.content.trim().replace(/\s+/g, " ");
  return t.length > 42 ? t.slice(0, 42) + "…" : t;
}

function load() {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (!Array.isArray(data.conversations) || data.conversations.length === 0) return null;
    return data;
  } catch {
    return null;
  }
}

export function useConversations() {
  const [conversations, setConversations] = useState(() => {
    const data = load();
    return data ? data.conversations : [freshConversation()];
  });
  const [activeId, setActiveId] = useState(() => {
    const data = load();
    return data ? data.activeId || data.conversations[0].id : null;
  });
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("Модель работает на этом компьютере.");
  const abortRef = useRef(null);

  // Гарантируем валидный activeId при первом рендере.
  useEffect(() => {
    setActiveId((id) => (conversations.some((c) => c.id === id) ? id : conversations[0]?.id));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Сохраняем в localStorage при любом изменении.
  useEffect(() => {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify({ conversations, activeId }));
    } catch {
      /* квота переполнена — молча пропускаем */
    }
  }, [conversations, activeId]);

  const active = conversations.find((c) => c.id === activeId) || conversations[0];
  const modelMode = validMode(active?.modelMode);

  const patch = useCallback((id, updater) => {
    setConversations((list) =>
      list.map((c) => (c.id === id ? { ...updater(c), updatedAt: Date.now() } : c)),
    );
  }, []);

  const send = useCallback(
    async (text) => {
      const trimmed = text.trim();
      if (!trimmed || busy || !active) return;
      const id = active.id;

      const base = active.messages.filter((m) => m !== GREETING || active.messages.length > 1);
      const withUser = [...active.messages, { role: "user", content: trimmed }];
      patch(id, (c) => ({
        ...c,
        title: c.title === "Новый чат" ? titleFrom(withUser) : c.title,
        messages: [...withUser, { role: "assistant", content: "" }],
      }));

      setBusy(true);
      setStatus("Модель отвечает…");
      const controller = new AbortController();
      abortRef.current = controller;

      // В модель уходит диалог без приветственной заглушки.
      const forModel = base
        .concat({ role: "user", content: trimmed })
        .filter((m) => m !== GREETING);

      let answer = "";
      try {
        for await (const piece of streamChat(forModel, controller.signal, modelMode)) {
          answer += piece;
          patch(id, (c) => {
            const msgs = c.messages.slice();
            msgs[msgs.length - 1] = { role: "assistant", content: answer };
            return { ...c, messages: msgs };
          });
        }
        if (!answer) {
          patch(id, (c) => {
            const msgs = c.messages.slice();
            msgs[msgs.length - 1] = { role: "assistant", content: "(пустой ответ)" };
            return { ...c, messages: msgs };
          });
        }
        setStatus("Готово. Можно писать дальше.");
      } catch (error) {
        if (controller.signal.aborted) {
          setStatus("Ответ остановлен. Сохранён как есть.");
        } else {
          patch(id, (c) => {
            const msgs = c.messages.slice();
            msgs[msgs.length - 1] = {
              role: "assistant",
              content: "Не удалось получить ответ. Проверьте, что Ollama и server.py запущены.",
            };
            return { ...c, messages: msgs };
          });
          setStatus(String(error.message || error));
        }
      } finally {
        setBusy(false);
        abortRef.current = null;
      }
    },
    [active, busy, patch, modelMode],
  );

  const stop = useCallback(() => abortRef.current?.abort(), []);

  const newChat = useCallback(() => {
    abortRef.current?.abort();
    setBusy(false);
    const conv = freshConversation(modelMode);
    setConversations((list) => [conv, ...list]);
    setActiveId(conv.id);
    setStatus("Новый чат. Контекст очищен.");
  }, [modelMode]);

  const selectModel = useCallback((mode) => {
    if (busy || mode === modelMode) return;
    const next = validMode(mode);
    rememberMode(next);
    if (active.messages.length <= 1) {
      patch(active.id, (c) => ({ ...c, modelMode: next }));
    } else {
      const conv = freshConversation(next);
      setConversations((list) => [conv, ...list]);
      setActiveId(conv.id);
    }
    setStatus("Модель выбрана. Новый чат готов.");
  }, [active, busy, modelMode, patch]);

  const selectChat = useCallback(
    (id) => {
      if (id === activeId) return;
      abortRef.current?.abort();
      setBusy(false);
      setActiveId(id);
      setStatus("Открыт сохранённый чат.");
    },
    [activeId],
  );

  const deleteChat = useCallback(
    (id) => {
      setConversations((list) => {
        const rest = list.filter((c) => c.id !== id);
        const next = rest.length ? rest : [freshConversation()];
        if (id === activeId) setActiveId(next[0].id);
        return next;
      });
    },
    [activeId],
  );

  const clearAll = useCallback(() => {
    abortRef.current?.abort();
    setBusy(false);
    const conv = freshConversation();
    setConversations([conv]);
    setActiveId(conv.id);
    setStatus("История очищена.");
  }, []);

  const ordered = [...conversations].sort((a, b) => b.updatedAt - a.updatedAt);

  return {
    conversations: ordered,
    active,
    activeId: active?.id,
    messages: active?.messages || [GREETING],
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
  };
}
