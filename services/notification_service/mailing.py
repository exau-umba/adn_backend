import json
import os
import smtplib
from email.message import EmailMessage

from templates import render_email, render_push, render_sms

EMAIL_HOST = os.getenv("EMAIL_HOST", "mail.adnproservice.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "465"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "no-reply@adnproservice.com")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "True").lower() == "true"
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "20"))
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)


def send_email(payload: dict):
    template = payload.get("template", "")
    data = payload.get("data", {})
    rendered_subject, rendered_body = render_email(template, data)
    subject = payload.get("subject") or rendered_subject
    recipient = payload.get("to")
    if not recipient:
        raise ValueError("Missing recipient")
    from_email = payload.get("from_email") or DEFAULT_FROM_EMAIL
    body = rendered_body

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = recipient
    msg.set_content(body)

    if EMAIL_USE_SSL:
        with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT, timeout=EMAIL_TIMEOUT) as server:
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.send_message(msg)
    else:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=EMAIL_TIMEOUT) as server:
            server.starttls()
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.send_message(msg)


def send_push(payload: dict):
    device_token = payload.get("device_token")
    if not device_token:
        raise ValueError("Missing push device_token")
    template = payload.get("template", "")
    data = payload.get("data", {})
    message = render_push(template, data)
    print(f"[notification] PUSH to={device_token} payload={json.dumps(message)}")


def send_sms(payload: dict):
    phone = payload.get("phone")
    if not phone:
        raise ValueError("Missing sms phone")
    template = payload.get("template", "")
    data = payload.get("data", {})
    message = render_sms(template, data)
    print(f"[notification] SMS to={phone} message={message}")


def dispatch_notification(payload: dict):
    channel_name = (payload.get("channel") or "email").lower()
    if channel_name == "email":
        send_email(payload)
        print(f"[notification] Email sent to {payload.get('to')}")
        return
    if channel_name == "push":
        send_push(payload)
        return
    if channel_name == "sms":
        send_sms(payload)
        return
    raise ValueError(f"Unsupported channel: {channel_name}")
