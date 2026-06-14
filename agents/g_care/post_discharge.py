"""Agent 13: Post-Discharge Care Agent."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent

RED_FLAG_SYMPTOMS = {
    "cardiac": ["chest pain", "breathlessness at rest", "ankle swelling", "palpitations", "can't breathe"],
    "orthopaedic": ["calf pain", "calf swelling", "wound discharge", "fever"],
    "appendectomy": ["wound", "dehiscence", "fever", "abdominal rigidity", "abdominal pain"],
    "general": ["severe pain", "high fever", "bleeding", "loss of consciousness", "confusion"],
}


class PostDischargeAgent(VhosAgent):
    agent_id = "post_discharge"
    pillar = "g_care"
    domain = "engagement"
    registered_intents = ["Post_Discharge_Check", "Wound_Care_Reminder", "Red_Flag_Symptom_Check", "Readmission_Prevention_Outreach"]
    required_auth_level = AuthLevel.MEDIUM
    fallback_safe = True
    mdsw_scope = "Pending CDSCO SaMD — advisory only"
    KPI_TARGET = 0.78
    ESC_MAX = 0.12

    def _check_red_flags_by_procedure(self, msg: str, procedure: str) -> list[str]:
        proc_lower = procedure.lower()
        flags = []
        for category, keywords in RED_FLAG_SYMPTOMS.items():
            if category in proc_lower or category == "general":
                for kw in keywords:
                    if kw in msg.lower():
                        flags.append(kw)
        return flags

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message()
        pv = ctx.context.patient_view
        procedure = pv.get("procedure", "general")

        # Red flag check — ALWAYS before anything else
        red_flags = self._check_red_flags_by_procedure(msg, procedure)
        if red_flags:
            self._handback(ctx, reason=f"Red flag symptoms: {red_flags}", next_intent="triage")
            ctx.response_in_progress.text = (
                f"I'm concerned about what you've described — {', '.join(red_flags)}. "
                "I'm connecting you immediately to our triage team. Please stay on the line. "
                "If you feel this is an emergency, please call 112 right now."
            )
            await self.return_control(ctx)
            return

        intent = ctx.goal

        if intent == "Wound_Care_Reminder" or "wound" in msg.lower() or "dressing" in msg.lower():
            await self._wound_care(ctx)
        elif intent == "Readmission_Prevention_Outreach" or "come back" in msg.lower():
            await self._readmission_prevention(ctx)
        elif intent == "Red_Flag_Symptom_Check":
            await self._red_flag_check(ctx, procedure)
        else:
            await self._post_discharge_check(ctx)

        await self.return_control(ctx)

    async def _post_discharge_check(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        name = pv.get("name", "")
        discharge_day = pv.get("discharge_day_number", 1)
        procedure = pv.get("procedure", "your procedure")
        response = (
            f"Hello{', ' + name if name else ''}. "
            f"This is your Day {discharge_day} post-discharge check after {procedure}. "
            "A few quick questions:\n"
            "1. Have you been able to get all your prescribed medications?\n"
            "2. How would you describe your wound/incision site — any redness, swelling, or discharge?\n"
            "3. Any unusual pain or fever since discharge?\n"
            "Please take your time answering."
        )
        self._set_response(ctx, response)

    async def _wound_care(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        day = pv.get("post_procedure_day", 5)
        procedure = pv.get("procedure", "your procedure")
        response = (
            f"Day {day} wound care reminder for {procedure}: "
            "Keep the wound dry and clean. Change dressing as instructed by your nurse. "
            "Watch for: redness spreading beyond the wound edges, warmth, discharge, or fever above 38°C. "
            "If you notice any of these — call us immediately or go to the nearest emergency department."
        )
        self._set_response(ctx, response)

    async def _red_flag_check(self, ctx: SessionContextBlock, procedure: str):
        flags_to_check = RED_FLAG_SYMPTOMS.get(
            next((k for k in RED_FLAG_SYMPTOMS if k in procedure.lower()), "general"), []
        )
        response = (
            f"I need to ask you a few important questions about your recovery from {procedure}. "
            "Are you experiencing any of the following?\n"
            + "\n".join(f"• {f.capitalize()}" for f in flags_to_check[:5])
            + "\nPlease answer yes or no for each."
        )
        self._set_response(ctx, response)

    async def _readmission_prevention(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        doctor = pv.get("treating_doctor", "your doctor")
        response = (
            "Based on your recovery progress, I'd recommend a follow-up visit with your care team. "
            f"Shall I book an urgent follow-up appointment with {doctor}?"
        )
        self._set_response(ctx, response, next_intent="Book_Appointment")
