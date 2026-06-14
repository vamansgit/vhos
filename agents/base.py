"""VHOS Agent Base — Orchestrator-Agent Contract v2.4"""
from __future__ import annotations

import hashlib
import hmac
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class AuthLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PROVIDER = "provider"

    @classmethod
    def rank(cls, level: "AuthLevel") -> int:
        order = [cls.NONE, cls.LOW, cls.MEDIUM, cls.HIGH, cls.PROVIDER]
        return order.index(level)


@dataclass
class AuthPrincipal:
    principal_id: str
    auth_level: AuthLevel
    verified_at: float = field(default_factory=time.time)
    identity_claims: dict = field(default_factory=dict)
    tenant_id: str = ""


@dataclass
class ContextView:
    patient_view: dict = field(default_factory=dict)
    hospital_view: dict = field(default_factory=dict)


@dataclass
class ConversationDirectives:
    language: str = "en"
    voice_mode: bool = False
    max_turns: int = 20
    tts_provider: str = "sarvam"
    stt_provider: str = "sarvam"


@dataclass
class RegulationInstruction:
    regulation_id: str
    rule: str
    applies_to: list[str] = field(default_factory=list)


@dataclass
class GuardrailInstruction:
    guardrail_id: str
    rule: str
    action: str = "block"
    applies_to_agents: list[str] = field(default_factory=list)


@dataclass
class IntegrationPermission:
    integration_id: str
    permitted_operations: list[str] = field(default_factory=list)


@dataclass
class DataWriteDeclaration:
    target: str
    operation: str
    idempotency_key_fields: list[str] = field(default_factory=list)
    compensating_action: Optional["DataWriteDeclaration"] = None
    reason_template: str = ""


@dataclass
class ResponseInProgress:
    text: str = ""
    structured_data: dict = field(default_factory=dict)
    voice_ssml: Optional[str] = None
    next_intent_hint: Optional[str] = None
    outcome: Optional[str] = None  # "success" | "handback" | "escalate" | "error"
    escalation_target: Optional[str] = None
    escalation_reason: Optional[str] = None
    draft_resources: list[dict] = field(default_factory=list)
    requires_confirmation: bool = False
    confirmation_prompt: Optional[str] = None


@dataclass
class AgentWorkspace:
    scratch: dict = field(default_factory=dict)
    fetched_resources: dict = field(default_factory=dict)
    pending_sagas: list[dict] = field(default_factory=list)


@dataclass
class MutationEntry:
    author: str
    field: str
    value: str
    reason: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class ConversationTurn:
    role: str  # "user" | "agent"
    text: str
    timestamp: float = field(default_factory=time.time)
    intent: Optional[str] = None
    agent_id: Optional[str] = None


@dataclass
class SessionContextBlock:
    session_id: str
    tenant_id: str
    capability_token: str
    principal: AuthPrincipal
    goal: str
    context: ContextView = field(default_factory=ContextView)
    regulations: list[RegulationInstruction] = field(default_factory=list)
    guardrails: list[GuardrailInstruction] = field(default_factory=list)
    conversation_directives: ConversationDirectives = field(default_factory=ConversationDirectives)
    integrations_allowed: list[IntegrationPermission] = field(default_factory=list)
    conversation_history: list[ConversationTurn] = field(default_factory=list)
    agent_workspace: AgentWorkspace = field(default_factory=AgentWorkspace)
    response_in_progress: ResponseInProgress = field(default_factory=ResponseInProgress)
    context_pending_data_requests: list[dict] = field(default_factory=list)
    mutation_log: list[MutationEntry] = field(default_factory=list)
    lifecycle_state: str = "active"
    created_at: float = field(default_factory=time.time)
    current_agent_id: Optional[str] = None

    def add_turn(self, role: str, text: str, intent: str = None, agent_id: str = None):
        self.conversation_history.append(
            ConversationTurn(role=role, text=text, intent=intent, agent_id=agent_id)
        )

    def last_user_message(self) -> str:
        for turn in reversed(self.conversation_history):
            if turn.role == "user":
                return turn.text
        return self.goal


class VhosAgent(ABC):
    agent_id: str = ""
    pillar: str = ""
    domain: str = ""
    registered_intents: list[str] = []
    required_auth_level: AuthLevel = AuthLevel.NONE
    required_context_fields: list[str] = []
    lazy_fetchable_fields: list[str] = []
    data_writes: list[DataWriteDeclaration] = []
    fallback_safe: bool = True
    streaming_voice_compatible: bool = True
    mdsw_scope: str = "Not a medical device"
    RED_FLAGS: list[str] = []
    OPENING_STATEMENT: str = ""
    CLOSING_SUCCESS: str = ""
    KPI_TARGET: float = 0.85
    ESC_MAX: float = 0.05

    @abstractmethod
    async def execute(self, ctx: SessionContextBlock) -> None:
        """Validate block, dispatch to intent handler, write response, call return_control()."""

    def validate_block(self, ctx: SessionContextBlock) -> Optional[str]:
        """Returns error message if block is invalid, else None."""
        if not self._validate_auth(ctx):
            return (
                f"I need to verify your identity before I can help with that. "
                f"This service requires {self.required_auth_level.value}-level authentication."
            )
        for field_name in self.required_context_fields:
            parts = field_name.split(".")
            obj = ctx.context
            try:
                for part in parts:
                    obj = getattr(obj, part, None) or (obj.get(part) if isinstance(obj, dict) else None)
                if obj is None:
                    return f"Required context '{field_name}' is not available for this session."
            except Exception:
                pass
        return None

    def _validate_auth(self, ctx: SessionContextBlock) -> bool:
        return AuthLevel.rank(ctx.principal.auth_level) >= AuthLevel.rank(self.required_auth_level)

    def _check_red_flags(self, text: str) -> bool:
        """Returns True if any red flag keyword found in text."""
        text_lower = text.lower()
        return any(flag.lower() in text_lower for flag in self.RED_FLAGS)

    def _log_mutation(self, ctx: SessionContextBlock, field: str, value: Any, reason: str):
        ctx.mutation_log.append(
            MutationEntry(author=self.agent_id, field=field, value=str(value), reason=reason)
        )

    def _set_response(self, ctx: SessionContextBlock, text: str, outcome: str = "success",
                      structured_data: dict = None, next_intent: str = None):
        ctx.response_in_progress.text = text
        ctx.response_in_progress.outcome = outcome
        if structured_data:
            ctx.response_in_progress.structured_data = structured_data
        if next_intent:
            ctx.response_in_progress.next_intent_hint = next_intent

    def _escalate(self, ctx: SessionContextBlock, reason: str, target: str = "emergency_escalation"):
        ctx.response_in_progress.outcome = "escalate"
        ctx.response_in_progress.escalation_target = target
        ctx.response_in_progress.escalation_reason = reason
        ctx.lifecycle_state = "escalating"
        self._log_mutation(ctx, "lifecycle_state", "escalating", f"Emergency escalation: {reason}")

    def _handback(self, ctx: SessionContextBlock, reason: str, next_intent: str = None):
        ctx.response_in_progress.outcome = "handback"
        ctx.response_in_progress.next_intent_hint = next_intent
        ctx.response_in_progress.escalation_reason = reason

    async def return_control(self, ctx: SessionContextBlock):
        if ctx.lifecycle_state == "active":
            ctx.lifecycle_state = "returned"
        ctx.add_turn(
            role="agent",
            text=ctx.response_in_progress.text,
            agent_id=self.agent_id
        )
