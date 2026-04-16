"""
API HTTP minimale pour tester l'envoi SMTP depuis Postman (hors RabbitMQ).
Activer avec ENABLE_MAIL_TEST_API=true. Optionnel : MAIL_TEST_API_TOKEN (Bearer).
Ne pas activer en production sans token fort et accès réseau restreint.
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from mailing import dispatch_notification


def _truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


class MailTestHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[mail-test-api] {fmt % args}")

    def _send_json(self, code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        expected = os.getenv("MAIL_TEST_API_TOKEN", "").strip()
        if not expected:
            return True
        auth = self.headers.get("Authorization", "").strip()
        return auth == f"Bearer {expected}"

    def do_GET(self):
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path in ("/internal/health", "/internal"):
            self._send_json(200, {"status": "ok", "service": "notification-mail-test"})
            return
        self._send_json(404, {"detail": "Not found"})

    def do_POST(self):
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path not in ("/internal/mail/send", "/internal/mail"):
            self._send_json(404, {"detail": "Not found"})
            return
        if not self._authorized():
            self._send_json(401, {"detail": "Unauthorized"})
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"detail": "Corps JSON invalide."})
            return
        payload.setdefault("channel", "email")
        try:
            dispatch_notification(payload)
            self._send_json(
                200,
                {
                    "detail": "E-mail envoyé.",
                    "to": payload.get("to"),
                    "channel": payload.get("channel"),
                    "template": payload.get("template"),
                },
            )
        except Exception as exc:
            self._send_json(502, {"detail": f"Echec envoi: {exc}"})


def start_mail_test_api_background():
    if not _truthy("ENABLE_MAIL_TEST_API"):
        return
    port = int(os.getenv("MAIL_TEST_API_PORT", "8090"))
    host = os.getenv("MAIL_TEST_API_HOST", "0.0.0.0")

    def run():
        server = ThreadingHTTPServer((host, port), MailTestHandler)
        print(f"[mail-test-api] Listening http://{host}:{port} POST /internal/mail/send")
        server.serve_forever()

    thread = Thread(target=run, name="mail-test-api", daemon=True)
    thread.start()
