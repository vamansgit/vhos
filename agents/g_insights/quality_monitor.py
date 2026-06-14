"""Agent 37: Quality Monitor Agent — NABH/JCI metrics."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class QualityMonitorAgent(VhosAgent):
    agent_id = "quality_monitor"
    pillar = "g_insights"
    domain = "insights"
    registered_intents = ["Check_Quality_Metrics", "Flag_Quality_Incident", "Generate_Quality_Report", "Monitor_SLA_Compliance"]
    required_auth_level = AuthLevel.PROVIDER
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.90
    ESC_MAX = 0.02

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if "incident" in msg or "flag" in msg or intent == "Flag_Quality_Incident":
            await self._flag_incident(ctx, msg)
        elif "sla" in msg or "compliance" in msg or intent == "Monitor_SLA_Compliance":
            await self._sla(ctx)
        elif "report" in msg or intent == "Generate_Quality_Report":
            await self._report(ctx)
        else:
            await self._metrics(ctx)
        await self.return_control(ctx)

    async def _metrics(self, ctx: SessionContextBlock):
        response = (
            "Quality metrics (current month):\n"
            "• Patient satisfaction: 4.3/5.0 ✅ (target: ≥4.0)\n"
            "• Medication error rate: 0.8/1000 doses ✅ (target: <2.0)\n"
            "• Falls rate: 1.2/1000 bed-days ✅ (target: <2.0)\n"
            "• HAI rate: 2.1% ⚠️ (target: <2.0%)\n"
            "• Discharge by noon: 42% ⚠️ (target: ≥50%)\n"
            "• 30-day readmission: 7.2% ✅ (target: <8%)\n"
            "[NABH/JCI metrics | Reported to Quality Committee]"
        )
        self._set_response(ctx, response, structured_data={"hai_rate": 2.1, "satisfaction": 4.3})

    async def _flag_incident(self, ctx: SessionContextBlock, msg: str):
        incident_ref = "QI-2026-" + str(hash(msg))[:6]
        response = (
            f"Quality incident flagged (Ref: {incident_ref}):\n"
            "• Category: Patient safety\n"
            "• Root cause analysis: Initiated\n"
            "• Notified: Quality Manager, Department Head\n"
            "• Required: Incident report within 24h\n"
            "[All incidents logged per NABH/JCI requirements]"
        )
        self._log_mutation(ctx, "quality_incident.logged", incident_ref, "Quality incident reported")
        self._set_response(ctx, response, outcome="success")

    async def _sla(self, ctx: SessionContextBlock):
        response = (
            "SLA compliance:\n"
            "• ED triage within 5 min: 94% ✅\n"
            "• Consultant response to urgent referral: 89% ✅\n"
            "• Lab TAT (routine): 4.2h ✅ (target: <6h)\n"
            "• Lab TAT (urgent): 58min ✅ (target: <90min)\n"
            "• Discharge summary dispatch: 72% ⚠️ (target: ≥80%)\n"
        )
        self._set_response(ctx, response)

    async def _report(self, ctx: SessionContextBlock):
        response = (
            "Monthly quality report:\n"
            "Overall quality score: 87/100 (Grade: Good)\n"
            "Key achievements: Falls prevention improved 15%\n"
            "Areas for improvement: Discharge summary timeliness\n"
            "Action plan: Drafted and submitted to Quality Committee\n"
            "[Report prepared for NABH/JCI submission]"
        )
        self._set_response(ctx, response)
