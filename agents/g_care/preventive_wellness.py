"""Agent 10: Preventive Care & Wellness Agent."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class PreventiveWellnessAgent(VhosAgent):
    agent_id = "preventive_wellness"
    pillar = "g_care"
    domain = "engagement"
    registered_intents = ["Schedule_Routine_Checkup", "Send_Health_Reminder", "Provide_Preventive_Advice", "Outreach_Care_Gap"]
    required_auth_level = AuthLevel.MEDIUM
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.75
    ESC_MAX = 0.06

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        # Symptom report → triage
        if any(w in msg for w in ["pain", "sick", "fever", "hurt", "symptom", "unwell"]):
            self._handback(ctx, reason="Symptom reported in wellness check", next_intent="triage")
            ctx.response_in_progress.text = "I'm concerned — let me connect you to our triage team to check on your symptoms."
            await self.return_control(ctx)
            return

        if intent == "Outreach_Care_Gap" or "care gap" in msg or "overdue" in msg:
            await self._outreach_care_gap(ctx)
        elif intent == "Send_Health_Reminder" or "reminder" in msg or "vaccination" in msg:
            await self._send_reminder(ctx)
        elif intent == "Schedule_Routine_Checkup" or "checkup" in msg or "routine" in msg:
            await self._schedule_checkup(ctx)
        else:
            await self._provide_advice(ctx, msg)
        await self.return_control(ctx)

    async def _schedule_checkup(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        doctor = pv.get("primary_physician", "your doctor")
        response = (
            f"It looks like you may be due for your annual health check-up. "
            f"{doctor.title() if not doctor.startswith('Dr') else doctor} recommends regular screenings. "
            "Shall I check available slots and book one for you?"
        )
        self._set_response(ctx, response, next_intent="Check_Availability")

    async def _send_reminder(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        age = pv.get("age", 45)
        gender = pv.get("gender", "unknown")
        reminders = ["Annual HbA1c test", "Blood pressure check"]
        if int(age) > 40:
            reminders.append("Lipid profile screening")
        if gender.lower() == "female":
            reminders.append("Mammogram screening")
            reminders.append("Pap smear (if overdue)")
        response = (
            "Based on your health profile, the following screenings are recommended:\n"
            + "\n".join(f"• {r}" for r in reminders)
            + "\nWould you like to book any of these?"
        )
        self._set_response(ctx, response, next_intent="Book_Appointment")

    async def _provide_advice(self, ctx: SessionContextBlock, msg: str):
        response = (
            "Here's some general preventive health guidance:\n"
            "• Annual health check-ups help detect issues early\n"
            "• Stay up to date with vaccinations\n"
            "• Regular exercise (150 min/week moderate intensity)\n"
            "• Healthy diet rich in vegetables and whole grains\n"
            "For personalised advice, please speak to your doctor. "
            "[This is general wellness information, not medical advice]"
        )
        self._set_response(ctx, response)

    async def _outreach_care_gap(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        doctor = pv.get("treating_doctor", "Dr. Mehta")
        gap = pv.get("care_gap_description", "6-month HbA1c check")
        months_overdue = pv.get("months_overdue", 8)
        response = (
            f"{doctor} noted you're due for your {gap} — it's been {months_overdue} months. "
            "Shall I book that for you now? It only takes a moment."
        )
        self._set_response(ctx, response, next_intent="Book_Appointment")
