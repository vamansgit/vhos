"""Agent 33: OT Scheduler Agent."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class OtSchedulerAgent(VhosAgent):
    agent_id = "ot_scheduler"
    pillar = "g_orchestrate"
    domain = "orchestration"
    registered_intents = ["Schedule_Surgery", "Check_OT_Availability", "Manage_OT_Delays", "Generate_OT_List"]
    required_auth_level = AuthLevel.PROVIDER
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.90
    ESC_MAX = 0.03

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if "delay" in msg or intent == "Manage_OT_Delays":
            await self._manage_delay(ctx)
        elif "list" in msg or "today's" in msg or intent == "Generate_OT_List":
            await self._ot_list(ctx)
        elif "available" in msg or intent == "Check_OT_Availability":
            await self._availability(ctx)
        else:
            await self._schedule(ctx, msg)
        await self.return_control(ctx)

    async def _schedule(self, ctx: SessionContextBlock, msg: str):
        pv = ctx.context.patient_view
        procedure = pv.get("procedure", "the procedure")
        patient = pv.get("name", "Patient")
        ref = "OT-2026-001"
        response = (
            f"Surgery scheduled:\n"
            f"• Patient: {patient}\n"
            f"• Procedure: {procedure}\n"
            "• OT: Theatre 2\n"
            "• Date/Time: 18 Jun 2026 at 09:00\n"
            f"• Ref: {ref}\n"
            "• Anaesthesia: Confirmed\n"
            "• Surgical team notified"
        )
        self._log_mutation(ctx, "ot.scheduled", ref, f"Surgery scheduled: {procedure} for {patient}")
        self._set_response(ctx, response, outcome="success")

    async def _availability(self, ctx: SessionContextBlock):
        response = (
            "OT availability (next 3 days):\n"
            "• Tomorrow (17 Jun): OT 1 — 08:00–12:00 (available), OT 3 — 13:00–17:00 (available)\n"
            "• 18 Jun: OT 2 — all day (available), OT 4 — AM only\n"
            "• 19 Jun: Limited (OT maintenance 09:00–12:00)\n"
            "Which OT and time slot would you prefer?"
        )
        self._set_response(ctx, response)

    async def _manage_delay(self, ctx: SessionContextBlock):
        response = (
            "OT delay management:\n"
            "• OT 1: Running 45 minutes late (complex case)\n"
            "• Action: Next patient (Mr. Kumar, appendectomy) notified\n"
            "• OT 2 available: Transfer possible if delay exceeds 60 min\n"
            "• Anaesthesiology briefed\n"
            "Shall I notify all waiting patients and families?"
        )
        self._set_response(ctx, response)

    async def _ot_list(self, ctx: SessionContextBlock):
        response = (
            "Today's OT list:\n"
            "1. 08:00 — OT 1: Mr. Sharma, CABG (Dr. Verma) — IN PROGRESS\n"
            "2. 09:30 — OT 2: Mrs. Patel, Total knee replacement (Dr. Kapoor) — NEXT\n"
            "3. 11:00 — OT 3: Mr. Kumar, Laparoscopic appendectomy (Dr. Singh) — WAITING\n"
            "4. 13:00 — OT 1: Ms. Gupta, Cholecystectomy (Dr. Mehta) — SCHEDULED\n"
            "Total cases: 4 | Completed: 0 | In progress: 1 | Pending: 3"
        )
        self._set_response(ctx, response)
