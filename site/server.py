"""Local news assistant with a guarded Ollama model and SmoothLLM-style defence."""

from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from safety import MAX_BODY_BYTES, ValidationError, validate_messages
from smoothllm import defend

ROOT = Path(__file__).resolve().parent
# Собранный React-фронтенд (vite build). Если его нет — отдаём старый статический макет.
WEB_DIST = ROOT / "web" / "dist"
STATIC_ROOT = WEB_DIST if (WEB_DIST / "index.html").is_file() else ROOT
OLLAMA = "http://127.0.0.1:11434/api/chat"
MODEL = "vicuna-guarded"
SMOOTHLLM_ENABLED = os.environ.get("SMOOTHLLM_ENABLED", "1") == "1"
MODEL_MODES = {
    "baseline": ("vicuna:7b", False),
    "guarded": ("vicuna-guarded", False),
    "guarded_smooth": ("vicuna-guarded", True),
}
DEFAULT_MODE = "guarded_smooth" if SMOOTHLLM_ENABLED else "guarded"


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
        try:
            if self.headers.get("Transfer-Encoding"):
                raise ValidationError("transfer_encoding_not_supported")
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                raise ValidationError("invalid_content_length")
            if length <= 0:
                raise ValidationError("body_required")
            if length > MAX_BODY_BYTES:
                raise ValidationError("body_too_large", 413)
            self.connection.settimeout(30)
            body = json.loads(self.rfile.read(length) or b"{}")
            messages = validate_messages(body)
            mode = body.get("mode", DEFAULT_MODE)
            if not isinstance(mode, str) or mode not in MODEL_MODES:
                raise ValidationError("unknown_model_mode")
            model, smoothing = MODEL_MODES[mode]
            if mode == "baseline":
                # Keep API validation, but let base Vicuna use its own system prompt.
                messages = messages[1:]
        except ValidationError as exc:
            self.json_error(exc.status, exc.code)
            return
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.json_error(400, "invalid_json")
            return
        except (TimeoutError, socket.timeout):
            self.json_error(408, "request_timeout")
            return
        if smoothing:
            # Buffer all candidates. Never stream a response before the vote.
            try:
                result, _, _ = defend(model, messages)
            except (urllib.error.URLError, OSError, ValueError):
                self.json_error(502, "defence_or_model_unavailable")
                return
            data = (json.dumps(result, ensure_ascii=False) + "\n").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Model-Mode", mode)
            self.end_headers()
            self.wfile.write(data)
            return
        payload = json.dumps(
            {
                "model": model,
                "messages": messages,
                "stream": True,
                "options": {"temperature": 0, "num_predict": 96, "num_ctx": 2048,
                            "seed": 20261027, "num_gpu": 99},
            }
        ).encode()
        request = urllib.request.Request(
            OLLAMA,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            upstream = urllib.request.urlopen(request, timeout=30)
        except (urllib.error.URLError, OSError):
            self.json_error(502, "model_unavailable")
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("X-Model-Mode", mode)
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
        except (OSError, TimeoutError):
            try:
                self.wfile.write(b'{"error":"model_stream_interrupted"}\n')
                self.wfile.flush()
            except OSError:
                pass
        finally:
            upstream.close()

    def json_error(self, status, code):
        self.close_connection = True
        data = json.dumps({"error": code}).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()
