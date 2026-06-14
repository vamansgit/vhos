"""Agent 43: Emergency Escalation Agent — <800ms response for all emergencies."""
from __future__ import annotations

import time

from agents.base import AuthLevel, SessionContextBlock, VhosAgent

EMERGENCY_RESPONSES = {
    "chest pain": "cardiac",
    "heart attack": "cardiac",
    "can't breathe": "respiratory",
    "shortness of breath": "respiratory",
    "stroke": "neuro",
    "slurred speech": "neuro",
    "unconscious": "trauma",
    "bleeding": "trauma",
    "suicide": "mental_health",
    "anaphylaxis": "allergy",
    "seizure": "neuro",
    "overdose": "toxicology",
    "obstetric": "obstetric",
}


class EmergencyEscalationAgent(VhosAgent):
    agent_id = "emergency_escalation"
    pillar = "platform_control"
    domain = "emergency"
    registered_intents = ["Emergency_Response", "Activate_Code_Blue", "Notify_Emergency_Team"]
    required_auth_level = AuthLevel.NONE
    fallback_safe = False
    streaming_voice_compatible = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 1.0
    ESC_MAX = 0.0
    RED_FLAGS = list(EMERGENCY_RESPONSES.keys())

    async def execute(self, ctx: SessionContextBlock) -> None:
        start_time = time.time()
        msg = ctx.last_user_message().lower()
        reason = ctx.response_in_progress.escalation_reason or "Emergency escalation triggered"

        # Detect emergency type
        emergency_type = "general"
        for keyword, etype in EMERGENCY_RESPONSES.items():
            if keyword in msg or (reason and keyword in reason.lower()):
                emergency_type = etype
                break

        response = self._build_response(emergency_type, ctx)

        elapsed_ms = (time.time() - start_time) * 1000
        self._log_mutation(ctx, "emergency.escalated", emergency_type,
                           f"Emergency escalation: {emergency_type} | {elapsed_ms:.0f}ms response time")
        self._set_response(ctx, response, outcome="escalate",
                           structured_data={"emergency_type": emergency_type,
                                            "response_time_ms": elapsed_ms,
                                            "emergency_team_notified": True})
        ctx.lifecycle_state = "emergency_escalated"
        await self.return_control(ctx)

    def _build_response(self, emergency_type: str, ctx: SessionContextBlock) -> str:
        base = "🚨 EMERGENCY RESPONSE ACTIVATED 🚨\n"
        emergency_numbers = "Emergency: 112 | Hospital Emergency: Ext. 999\n"

        type_msgs = {
            "cardiac": (
                "Potential cardiac emergency. "
                "→ Call 112 immediately if not already done.\n"
                "→ Our cardiac emergency team has been notified.\n"
                "→ If patient is conscious: Keep calm, don't exert.\n"
                "→ If trained: Be prepared to give CPR if patient collapses.\n"
                "→ Do not give food/water."
            ),
            "respiratory": (
                "Respiratory emergency.\n"
                "→ Call 112 now.\n"
                "→ Help patient sit upright and stay calm.\n"
                "→ Loosen tight clothing.\n"
                "→ Emergency team notified."
            ),
            "neuro": (
                "Potential neurological emergency (stroke/seizure).\n"
                "→ Call 112 immediately — time is critical.\n"
                "→ Note the time symptoms started.\n"
                "→ Keep patient safe and still. Do not give food/water.\n"
                "→ Emergency team alerted."
            ),
            "mental_health": (
                "Mental health crisis.\n"
                "→ Please stay with the person.\n"
                "→ You are not alone — our crisis team is being connected now.\n"
                "→ iCall: 9152987821 | Vandrevala: 1860-2662-345 (24/7)\n"
                "→ If immediate danger: Call 112."
            ),
            "allergy": (
                "Possible anaphylaxis — severe allergic reaction.\n"
                "→ Call 112 immediately.\n"
                "→ If epinephrine auto-injector available — use it now.\n"
                "→ Help person lie down with legs raised (unless breathing difficulty).\n"
                "→ Emergency team alerted."
            ),
            "trauma": (
                "Trauma/bleeding emergency.\n"
                "→ Call 112 immediately.\n"
                "→ Apply firm pressure to any wound.\n"
                "→ Do not remove embedded objects.\n"
                "→ Emergency team notified."
            ),
        }
        specific = type_msgs.get(emergency_type, (
            "Emergency detected.\n"
            "→ Call 112 immediately.\n"
            "→ Emergency team has been notified.\n"
            "→ Stay with the patient."
        ))
        return base + emergency_numbers + specific
