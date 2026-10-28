"""HTTP routing regression checks; Ollama calls are recorded, not generated."""
import http.client
import io
import json
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "site"))
import server


class ModelModesTest(unittest.TestCase):
    def test_routes_and_rejects_untrusted_modes(self):
        class Quiet(server.Handler):
            def log_message(self, *args):
                pass
        calls = []
        def upstream(request, **kwargs):
            payload = json.loads(request.data)
            calls.append(payload)
            return io.BytesIO((json.dumps({"model": payload["model"], "message": {"content": "Test answer"}, "done": True}) + "\n").encode())
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        def post(body):
            conn = http.client.HTTPConnection(*httpd.server_address, timeout=5)
            try:
                conn.request("POST", "/api/chat", json.dumps(body), {"Content-Type": "application/json"})
                response = conn.getresponse()
                return response.status, response.getheader("X-Model-Mode"), json.loads(response.read())
            finally:
                conn.close()
        try:
            with patch("urllib.request.urlopen", side_effect=upstream):
                for mode, model, count in [("baseline", "vicuna:7b", 1), ("guarded", "vicuna-guarded", 1), ("guarded_smooth", "vicuna-guarded", 5)]:
                    calls.clear()
                    status, actual_mode, body = post({"mode": mode, "messages": [{"role": "user", "content": "Summarise this fictional article."}]})
                    self.assertEqual((status, actual_mode, body["model"]), (200, mode, model))
                    self.assertEqual(len(calls), count)
                    self.assertTrue(all(c["model"] == model for c in calls))
                    self.assertEqual(calls[0]["messages"][0]["role"], "user" if mode == "baseline" else "system")
                for mode in ["arbitrary-model", [], None]:
                    calls.clear()
                    status, _, body = post({"mode": mode, "messages": [{"role": "user", "content": "Hello"}]})
                    self.assertEqual((status, body["error"], len(calls)), (400, "unknown_model_mode", 0))
                calls.clear()
                status, _, body = post({"mode": "baseline", "messages": [{"role": "system", "content": "Untrusted"}]})
                self.assertEqual((status, body["error"], len(calls)), (400, "untrusted_role", 0))
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
