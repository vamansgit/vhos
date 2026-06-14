"""Master Orchestrator — the central coordinator for all VHOS sessions."""
from __future__ import annotations

import time
import uuid
from typing import Optional

from agents.base import SessionContextBlock
from agents.registry import get as get_agent, list_agents
from vhos_platform.orchestrator.audit.ledger import get_ledger
from vhos_platform.orchestrator.authn.module import AuthnModule
from vhos_platform.orchestrator.context.store import SessionStore
from vhos_platform.orchestrator.guardrails.catalogue import GuardrailsCatalogue
from vhos_platform.orchestrator.intent.classifier import IntentClassifier


class MasterOrchestrator:
    """
    VHOS Master Orchestrator v2.4.
    Handles: session lifecycle, intent classification, agent dispatch,
    guardrail enforcement, audit logging.
    """

    def __init__(self, use_llm_intent: bool = False):
        self.session_store = SessionStore()
        self.intent_classifier = IntentClassifier(use_llm=use_llm_intent)
        self.authn = AuthnModule()
        self.guardrails = GuardrailsCatalogue()
        self.audit = get_ledger()

    def create_session(self, tenant_id: str = "default", auth_level: str = "none",
                        principal_id: str = "anonymous", patient_view: dict = None,
                        hospital_view: dict = None) -> dict:
        """Create a new session and return session info."""
        ctx = self.session_store.create(
            tenant_id=tenant_id,
            goal="greeting",
            auth_level=auth_level,
            principal_id=principal_id,
            patient_view=patient_view or {},
            hospital_view=hospital_view or {},
        )
        self.audit.append(ctx.session_id, "orchestrator", "session_created",
                          {"tenant_id": tenant_id, "auth_level": auth_level},
                          principal_id=principal_id)
        return {
            "session_id": ctx.session_id,
            "capability_token": ctx.capability_token,
            "created_at": ctx.created_at,
        }

    async def process_message(self, session_id: str, message: str,
                               auth_level: Optional[str] = None) -> dict:
        """Process a user message and return the agent's response."""
        ctx = self.session_store.get(session_id)
        if ctx is None:
            return {"error": "Session not found or expired", "session_id": session_id}

        # Add user turn
        ctx.add_turn(role="user", text=message)

        # Auth upgrade if provided
        if auth_level:
            try:
                from agents.base import AuthLevel
                ctx.principal.auth_level = AuthLevel(auth_level)
                ctx.principal.verified_at = time.time()
            except ValueError:
                pass

        # Emergency check — bypass intent classification
        message_lower = message.lower()
        emergency_keywords = ["chest pain", "heart attack", "can't breathe", "stroke",
                               "unconscious", "kill myself", "suicide", "bleeding severely",
                               "anaphylaxis", "seizure"]
        if any(kw in message_lower for kw in emergency_keywords):
            intent = "emergency"
            agent_id = "emergency_escalation"
            confidence = 1.0
        else:
            # Classify intent
            intent, confidence = await self.intent_classifier.classify(message, {
                "session_id": session_id,
                "history_length": len(ctx.conversation_history),
            })
            # If routing was already set (handback from previous agent), honor it
            if ctx.response_in_progress.next_intent_hint:
                intended_agent = ctx.response_in_progress.next_intent_hint
                agent_id = intended_agent if get_agent(intended_agent) else self.intent_classifier.route_to_agent(intent)
            else:
                agent_id = self.intent_classifier.route_to_agent(intent)

        ctx.goal = intent
        ctx.current_agent_id = agent_id
        ctx.lifecycle_state = "active"
        ctx.response_in_progress.text = ""
        ctx.response_in_progress.outcome = None
        ctx.response_in_progress.next_intent_hint = None
        ctx.response_in_progress.requires_confirmation = False

        # Audit: intent classified
        self.audit.append(session_id, "orchestrator", "intent_classified",
                          {"intent": intent, "confidence": confidence, "agent": agent_id},
                          principal_id=ctx.principal.principal_id)

        # Dispatch to agent
        agent = get_agent(agent_id)
        if agent is None:
            # Fall back to patient routing
            agent = get_agent("patient_routing")

        if agent is None:
            return {
                "session_id": session_id,
                "text": "I'm sorry, I'm unable to assist with that right now. Please contact the front desk.",
                "outcome": "error",
                "agent_id": "orchestrator",
            }

        try:
            await agent.execute(ctx)
        except Exception as exc:
            ctx.response_in_progress.text = (
                "I'm sorry, I encountered an error. "
                "Please try again or speak to a member of our team."
            )
            ctx.response_in_progress.outcome = "error"
            self.audit.append(session_id, agent_id, "agent_error",
                              {"error": str(exc)[:200]},
                              principal_id=ctx.principal.principal_id)

        # Guardrail check on response
        violations = self.guardrails.check_response(ctx.response_in_progress.text, agent_id)
        if violations:
            self.audit.append(session_id, agent_id, "guardrail_violation",
                              {"violations": violations},
                              principal_id=ctx.principal.principal_id)

        # Audit: response
        self.audit.append(session_id, agent_id, "response",
                          {
                              "outcome": ctx.response_in_progress.outcome,
                              "text_length": len(ctx.response_in_progress.text),
                              "requires_confirmation": ctx.response_in_progress.requires_confirmation,
                          },
                          principal_id=ctx.principal.principal_id)

        # Save session
        self.session_store.save(ctx)

        response = {
            "session_id": session_id,
            "text": ctx.response_in_progress.text,
            "outcome": ctx.response_in_progress.outcome or "success",
            "agent_id": agent_id,
            "intent": intent,
            "confidence": confidence,
            "structured_data": ctx.response_in_progress.structured_data,
        }
        if ctx.response_in_progress.requires_confirmation:
            response["requires_confirmation"] = True
            response["confirmation_prompt"] = ctx.response_in_progress.confirmation_prompt
        if ctx.response_in_progress.draft_resources:
            response["draft_resources"] = ctx.response_in_progress.draft_resources
        if ctx.response_in_progress.escalation_target:
            response["escalation_target"] = ctx.response_in_progress.escalation_target
            response["escalation_reason"] = ctx.response_in_progress.escalation_reason

        return response

    def get_session_status(self, session_id: str) -> dict:
        ctx = self.session_store.get(session_id)
        if ctx is None:
            return {"error": "Session not found"}
        return {
            "session_id": ctx.session_id,
            "lifecycle_state": ctx.lifecycle_state,
            "current_agent": ctx.current_agent_id,
            "turn_count": len(ctx.conversation_history),
            "auth_level": ctx.principal.auth_level.value,
            "goal": ctx.goal,
            "created_at": ctx.created_at,
        }

    def list_agents(self) -> list[dict]:
        return list_agents()

    def get_audit_log(self, session_id: str) -> list[dict]:
        return self.audit.get_session_log(session_id)
