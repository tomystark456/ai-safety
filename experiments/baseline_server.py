"""Local news demo with a chat proxy to Ollama vicuna:7b."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Собранный React-фронтенд (vite build). Если его нет — отдаём старый статический макет.
WEB_DIST = ROOT / "web" / "dist"
STATIC_ROOT = WEB_DIST if (WEB_DIST / "index.html").is_file() else ROOT
OLLAMA = "http://127.0.0.1:11434/api/chat"
MODEL = "vicuna:7b"


def clean_messages(messages: list) -> list[dict]:
    cleaned = []
    for message in messages[-12:]:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        content = message.get("content")
        if role not in ("user", "assistant", "system"):
            continue
        if not isinstance(content, str) or not content.strip():
            continue
        cleaned.append({"role": role, "content": content.strip()})
    return cleaned


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        # SPA-фолбэк: неизвестные пути (кроме файлов и /api) отдают index.html,
        # чтобы клиентская маршрутизация React работала при обновлении страницы.
        path = self.path.split("?", 1)[0]
        target = STATIC_ROOT / path.lstrip("/")
        if path != "/" and not path.startswith("/api") and not target.is_file():
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.send_error(400, "invalid json")
            return
        messages = clean_messages(body.get("messages") or [])
        if not messages:
            self.send_error(400, "messages required")
            return
        payload = json.dumps(
            {
                "model": MODEL,
                "messages": messages,
                "stream": True,
                "options": {"temperature": 0.7, "num_predict": 512},
            }
        ).encode()
        request = urllib.request.Request(
            OLLAMA,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            upstream = urllib.request.urlopen(request, timeout=600)
        except urllib.error.URLError as exc:
            self.send_response(502)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                json.dumps({"error": f"Ollama недоступна: {exc}"}).encode("utf-8")
            )
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.end_headers()
        try:
            while True:
                chunk = upstream.read(4096)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            upstream.close()

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()
