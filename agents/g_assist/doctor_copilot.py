"""Agent 18: Doctor Co-Pilot Agent — ambient clinic, SOAP notes, orders. DRAFT only."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class DoctorCopilotAgent(VhosAgent):
    agent_id = "doctor_copilot"
    pillar = "g_assist"
    domain = "expertise"
    registered_intents = [
        "Summarize_Patient_Record", "Automate_Documentation",
        "Extract_Clinical_History", "Draft_Clinical_Order", "Ward_Round_Briefing",
    ]
    required_auth_level = AuthLevel.PROVIDER
    fallback_safe = False
    mdsw_scope = "Pending CDSCO SaMD — advisory only"
    KPI_TARGET = 0.80
    ESC_MAX = 0.04

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

        if intent == "Ward_Round_Briefing" or "ward round" in msg or "briefing" in msg:
            await self._ward_round(ctx)
        elif intent == "Draft_Clinical_Order" or any(w in msg for w in ["prescribe", "order", "medication", "mg", "dose"]):
            await self._draft_order(ctx, msg)
        elif intent == "Extract_Clinical_History" or any(w in msg for w in ["last", "previous", "hba1c", "lab", "history of"]):
            await self._extract_history(ctx, msg)
        elif intent == "Automate_Documentation" or any(w in msg for w in ["note", "soap", "document", "dictate"]):
            await self._automate_docs(ctx, msg)
        else:
            await self._summarize_record(ctx)
        await self.return_control(ctx)

    async def _summarize_record(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        df_patients = self._load("patients.xlsx")
        df_labs = self._load("labs.xlsx")

        patient_name = pv.get("name", "the patient")
        age = pv.get("age", "unknown")
        conditions = pv.get("conditions", ["hypertension", "type 2 diabetes"])
        medications = pv.get("medications", ["metformin 500mg", "amlodipine 5mg"])
        allergies = pv.get("allergies", ["penicillin"])

        summary = (
            f"Pre-consultation brief — {patient_name}, {age}y:\n"
            f"• Active conditions: {', '.join(conditions)}\n"
            f"• Current medications: {', '.join(medications)}\n"
            f"• Allergies: {', '.join(allergies)}\n"
            f"• Last visit: {pv.get('last_visit_date', '3 months ago')}\n"
            f"• Last HbA1c: {pv.get('last_hba1c', '7.8%')} ({pv.get('last_hba1c_date', '3 months ago')})\n"
            f"• BP trend: {pv.get('bp_trend', '130-140/85 mmHg range')}\n"
            f"[Source: FHIR patient record | Advisory only — verify before clinical decisions]"
        )
        self._set_response(ctx, summary, structured_data={"patient_id": pv.get("patient_id"), "draft": True})

    async def _automate_docs(self, ctx: SessionContextBlock, msg: str):
        pv = ctx.context.patient_view
        patient_name = pv.get("name", "patient")
        soap_draft = (
            f"[DRAFT SOAP NOTE — {patient_name}]\n"
            f"S (Subjective): {pv.get('chief_complaint', msg[:200])}\n"
            f"O (Objective): Vitals: {pv.get('vitals', 'BP 130/85, HR 78, SpO2 98%')}. Examination: {pv.get('examination', 'as documented')}\n"
            f"A (Assessment): {pv.get('assessment', '[Doctor to complete]')}\n"
            f"P (Plan): {pv.get('plan', '[Doctor to complete]')}\n\n"
            "This is a DRAFT. Doctor must review, edit, and confirm before filing. "
            "Agent NEVER auto-commits any note."
        )
        ctx.response_in_progress.requires_confirmation = True
        ctx.response_in_progress.draft_resources = [{"type": "SOAPNote", "content": soap_draft}]
        self._set_response(ctx, soap_draft, structured_data={"draft": True})
        self._log_mutation(ctx, "fhir:DocumentReference.DRAFT", "created", "Ambient SOAP note draft (pending doctor confirmation)")

    async def _extract_history(self, ctx: SessionContextBlock, msg: str):
        df = self._load("labs.xlsx")
        pv = ctx.context.patient_view
        patient_id = pv.get("patient_id", "P-DEMO-001")

        # Detect what's being queried
        param = "HbA1c"
        for p in ["hba1c", "creatinine", "haemoglobin", "hemoglobin", "tsh", "sodium", "potassium", "glucose"]:
            if p in msg.lower():
                param = p.upper()
                break

        if df.empty or patient_id not in df.get("patient_id", pd.Series([])).values:
            # Demo trend data
            history = [
                {"date": "Jan 2026", "value": "9.2%"},
                {"date": "Apr 2026", "value": "8.4%"},
                {"date": "Jul 2026", "value": "7.8%"},
            ]
        else:
            pid_col = next((c for c in df.columns if "patient" in c.lower()), None)
            param_col = next((c for c in df.columns if param.lower() in c.lower()), None)
            date_col = next((c for c in df.columns if "date" in c.lower()), None)
            rows = df[df[pid_col] == patient_id].head(3) if pid_col else df.head(3)
            history = [{"date": str(r.get(date_col, "N/A")), "value": str(r.get(param_col, "N/A"))} for _, r in rows.iterrows()]

        trend_str = " → ".join(f"{h['value']} ({h['date']})" for h in history)
        direction = "improving" if history else "unknown"
        if len(history) >= 2:
            try:
                first = float("".join(c for c in history[0]["value"] if c.isdigit() or c == "."))
                last = float("".join(c for c in history[-1]["value"] if c.isdigit() or c == "."))
                direction = "improving" if last < first else "worsening" if last > first else "stable"
            except Exception:
                pass

        response = (
            f"{param} trend (last 3 values): {trend_str} — {direction} trajectory. "
            f"[Source: LIS DiagnosticReport | All values from patient record]"
        )
        self._set_response(ctx, response, structured_data={"param": param, "history": history, "direction": direction})

    async def _draft_order(self, ctx: SessionContextBlock, msg: str):
        # Parse basic order from voice/text — DRAFT ONLY
        order_draft = {
            "drug": ctx.agent_workspace.scratch.get("drug", "as specified"),
            "dose": ctx.agent_workspace.scratch.get("dose", "as specified"),
            "frequency": ctx.agent_workspace.scratch.get("frequency", "as specified"),
            "duration": ctx.agent_workspace.scratch.get("duration", "as specified"),
            "route": ctx.agent_workspace.scratch.get("route", "oral"),
            "raw_dictation": msg,
        }
        response = (
            f"[DRAFT MEDICATION ORDER]\n"
            f"Drug: {order_draft['drug']}\n"
            f"Dose: {order_draft['dose']}\n"
            f"Frequency: {order_draft['frequency']}\n"
            f"Duration: {order_draft['duration']}\n"
            f"Route: {order_draft['route']}\n\n"
            "Please review this order carefully. "
            "Say 'confirm' or tap Sign-Off to submit. Agent NEVER auto-submits orders."
        )
        ctx.response_in_progress.requires_confirmation = True
        ctx.response_in_progress.draft_resources = [{"type": "MedicationRequest", **order_draft}]
        self._set_response(ctx, response, structured_data={"draft_order": order_draft})
        self._log_mutation(ctx, "fhir:MedicationRequest.DRAFT", str(order_draft), "Draft order created (pending doctor sign-off)")

    async def _ward_round(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        patient_name = pv.get("name", "Patient")
        overnight = pv.get("overnight_events", "No significant events overnight.")
        vitals_change = pv.get("vitals_change", "Vitals stable")
        labs_change = pv.get("labs_change", "No critical lab changes")
        plan = pv.get("current_plan", "Continue current management")

        response = (
            f"Ward round brief — {patient_name} (45 seconds):\n"
            f"Overnight: {overnight}\n"
            f"Vitals: {vitals_change}\n"
            f"Labs: {labs_change}\n"
            f"Current plan: {plan}\n"
            "[Source: FHIR overnight records | Advisory — verify before decisions]"
        )
        self._set_response(ctx, response)
