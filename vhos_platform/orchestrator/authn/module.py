"""Auth module — auth ladder + HMAC capability token."""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Optional

from agents.base import AuthLevel, AuthPrincipal
from config import settings


class AuthnModule:
    def __init__(self):
        self._secret = settings.capability_token_secret.encode()

    def issue_capability_token(self, session_id: str, agent_id: str, principal_id: str,
                                auth_level: AuthLevel) -> str:
        payload = {
            "session_id": session_id,
            "agent_id": agent_id,
            "principal_id": principal_id,
            "auth_level": auth_level.value,
            "issued_at": time.time(),
            "expires_at": time.time() + settings.token_ttl_seconds,
        }
        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        sig = hmac.new(self._secret, payload_bytes, hashlib.sha256).hexdigest()
        return f"{payload_bytes.hex()}.{sig}"

    def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload_hex, sig = token.rsplit(".", 1)
            payload_bytes = bytes.fromhex(payload_hex)
            expected_sig = hmac.new(self._secret, payload_bytes, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expected_sig):
                return None
            payload = json.loads(payload_bytes)
            if payload["expires_at"] < time.time():
                return None
            return payload
        except Exception:
            return None

    def build_principal(self, principal_id: str, auth_level_str: str,
                        identity_claims: dict = None) -> AuthPrincipal:
        try:
            level = AuthLevel(auth_level_str)
        except ValueError:
            level = AuthLevel.NONE
        return AuthPrincipal(
            principal_id=principal_id,
            auth_level=level,
            verified_at=time.time(),
            identity_claims=identity_claims or {},
        )

    def verify_staff_pin(self, staff_id: str, pin: str) -> bool:
        """Demo: accept any 4-digit PIN. Production: verify against HR system."""
        return len(pin) == 4 and pin.isdigit()
