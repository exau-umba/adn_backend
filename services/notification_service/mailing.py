import html
import json
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

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
    rendered_subject, plain_body, html_body = render_email(template, data)
    subject = payload.get("subject") or rendered_subject
    recipient = payload.get("to")
    if not recipient:
        raise ValueError("Missing recipient")
    from_email = payload.get("from_email") or DEFAULT_FROM_EMAIL
    reply_to = payload.get("reply_to")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = recipient
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(plain_body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    if EMAIL_USE_SSL:
        with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT, timeout=EMAIL_TIMEOUT) as server:
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.send_message(msg)
    else:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=EMAIL_TIMEOUT) as server:
            server.starttls()
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.send_message(msg)


def send_contact_site_message(*, from_name: str, from_email: str, subject: str, message: str) -> None:
    """Transfère un message du formulaire public vers la boîte contact (ex. contact@adnproservice.com)."""

    inbox = os.getenv("CONTACT_INBOX_EMAIL", "contact@adnproservice.com").strip()
    safe_name = html.escape(from_name.strip())
    safe_email = html.escape(from_email.strip())
    safe_subject = html.escape(subject.strip())
    safe_message = html.escape(message.strip()).replace("\n", "<br>\n")
    line_subject = f"[Site] {subject.strip()}"[:180]
    plain = (
        f"Message depuis le site ADN PRO SERVICE\n\n"
        f"De : {from_name.strip()} <{from_email.strip()}>\n"
        f"Sujet : {subject.strip()}\n\n"
        f"{message.strip()}\n"
    )
    inner = (
        f"<p><strong>Nom</strong> : {safe_name}<br>"
        f"<strong>E-mail</strong> : <a href=\"mailto:{safe_email}\">{safe_email}</a><br>"
        f"<strong>Sujet</strong> : {safe_subject}</p>"
        f"<hr style=\"border:none;border-top:1px solid #e2e8f0;margin:20px 0;\">"
        f"<div style=\"font-size:15px;\">{safe_message}</div>"
    )
    html_body = (
        "<!DOCTYPE html><html lang=\"fr\"><head><meta charset=\"utf-8\"></head><body style=\"margin:0;background:#f4f5fc;font-family:Arial,Helvetica,sans-serif;\">"
        "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"padding:24px;\">"
        "<tr><td align=\"center\">"
        "<table width=\"600\" style=\"max-width:600px;background:#fff;border-radius:16px;padding:28px;border:1px solid #e2e4f5;\">"
        "<tr><td style=\"color:#08047a;font-size:18px;font-weight:700;\">Nouveau message (formulaire contact)</td></tr>"
        f"<tr><td style=\"padding-top:16px;color:#334155;\">{inner}</td></tr>"
        "</table></td></tr></table></body></html>"
    )
    msg = EmailMessage()
    msg["Subject"] = line_subject
    msg["From"] = DEFAULT_FROM_EMAIL
    msg["To"] = inbox
    msg["Reply-To"] = formataddr((from_name.strip(), from_email.strip()))
    msg.set_content(plain)
    msg.add_alternative(html_body, subtype="html")

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
