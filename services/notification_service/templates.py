import html
from typing import Dict, Tuple

BRAND_PRIMARY = "#08047a"
BRAND_ACCENT = "#7a7ee5"


def _email_shell(page_title: str, inner_html: str) -> str:
    safe_title = html.escape(page_title)
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
</head>
<body style="margin:0;background:#f4f5fc;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f5fc;padding:28px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0"
          style="max-width:600px;width:100%;background:#ffffff;border-radius:16px;overflow:hidden;
          box-shadow:0 8px 32px rgba(8,4,122,0.1);border:1px solid #e2e4f5;">
          <tr>
            <td style="background:{BRAND_PRIMARY};padding:22px 28px;">
              <p style="margin:0;font-size:11px;font-weight:700;letter-spacing:0.18em;text-transform:uppercase;color:{BRAND_ACCENT};">
                ADN PRO SERVICE
              </p>
              <h1 style="margin:10px 0 0;font-size:20px;line-height:1.25;color:#ffffff;font-weight:700;">
                {safe_title}
              </h1>
            </td>
          </tr>
          <tr>
            <td style="padding:28px 28px 8px;color:#1e293b;font-size:15px;line-height:1.65;">
              {inner_html}
            </td>
          </tr>
          <tr>
            <td style="padding:8px 28px 26px;font-size:12px;line-height:1.5;color:#64748b;">
              Message automatique — merci de ne pas répondre directement à cette adresse d&apos;envoi.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _cta_button(href: str, label: str) -> str:
    safe_href = html.escape(href, quote=True)
    safe_label = html.escape(label)
    return f"""
      <p style="margin:24px 0 8px;">
        <a href="{safe_href}" style="display:inline-block;padding:14px 28px;background:{BRAND_PRIMARY};
          color:#ffffff;text-decoration:none;border-radius:12px;font-weight:700;font-size:14px;">
          {safe_label}
        </a>
      </p>
      <p style="margin:0;font-size:12px;color:#64748b;word-break:break-all;">{html.escape(href)}</p>
    """


def _email_activation(data: Dict) -> Tuple[str, str, str]:
    full_name = data.get("full_name", "Utilisateur")
    activation_url = data.get("activation_url", "")
    subject = data.get("subject") or "Activation de votre compte ADN PRO SERVICE"
    plain = (
        f"Bonjour {full_name},\n\n"
        "Merci pour votre inscription sur ADN PRO SERVICE.\n"
        "Veuillez activer votre compte en ouvrant ce lien :\n"
        f"{activation_url}\n\n"
        "Ce lien expire automatiquement.\n"
    )
    inner = (
        f"<p>Bonjour <strong>{html.escape(str(full_name))}</strong>,</p>"
        "<p>Merci pour votre inscription sur <strong>ADN PRO SERVICE</strong>.</p>"
        "<p>Activez votre compte en un clic :</p>"
        f"{_cta_button(activation_url, 'Activer mon compte')}"
        "<p style=\"margin-top:20px;\">Ce lien expire automatiquement pour des raisons de sécurité.</p>"
    )
    return subject, plain, _email_shell("Activation de votre compte", inner)


def _email_setup_password(data: Dict) -> Tuple[str, str, str]:
    full_name = data.get("full_name", "Utilisateur")
    setup_url = data.get("setup_password_url", "")
    subject = data.get("subject") or "Créez votre mot de passe ADN PRO SERVICE"
    plain = (
        f"Bonjour {full_name},\n\n"
        "Un compte a été créé pour vous sur ADN PRO SERVICE.\n"
        "Définissez votre mot de passe en ouvrant ce lien :\n"
        f"{setup_url}\n\n"
        "Ce lien expire automatiquement.\n"
    )
    inner = (
        f"<p>Bonjour <strong>{html.escape(str(full_name))}</strong>,</p>"
        "<p>Un compte a été créé pour vous sur <strong>ADN PRO SERVICE</strong>.</p>"
        "<p>Définissez votre mot de passe :</p>"
        f"{_cta_button(setup_url, 'Choisir mon mot de passe')}"
        "<p style=\"margin-top:20px;\">Ce lien expire automatiquement.</p>"
    )
    return subject, plain, _email_shell("Création de votre accès", inner)


def _email_generic(data: Dict) -> Tuple[str, str, str]:
    subject = data.get("subject") or "Notification ADN PRO SERVICE"
    raw_body = data.get("body") or ""
    plain = str(raw_body)
    inner = f"<p style=\"white-space:pre-wrap;\">{html.escape(plain)}</p>"
    return subject, plain, _email_shell(subject, inner)


def render_email(template: str, data: Dict) -> Tuple[str, str, str]:
    if template == "activation":
        return _email_activation(data)
    if template == "setup_password":
        return _email_setup_password(data)
    return _email_generic(data)


def render_push(template: str, data: Dict) -> Dict:
    title = data.get("title") or "Notification ADN PRO SERVICE"
    message = data.get("message") or data.get("body") or ""
    return {"title": title, "message": message, "template": template}


def render_sms(template: str, data: Dict) -> str:
    if template == "activation":
        return f"Activez votre compte ADN PRO SERVICE: {data.get('activation_url', '')}"
    if template == "setup_password":
        return f"Définissez votre mot de passe ADN PRO SERVICE: {data.get('setup_password_url', '')}"
    return data.get("message") or data.get("body") or ""
