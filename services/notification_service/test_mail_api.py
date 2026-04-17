"""
HTTP embarqué du service notification :
- GET /internal/health : santé
- POST /public/contact : formulaire site → CONTACT_INBOX_EMAIL (ex. contact@adnproservice.com)
- POST /internal/mail/send : test Postman (uniquement si ENABLE_MAIL_TEST_API=true ; token optionnel)
"""

import json
import os
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread

from mailing import dispatch_notification, send_contact_site_message

_RATE_LOCK = Lock()
_RATE_BY_IP: dict[str, list[float]] = {}


def _truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


def _client_ip(handler: BaseHTTPRequestHandler) -> str:
    forwarded = handler.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if forwarded:
        return forwarded
    return handler.client_address[0] if handler.client_address else "unknown"


def _rate_ok(ip: str) -> bool:
    max_n = int(os.getenv("CONTACT_RATE_LIMIT_MAX", "8"))
    window = float(os.getenv("CONTACT_RATE_LIMIT_WINDOW_SEC", "900"))
    now = time.monotonic()
    with _RATE_LOCK:
        bucket = _RATE_BY_IP.setdefault(ip, [])
        bucket[:] = [t for t in bucket if now - t < window]
        if len(bucket) >= max_n:
            return False
        bucket.append(now)
    return True


def _cors_headers(handler: BaseHTTPRequestHandler):
    origin = os.getenv("CONTACT_CORS_ORIGIN", "*").strip() or "*"
    handler.send_header("Access-Control-Allow-Origin", origin)
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler.send_header("Access-Control-Max-Age", "86400")


class NotificationHttpHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[notification-http] {fmt % args}")

    def _send_json(self, code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        _cors_headers(self)
        self.end_headers()
        self.wfile.write(body)

    def _authorized_internal_mail(self) -> bool:
        if not _truthy("ENABLE_MAIL_TEST_API"):
            return False
        expected = os.getenv("MAIL_TEST_API_TOKEN", "").strip()
        if not expected:
            return True
        auth = self.headers.get("Authorization", "").strip()
        return auth == f"Bearer {expected}"

    def do_OPTIONS(self):
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path in ("/public/contact", "/public"):
            self.send_response(204)
            _cors_headers(self)
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path in ("/internal/health", "/internal"):
            self._send_json(200, {"status": "ok", "service": "notification-service"})
            return
        self._send_json(404, {"detail": "Not found"})

    def do_POST(self):
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path in ("/public/contact", "/public"):
            self._handle_public_contact()
            return
        if path in ("/internal/mail/send", "/internal/mail"):
            self._handle_internal_mail()
            return
        self._send_json(404, {"detail": "Not found"})

    def _handle_public_contact(self):
        ip = _client_ip(self)
        if not _rate_ok(ip):
            self._send_json(429, {"detail": "Trop de requêtes. Réessayez plus tard."})
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"detail": "Corps JSON invalide."})
            return
        honeypot = (data.get("website") or data.get("url") or "").strip()
        if honeypot:
            self._send_json(400, {"detail": "Requête refusée."})
            return
        from_name = (data.get("from_name") or data.get("name") or "").strip()
        from_email = (data.get("from_email") or data.get("email") or "").strip()
        subject = (data.get("subject") or "").strip()
        message = (data.get("message") or data.get("body") or "").strip()
        if len(from_name) < 2 or len(from_name) > 120:
            self._send_json(400, {"detail": "Nom invalide."})
            return
        if len(from_email) < 5 or len(from_email) > 254 or "@" not in from_email:
            self._send_json(400, {"detail": "E-mail invalide."})
            return
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", from_email):
            self._send_json(400, {"detail": "E-mail invalide."})
            return
        if len(subject) < 2 or len(subject) > 180:
            self._send_json(400, {"detail": "Sujet invalide."})
            return
        if len(message) < 10 or len(message) > 8000:
            self._send_json(400, {"detail": "Message invalide (10 à 8000 caractères)."})
            return
        try:
            send_contact_site_message(from_name=from_name, from_email=from_email, subject=subject, message=message)
            self._send_json(200, {"detail": "Message envoyé."})
        except Exception as exc:
            self._send_json(502, {"detail": f"Échec envoi: {exc}"})

    def _handle_internal_mail(self):
        if not self._authorized_internal_mail():
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


def start_notification_http_background():
    port = int(os.getenv("NOTIFICATION_HTTP_PORT", os.getenv("MAIL_TEST_API_PORT", "8090")))
    host = os.getenv("NOTIFICATION_HTTP_HOST", os.getenv("MAIL_TEST_API_HOST", "0.0.0.0"))

    def run():
        server = ThreadingHTTPServer((host, port), NotificationHttpHandler)
        print(
            f"[notification-http] http://{host}:{port} "
            "GET /internal/health | POST /public/contact"
            + (" | POST /internal/mail/send" if _truthy("ENABLE_MAIL_TEST_API") else "")
        )
        server.serve_forever()

    thread = Thread(target=run, name="notification-http", daemon=True)
    thread.start()


def start_mail_test_api_background():
    """Alias pour compatibilité."""
    start_notification_http_background()
