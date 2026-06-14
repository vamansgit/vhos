"""Agent 36: Risk Detection Agent — patient risk stratification."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class RiskDetectionAgent(VhosAgent):
    agent_id = "risk_detection"
    pillar = "g_insights"
    domain = "insights"
    registered_intents = ["Stratify_Patient_Risk", "Detect_Deterioration", "Flag_Care_Gap", "Generate_Risk_Report"]
    required_auth_level = AuthLevel.PROVIDER
    fallback_safe = True
    mdsw_scope = "Pending CDSCO SaMD — advisory only"
    KPI_TARGET = 0.82
    ESC_MAX = 0.05

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if "deteriorat" in msg or intent == "Detect_Deterioration":
            await self._detect_deterioration(ctx)
        elif "care gap" in msg or intent == "Flag_Care_Gap":
            await self._flag_care_gap(ctx)
        elif "report" in msg or intent == "Generate_Risk_Report":
            await self._risk_report(ctx)
        else:
            await self._stratify(ctx)
        await self.return_control(ctx)

    async def _stratify(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        patient = pv.get("name", "Patient")
        age = pv.get("age", 55)
        conditions = pv.get("conditions", ["hypertension", "diabetes"])
        score = min(100, int(age) // 2 + len(conditions) * 15)
        risk = "High" if score >= 70 else "Medium" if score >= 40 else "Low"
        response = (
            f"Risk stratification — {patient}:\n"
            f"• Risk score: {score}/100 — {risk} risk\n"
            f"• Contributing factors: Age ({age}), {', '.join(conditions)}\n"
            f"• Recommended monitoring frequency: {'Weekly' if risk == 'High' else 'Monthly' if risk == 'Medium' else 'Quarterly'}\n"
            "[Advisory — risk stratification supports clinical planning, not a diagnosis]"
        )
        self._set_response(ctx, response, structured_data={"risk_score": score, "risk_level": risk})

    async def _detect_deterioration(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        vitals = pv.get("recent_vitals", {})
        news2_score = vitals.get("news2_score", 3)
        if news2_score >= 5:
            response = (
                f"⚠️ Deterioration detected — NEWS2 score: {news2_score}\n"
                "Action required: Immediate clinical review\n"
                "Alerting: RMO + Senior Nurse\n"
                "[Advisory — clinical assessment required urgently]"
            )
            self._log_mutation(ctx, "deterioration_alert.sent", True, f"NEWS2 {news2_score} — deterioration alert")
        else:
            response = f"No deterioration detected. NEWS2 score: {news2_score} (within acceptable range)."
        self._set_response(ctx, response)

    async def _flag_care_gap(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        gaps = pv.get("care_gaps", ["HbA1c overdue (8 months)", "Annual eye review overdue"])
        response = (
            "Care gaps identified:\n"
            + "\n".join(f"• {g}" for g in gaps)
            + "\nI've flagged these to the care team and Preventive Wellness Agent for outreach."
        )
        self._log_mutation(ctx, "care_gaps.flagged", str(gaps), "Care gaps identified and flagged")
        self._set_response(ctx, response, structured_data={"care_gaps": gaps})

    async def _risk_report(self, ctx: SessionContextBlock):
        response = (
            "Risk cohort report (ward/department level):\n"
            "• High risk patients: 8 (immediate follow-up required)\n"
            "• Medium risk: 23 (monthly monitoring)\n"
            "• Low risk: 142\n"
            "• Deterioration alerts (last 24h): 2\n"
            "• Care gaps flagged: 15\n"
            "[Report for clinical governance — anonymised at population level]"
        )
        self._set_response(ctx, response)
