from django.conf import settings
from .notification_bus import publish_email_event
from .tokens import build_account_token


def _frontend_base_url() -> str:
    return str(getattr(settings, "FRONTEND_BASE_URL", "http://localhost:5173")).rstrip("/")


def send_activation_email(user):
    token = build_account_token(user.id, "activate")
    url = f"{_frontend_base_url()}/activate-account?token={token}"
    publish_email_event(
        {
            "template": "activation",
            "to": user.email,
            "subject": "Activation de votre compte ADN PRO SERVICE",
            "from_email": getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
            "data": {
                "full_name": user.full_name or user.username,
                "activation_url": url,
            },
        }
    )


def send_password_setup_email(user):
    token = build_account_token(user.id, "setup-password")
    url = f"{_frontend_base_url()}/setup-password?token={token}"
    publish_email_event(
        {
            "template": "setup_password",
            "to": user.email,
            "subject": "Créez votre mot de passe ADN PRO SERVICE",
            "from_email": getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
            "data": {
                "full_name": user.full_name or user.username,
                "setup_password_url": url,
            },
        }
    )

