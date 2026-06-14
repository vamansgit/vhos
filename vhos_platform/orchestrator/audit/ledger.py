"""HMAC-SHA256-CHAINED audit ledger."""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Optional

from config import settings


class AuditLedger:
    def __init__(self):
        self._secret = settings.audit_hmac_secret.encode()
        self._chain: list[dict] = []
        self._last_hash = "genesis"

    def append(self, session_id: str, agent_id: str, event_type: str,
                data: dict, principal_id: str = "system") -> str:
        entry = {
            "seq": len(self._chain),
            "session_id": session_id,
            "agent_id": agent_id,
            "event_type": event_type,
            "principal_id": principal_id,
            "data": data,
            "timestamp": time.time(),
            "prev_hash": self._last_hash,
        }
        entry_bytes = json.dumps(entry, sort_keys=True, default=str).encode()
        entry_hash = hmac.new(self._secret, entry_bytes, hashlib.sha256).hexdigest()
        entry["hash"] = entry_hash
        self._chain.append(entry)
        self._last_hash = entry_hash
        return entry_hash

    def verify_chain(self) -> bool:
        """Verify the entire chain is unmodified."""
        prev = "genesis"
        for entry in self._chain:
            stored_hash = entry.pop("hash", "")
            entry_bytes = json.dumps(entry, sort_keys=True, default=str).encode()
            expected = hmac.new(self._secret, entry_bytes, hashlib.sha256).hexdigest()
            entry["hash"] = stored_hash
            if stored_hash != expected:
                return False
            if entry["prev_hash"] != prev:
                return False
            prev = stored_hash
        return True

    def get_session_log(self, session_id: str) -> list[dict]:
        return [e for e in self._chain if e["session_id"] == session_id]


# Module-level singleton
_ledger: Optional[AuditLedger] = None


def get_ledger() -> AuditLedger:
    global _ledger
    if _ledger is None:
        _ledger = AuditLedger()
    return _ledger
