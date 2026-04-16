from typing import Dict, Tuple


def _email_activation(data: Dict) -> Tuple[str, str]:
    full_name = data.get("full_name", "Utilisateur")
    subject = data.get("subject") or "Activation de votre compte ADN PRO SERVICE"
    body = (
        f"Bonjour {full_name},\n\n"
        "Merci pour votre inscription sur ADN PRO SERVICE.\n"
        "Veuillez activer votre compte en cliquant sur ce lien :\n"
        f"{data.get('activation_url', '')}\n\n"
        "Ce lien expire automatiquement.\n"
    )
    return subject, body


def _email_setup_password(data: Dict) -> Tuple[str, str]:
    full_name = data.get("full_name", "Utilisateur")
    subject = data.get("subject") or "Créez votre mot de passe ADN PRO SERVICE"
    body = (
        f"Bonjour {full_name},\n\n"
        "Un compte a été créé pour vous sur ADN PRO SERVICE.\n"
        "Définissez votre mot de passe en cliquant sur ce lien :\n"
        f"{data.get('setup_password_url', '')}\n\n"
        "Ce lien expire automatiquement.\n"
    )
    return subject, body


def render_email(template: str, data: Dict) -> Tuple[str, str]:
    if template == "activation":
        return _email_activation(data)
    if template == "setup_password":
        return _email_setup_password(data)
    return (
        data.get("subject") or "Notification ADN PRO SERVICE",
        data.get("body") or "",
    )


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

