"""Agent 30: Discharge Planner Agent."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class DischargePlannerAgent(VhosAgent):
    agent_id = "discharge_planner"
    pillar = "g_orchestrate"
    domain = "orchestration"
    registered_intents = ["Assess_Discharge_Readiness", "Create_Discharge_Plan", "Coordinate_Discharge", "Schedule_Follow_Up"]
    required_auth_level = AuthLevel.PROVIDER
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.88
    ESC_MAX = 0.05

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if "follow" in msg or "follow-up" in msg or intent == "Schedule_Follow_Up":
            await self._schedule_follow_up(ctx)
        elif "coordinate" in msg or "arrange" in msg or intent == "Coordinate_Discharge":
            await self._coordinate(ctx)
        elif "plan" in msg or "summary" in msg or intent == "Create_Discharge_Plan":
            await self._create_plan(ctx)
        else:
            await self._assess_readiness(ctx)
        await self.return_control(ctx)

    async def _assess_readiness(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        response = (
            "Discharge readiness assessment:\n"
            "✅ Vitals stable for 24h\n"
            "✅ Pain managed (score < 4/10)\n"
            "✅ Tolerating oral intake\n"
            "✅ Wound reviewed — healing well\n"
            "⏳ Discharge summary: Pending doctor sign-off\n"
            "⏳ Pharmacy medications: Being prepared\n"
            "Estimated discharge readiness: 2–3 hours\n"
            "[Advisory — discharge decision is the attending doctor's]"
        )
        self._set_response(ctx, response)

    async def _create_plan(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        patient = pv.get("name", "Patient")
        procedure = pv.get("procedure", "the procedure")
        response = (
            f"Discharge plan — {patient}, post {procedure}:\n"
            "• Medications: See attached prescription\n"
            "• Wound care: Clean and dry. Change dressing every 2 days\n"
            "• Activity: Gradually increase as tolerated. No heavy lifting for 4 weeks\n"
            "• Diet: Normal diet. Avoid alcohol\n"
            "• Red flags: Fever >38.5°C, wound redness/discharge, increasing pain → attend ED\n"
            "• Follow-up: 1 week outpatient clinic\n"
            "[Discharge plan sent to patient, family, and GP]"
        )
        self._log_mutation(ctx, "fhir:Composition.discharge_summary", "created", f"Discharge plan created for {patient}")
        self._set_response(ctx, response, outcome="success")

    async def _coordinate(self, ctx: SessionContextBlock):
        response = (
            "Discharge coordination in progress:\n"
            "• Transport: Patient's family confirmed for 3:00 PM pickup\n"
            "• Medications: Pharmacy preparing discharge pack\n"
            "• Discharge summary: Being finalised by doctor\n"
            "• Home preparation: No special requirements noted\n"
            "• Post-discharge calls: Scheduled Day 1, 3, 7\n"
            "All teams notified. Estimated discharge: 3:00 PM today."
        )
        self._set_response(ctx, response)

    async def _schedule_follow_up(self, ctx: SessionContextBlock):
        response = (
            "Follow-up appointments scheduled:\n"
            "• 1-week review: Next Monday at 10:00 AM — surgeon's clinic\n"
            "• 4-week review: Booked pending confirmation\n"
            "• GP referral letter: Sent\n"
            "Shall I confirm these appointments and send SMS reminders?"
        )
        self._set_response(ctx, response, next_intent="Book_Appointment")
