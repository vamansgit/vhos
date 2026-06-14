"""Agent 9: Medicine Adherence Agent."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class MedicineAdherenceAgent(VhosAgent):
    agent_id = "medicine_adherence"
    pillar = "g_care"
    domain = "engagement"
    registered_intents = ["Log_Medication_Intake", "Track_Missed_Dose", "Confirm_Compliance", "Discharge_Followup"]
    required_auth_level = AuthLevel.LOW
    fallback_safe = True
    mdsw_scope = "Pending CDSCO SaMD — advisory only"
    KPI_TARGET = 0.80
    ESC_MAX = 0.08

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

        # Adverse effect → immediate triage handback
        if any(w in msg for w in ["reaction", "side effect", "allergic", "rash", "swelling", "difficulty breathing", "chest tight"]):
            self._handback(ctx, reason="Adverse effect reported", next_intent="triage")
            ctx.response_in_progress.text = (
                "I'm concerned about what you've described. "
                "I'm connecting you to our triage team right away. Please stay on the line."
            )
            await self.return_control(ctx)
            return

        if intent == "Confirm_Compliance" or any(w in msg for w in ["compliance", "adherence", "summary", "report"]):
            await self._confirm_compliance(ctx)
        elif intent == "Track_Missed_Dose" or any(w in msg for w in ["missed", "forgot", "skip"]):
            await self._track_missed(ctx)
        elif intent == "Discharge_Followup" or "discharge" in msg:
            await self._discharge_followup(ctx, msg)
        else:
            await self._log_intake(ctx, msg)

        await self.return_control(ctx)

    async def _log_intake(self, ctx: SessionContextBlock, msg: str):
        pv = ctx.context.patient_view
        patient_name = pv.get("name", "")
        df = self._load("medications.xlsx")

        if any(w in msg for w in ["yes", "taken", "took", "done", "completed"]):
            status = "completed"
            response_text = (
                f"{'Great, ' + patient_name + '! ' if patient_name else ''}"
                "Logged: medication taken as prescribed by your doctor. "
                "Your next dose reminder will be sent at the scheduled time."
            )
        elif any(w in msg for w in ["not yet", "later", "soon"]):
            status = "not-taken"
            response_text = (
                "Understood. I'll check back in 30 minutes. "
                "Please take your medication as prescribed by your doctor."
            )
        elif any(w in msg for w in ["missed", "forgot", "can't", "cannot", "skip"]):
            status = "not-taken"
            response_text = (
                "I've logged this dose as missed. "
                "Please do not double-dose. Continue with your next scheduled dose as prescribed by your doctor. "
                "If you have concerns, please contact your care team."
            )
        else:
            response_text = (
                "Did you take your medication as scheduled? "
                "Please reply: 'Yes, taken' / 'Not yet' / 'I missed it'."
            )
            status = None

        if status:
            self._log_mutation(ctx, "fhir:MedicationStatement.status", status, f"Patient reported: {status}")
        self._set_response(ctx, response_text, structured_data={"status": status})

    async def _track_missed(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        missed_count = pv.get("consecutive_misses", 0) + 1
        if missed_count >= 2:
            response = (
                f"I've noted {missed_count} consecutive missed doses. "
                "I've sent an alert to your care team as per protocol. "
                "Please contact your doctor or care coordinator. "
                "[GUARDRAIL: Advisory only — do not stop or change doses without medical advice]"
            )
            self._log_mutation(ctx, "fhir:Communication", "care_team_alert", f"{missed_count} consecutive misses — alert sent")
        else:
            response = (
                "I've logged your missed dose. "
                "Please continue with your next scheduled dose as prescribed. "
                "Do not double-dose. If you miss 2 doses in a row, I'll notify your care team."
            )
            self._log_mutation(ctx, "fhir:MedicationStatement.status", "not-taken", "Missed dose logged")
        self._set_response(ctx, response)

    async def _confirm_compliance(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        doses_taken = pv.get("doses_taken_7d", 13)
        doses_scheduled = pv.get("doses_scheduled_7d", 14)
        rate = round(doses_taken / doses_scheduled * 100) if doses_scheduled else 0
        response = (
            f"Medication adherence summary (last 7 days): "
            f"{doses_taken} of {doses_scheduled} scheduled doses taken — {rate}% adherence. "
            + ("Excellent adherence!" if rate >= 90 else "Good progress — keep it up!" if rate >= 70 else "Below target — please speak to your care team.")
        )
        self._set_response(ctx, response, structured_data={"adherence_rate": rate, "period_days": 7})

    async def _discharge_followup(self, ctx: SessionContextBlock, msg: str):
        pv = ctx.context.patient_view
        patient_name = pv.get("name", "")
        response = (
            f"Hello{', ' + patient_name if patient_name else ''}. "
            "This is your post-discharge medication check. "
            "Have you been able to get all your prescribed medications from the pharmacy? "
            "Are you taking them as instructed by your doctor? "
            "Have you noticed any unusual symptoms since discharge?"
        )
        self._set_response(ctx, response)
