// Общая логика чата: приветствие и разбор NDJSON-потока Ollama (/api/chat через server.py).

export const GREETING = {
  role: "assistant",
  content:
    "Здравствуйте! Я редакторский помощник на локальной модели. Спрошу про материалы макета или помогу сформулировать текст.",
};

export async function* streamChat(messages, signal, mode) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, mode }),
    signal,
  });
  if (!response.ok || !response.body) {
    const text = await response.text().catch(() => "");
    throw new Error(text || response.statusText || "Сетевая ошибка");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (!line.trim()) continue;
      const packet = JSON.parse(line);
      if (packet.error) throw new Error(packet.error);
      const piece = packet.message && packet.message.content;
      if (piece) yield piece;
    }
  }
}
