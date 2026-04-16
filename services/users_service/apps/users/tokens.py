import base64
import json
from django.core import signing
from django.conf import settings


SIGNER_SALT = "users-service.account-links.v1"


def build_account_token(user_id: str, purpose: str) -> str:
    signer = signing.TimestampSigner(salt=SIGNER_SALT)
    payload = {"uid": str(user_id), "purpose": purpose}
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    compact = base64.urlsafe_b64encode(raw).decode("ascii")
    return signer.sign(compact)


def parse_account_token(token: str, purpose: str) -> str:
    signer = signing.TimestampSigner(salt=SIGNER_SALT)
    max_age = int(getattr(settings, "ACCOUNT_TOKEN_EXPIRATION_MINUTES", 60)) * 60
    unsigned = signer.unsign(token, max_age=max_age)
    raw = base64.urlsafe_b64decode(unsigned.encode("ascii"))
    payload = json.loads(raw.decode("utf-8"))
    if payload.get("purpose") != purpose:
        raise signing.BadSignature("Invalid token purpose")
    uid = payload.get("uid")
    if not uid:
        raise signing.BadSignature("Missing uid")
    return str(uid)

