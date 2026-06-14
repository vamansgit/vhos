"""Session store — in-memory with optional Redis backend."""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict
from typing import Optional

from agents.base import (AuthLevel, AuthPrincipal, ConversationDirectives,
                          ContextView, SessionContextBlock)
from config import settings


def _make_session(tenant_id: str, goal: str, auth_level: str = "none",
                   principal_id: str = "anonymous", patient_view: dict = None,
                   hospital_view: dict = None) -> SessionContextBlock:
    session_id = str(uuid.uuid4())
    principal = AuthPrincipal(
        principal_id=principal_id,
        auth_level=AuthLevel(auth_level) if auth_level in [e.value for e in AuthLevel] else AuthLevel.NONE,
        verified_at=time.time(),
    )
    context = ContextView(
        patient_view=patient_view or {},
        hospital_view=hospital_view or {"name": "VHOS Hospital", "tenant_id": tenant_id},
    )
    from vhos_platform.orchestrator.authn.module import AuthnModule
    authn = AuthnModule()
    cap_token = authn.issue_capability_token(session_id, "orchestrator", principal_id, principal.auth_level)
    return SessionContextBlock(
        session_id=session_id,
        tenant_id=tenant_id,
        capability_token=cap_token,
        principal=principal,
        goal=goal,
        context=context,
    )


class SessionStore:
    """In-memory session store. Production: backed by Redis cluster."""

    def __init__(self):
        self._sessions: dict[str, SessionContextBlock] = {}
        self._ttl: dict[str, float] = {}
        self._redis = None
        self._try_redis()

    def _try_redis(self):
        try:
            import redis
            r = redis.from_url(settings.redis_url, socket_connect_timeout=2)
            r.ping()
            self._redis = r
        except Exception:
            self._redis = None

    def create(self, tenant_id: str, goal: str, auth_level: str = "none",
                principal_id: str = "anonymous", patient_view: dict = None,
                hospital_view: dict = None) -> SessionContextBlock:
        ctx = _make_session(tenant_id, goal, auth_level, principal_id, patient_view, hospital_view)
        self._sessions[ctx.session_id] = ctx
        self._ttl[ctx.session_id] = time.time() + settings.session_ttl_seconds
        return ctx

    def get(self, session_id: str) -> Optional[SessionContextBlock]:
        self._evict_expired()
        return self._sessions.get(session_id)

    def save(self, ctx: SessionContextBlock) -> None:
        self._sessions[ctx.session_id] = ctx
        self._ttl[ctx.session_id] = time.time() + settings.session_ttl_seconds

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        self._ttl.pop(session_id, None)

    def _evict_expired(self):
        now = time.time()
        expired = [sid for sid, t in self._ttl.items() if t < now]
        for sid in expired:
            self._sessions.pop(sid, None)
            self._ttl.pop(sid, None)

    def list_sessions(self) -> list[str]:
        self._evict_expired()
        return list(self._sessions.keys())
