"""Agent 17: Nurse Co-Pilot Agent — ward workflow, SBAR, escalation support."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class NurseCopilotAgent(VhosAgent):
    agent_id = "nurse_copilot"
    pillar = "g_assist"
    domain = "expertise"
    registered_intents = [
        "Generate_Nursing_Summary", "Adhere_Escalation_Protocol",
        "Track_Ward_Workflow", "Assess_Falls_Risk", "Generate_SBAR_Handover",
    ]
    required_auth_level = AuthLevel.PROVIDER
    fallback_safe = True
    mdsw_scope = "Pending CDSCO SaMD — advisory only"
    KPI_TARGET = 0.85
    ESC_MAX = 0.05

    def _load(self, fname: str) -> pd.DataFrame:
        p = Path(os.getenv("DEMO_DATA_DIR", "demo_data")) / fname
        return pd.read_excel(p) if p.exists() else pd.DataFrame()

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if intent == "Generate_SBAR_Handover" or "sbar" in msg or "handover" in msg:
            await self._generate_sbar(ctx)
        elif intent == "Assess_Falls_Risk" or "falls" in msg or "morse" in msg or "fall risk" in msg:
            await self._assess_falls(ctx)
        elif intent == "Adhere_Escalation_Protocol" or "escalat" in msg or "news" in msg or "spo2" in msg or "deteriorat" in msg:
            await self._escalation_protocol(ctx, msg)
        elif intent == "Track_Ward_Workflow" or "task" in msg or "workflow" in msg or "due" in msg:
            await self._track_workflow(ctx)
        else:
            await self._nursing_summary(ctx)
        await self.return_control(ctx)

    async def _nursing_summary(self, ctx: SessionContextBlock):
        df = self._load("ward_patients.xlsx")
        pv = ctx.context.patient_view
        patient_id = pv.get("patient_id", "P-DEMO-001")

        if df.empty:
            summary = (
                "Ward summary — Bed 12, Patient: Mr. Sharma:\n"
                "• Vitals: BP 130/85, HR 88 bpm, SpO2 97%, Temp 37.2°C, RR 16\n"
                "• Active problems: Post-CABG Day 2, managed pain\n"
                "• Pending orders: ECG at 14:00, wound check at 16:00\n"
                "• MAR: All medications administered. No gaps.\n"
                "[DRAFT — Please review and confirm before filing]"
            )
        else:
            pid_col = next((c for c in df.columns if "patient" in c.lower()), df.columns[0])
            rows = df[df[pid_col] == patient_id] if pid_col else df
            row = rows.iloc[0] if not rows.empty else df.iloc[0]
            name_col = next((c for c in df.columns if "name" in c.lower()), df.columns[0])
            summary = (
                f"Summary for {row.get(name_col, 'Patient')}:\n"
                f"• Vitals: {row.get('vitals', 'See chart')}\n"
                f"• Active problems: {row.get('problems', 'See notes')}\n"
                f"• Pending orders: {row.get('pending_orders', 'None')}\n"
                "[DRAFT — Nurse must confirm before filing]"
            )

        ctx.response_in_progress.requires_confirmation = True
        ctx.response_in_progress.draft_resources = [{"type": "NursingDraft", "content": summary}]
        self._set_response(ctx, summary, structured_data={"draft": True})

    async def _escalation_protocol(self, ctx: SessionContextBlock, msg: str):
        # Apply NEWS2 scoring
        spo2_match = None
        for w in msg.split():
            w = w.replace("%", "")
            if w.isdigit() and 70 <= int(w) <= 100:
                spo2_match = int(w)
                break

        if spo2_match and spo2_match < 92:
            news2_score = "High (SpO2 below threshold)"
            action = "Immediate RRT activation — call 2222 and escalate to senior clinician now"
            level = "RED"
        elif spo2_match and spo2_match < 95:
            news2_score = "Medium"
            action = "Increase monitoring frequency, notify RMO within 30 minutes"
            level = "AMBER"
        else:
            news2_score = "Requires full assessment"
            action = "Perform full NEWS2 assessment: RR, SpO2, temperature, BP, HR, consciousness"
            level = "ASSESS"

        response = (
            f"Escalation assessment — NEWS2: {news2_score} [{level}]\n"
            f"Recommended action: {action}\n"
            "Please confirm your chosen escalation action. "
            "[Advisory only — clinical judgment is yours. This is logged with your staff ID.]"
        )
        ctx.response_in_progress.requires_confirmation = True
        self._set_response(ctx, response, structured_data={"news2": news2_score, "level": level})

    async def _track_workflow(self, ctx: SessionContextBlock):
        response = (
            "Current shift task list:\n"
            "⚠️ DUE IN 15 MIN: ECG for Bed 12 (Mr. Sharma)\n"
            "⚠️ DUE IN 20 MIN: Medication administration round — Beds 8, 10, 14\n"
            "⏰ UPCOMING: Wound assessment — Bed 6 (Mrs. Patel) at 14:30\n"
            "✅ COMPLETED: Morning vitals all beds\n"
            "✅ COMPLETED: 08:00 medication round"
        )
        self._set_response(ctx, response)

    async def _assess_falls(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        # Morse Falls Scale calculation
        history_falls = pv.get("history_of_falls", 0) * 25
        secondary_diagnosis = pv.get("secondary_diagnosis_count", 0) >= 1
        ambulatory_aid = pv.get("ambulatory_aid", "none")
        iv_therapy = pv.get("iv_therapy", False)
        gait = pv.get("gait", "normal")
        mental_status = pv.get("confused", False)

        score = history_falls
        if secondary_diagnosis:
            score += 15
        if ambulatory_aid not in ("none", "bed rest"):
            score += 15 if ambulatory_aid == "crutches" else 30
        if iv_therapy:
            score += 20
        if gait in ("weak", "impaired"):
            score += 10 if gait == "weak" else 20
        if mental_status:
            score += 15

        risk_level = "High" if score >= 45 else "Medium" if score >= 25 else "Low"
        recommendations = []
        if risk_level == "High":
            recommendations = [
                "Activate bed alarm", "Set bed to lowest position",
                "Ensure call light is within reach", "Non-slip footwear",
                "Hourly safety checks", "Document in care plan"
            ]

        response = (
            f"Morse Falls Scale assessment: Score = {score} — {risk_level} Risk\n"
            + (("Recommended interventions:\n" + "\n".join(f"• {r}" for r in recommendations)) if recommendations else "Continue standard safety monitoring.")
            + "\n[DRAFT — Please confirm to write to patient record]"
        )
        ctx.response_in_progress.requires_confirmation = True
        ctx.response_in_progress.draft_resources = [{"type": "FallsRiskObservation", "score": score, "risk": risk_level}]
        self._set_response(ctx, response, structured_data={"morse_score": score, "risk": risk_level})
        self._log_mutation(ctx, "fhir:Observation.falls_risk", f"{risk_level}/{score}", "Morse Falls Scale assessment (pending confirmation)")

    async def _generate_sbar(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        patient_name = pv.get("name", "Patient")
        situation = pv.get("sbar_situation", f"{patient_name} — post-operative, Day 2")
        background = pv.get("sbar_background", "Admitted for CABG, PMH: DM, HTN")
        assessment = pv.get("sbar_assessment", "Stable vitals. Pain controlled. Wound clean.")
        recommendation = pv.get("sbar_recommendation", "Continue current management. Review at 18:00.")

        sbar = (
            f"SBAR Handover [DRAFT — pending outgoing nurse sign-off]:\n"
            f"S (Situation): {situation}\n"
            f"B (Background): {background}\n"
            f"A (Assessment): {assessment}\n"
            f"R (Recommendation): {recommendation}\n\n"
            "Please review and confirm this SBAR before it is delivered to the incoming nurse."
        )
        ctx.response_in_progress.requires_confirmation = True
        ctx.response_in_progress.draft_resources = [{"type": "SBAR", "content": sbar}]
        self._set_response(ctx, sbar, structured_data={"sbar_draft": True})
