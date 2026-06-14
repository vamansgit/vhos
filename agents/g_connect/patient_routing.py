"""Agent 4: Patient Routing Agent — thin wrapper over IntentIdentifier, routes to agents."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent

EMERGENCY_KEYWORDS = [
    "chest pain", "can't breathe", "heart attack", "stroke", "unconscious",
    "bleeding", "not breathing", "dying", "faint", "severe pain", "emergency",
    "anaphylaxis", "seizure", "overdose", "suicide", "kill myself",
]

INTENT_ROUTING = {
    "appointment": "scheduling",
    "book": "scheduling",
    "schedule": "scheduling",
    "reschedule": "scheduling",
    "cancel appointment": "scheduling",
    "insurance": "insurance_tpa",
    "coverage": "insurance_tpa",
    "claim": "insurance_tpa",
    "tpa": "insurance_tpa",
    "symptom": "triage",
    "pain": "triage",
    "sick": "triage",
    "fever": "triage",
    "hurt": "triage",
    "medication": "medicine_adherence",
    "medicine": "medicine_adherence",
    "tablet": "medicine_adherence",
    "prescription": "medicine_adherence",
    "doctor": "access_query",
    "department": "access_query",
    "timing": "access_query",
    "direction": "access_query",
    "record": "medical_records",
    "discharge": "medical_records",
    "report": "medical_records",
}


class PatientRoutingAgent(VhosAgent):
    agent_id = "patient_routing"
    pillar = "g_connect"
    domain = "experience"
    registered_intents = ["Detect_Initial_Intent", "Route_Department", "Initiate_Handoff"]
    required_auth_level = AuthLevel.NONE
    fallback_safe = True
    streaming_voice_compatible = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.88
    ESC_MAX = 0.04
    OPENING_STATEMENT = (
        "Hello! I'm VHOS, the virtual hospital assistant. "
        "I can help you with appointments, information, insurance, or connect you to the right service. "
        "How can I help you today?"
    )

    async def execute(self, ctx: SessionContextBlock) -> None:
        msg = ctx.last_user_message().lower()

        # Emergency check — highest priority, <800ms
        for kw in EMERGENCY_KEYWORDS:
            if kw in msg:
                ctx.response_in_progress.text = (
                    "I can see this may be an emergency. Please call emergency services (112) immediately. "
                    "I'm connecting you to our emergency team right now."
                )
                self._escalate(ctx, reason=f"Emergency keyword detected: '{kw}'", target="emergency_escalation")
                await self.return_control(ctx)
                return

        # Route to appropriate agent
        target_agent = None
        for keyword, agent in INTENT_ROUTING.items():
            if keyword in msg:
                target_agent = agent
                break

        if not target_agent:
            # Ask one clarifying question
            if not ctx.agent_workspace.scratch.get("asked_clarify"):
                response = (
                    "I can help you with:\n"
                    "• Appointments (book, reschedule, cancel)\n"
                    "• Hospital information (doctors, departments, timings)\n"
                    "• Insurance & claims\n"
                    "• Symptoms & triage\n"
                    "• Medications & care\n"
                    "What would you like help with?"
                )
                ctx.agent_workspace.scratch["asked_clarify"] = True
                self._set_response(ctx, response)
            else:
                # Default to human after one clarifying question with no match
                self._handback(ctx, reason="Could not determine intent after clarification", next_intent="human_front_desk")
                ctx.response_in_progress.text = (
                    "I'm connecting you to our front desk team who can assist you further. "
                    "Please hold for a moment."
                )
        else:
            ctx.response_in_progress.text = f"Let me connect you to the right team for that."
            self._handback(ctx, reason=f"Routing to {target_agent}", next_intent=target_agent)

        await self.return_control(ctx)
