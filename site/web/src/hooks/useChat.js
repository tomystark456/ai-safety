import { useCallback, useRef, useState } from "react";
import { GREETING, streamChat } from "../lib/chat";
import { preferredMode, rememberMode, validMode } from "../lib/modelModes";

export function useChat() {
  const [modelMode, setModelMode] = useState(preferredMode);
  const [messages, setMessages] = useState([GREETING]);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("Модель работает на этом компьютере.");
  const abortRef = useRef(null);

  const send = useCallback(
    async (text) => {
      const trimmed = text.trim();
      if (!trimmed || busy) return;

      const history = [...messages, { role: "user", content: trimmed }];
      // Пустой «пузырёк» ассистента, в который будем дописывать поток.
      setMessages([...history, { role: "assistant", content: "" }]);
      setBusy(true);
      setStatus("Модель отвечает…");

      const controller = new AbortController();
      abortRef.current = controller;
      let answer = "";
      try {
        // В модель уходит только диалог без приветственной заглушки.
        const forModel = history.filter((m) => m !== GREETING);
        for await (const piece of streamChat(forModel, controller.signal, modelMode)) {
          answer += piece;
          setMessages([...history, { role: "assistant", content: answer }]);
        }
        if (!answer) {
          setMessages([...history, { role: "assistant", content: "(пустой ответ)" }]);
        }
        setStatus("Готово. Можно писать дальше.");
      } catch (error) {
        if (controller.signal.aborted) {
          setStatus("Ответ остановлен.");
        } else {
          setMessages([
            ...history,
            {
              role: "assistant",
              content: "Не удалось получить ответ. Проверьте, что Ollama и server.py запущены.",
            },
          ]);
          setStatus(String(error.message || error));
        }
      } finally {
        setBusy(false);
        abortRef.current = null;
      }
    },
    [messages, busy, modelMode],
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  // Новый чат: обрываем текущий запрос и полностью сбрасываем историю/контекст.
  const reset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setBusy(false);
    setMessages([GREETING]);
    setStatus("Новый чат. Контекст очищен.");
  }, []);

  const selectModel = useCallback((mode) => {
    if (busy || mode === modelMode) return;
    const next = validMode(mode);
    rememberMode(next);
    setModelMode(next);
    reset();
  }, [busy, modelMode, reset]);

  return { messages, busy, status, send, stop, reset, modelMode, selectModel };
}
