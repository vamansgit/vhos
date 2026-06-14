"""Agent 6: Proactive Outreach & Re-engagement Agent."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from agents.base import AuthLevel, SessionContextBlock, VhosAgent

OPT_OUT_PHRASES = ["stop", "opt out", "unsubscribe", "don't call", "do not call", "remove me", "no more calls"]


class ProactiveOutreachAgent(VhosAgent):
    agent_id = "proactive_outreach"
    pillar = "g_connect"
    domain = "experience"
    registered_intents = [
        "Match_Patient_To_Slot", "Initiate_Outbound_Campaign", "Personalise_Outreach_Message",
        "Handle_Patient_Response", "Book_Appointment_From_Outreach", "Process_Opt_Out",
    ]
    required_auth_level = AuthLevel.MEDIUM
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.30
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

        # Opt-out check — must be immediate
        for phrase in OPT_OUT_PHRASES:
            if phrase in msg:
                await self._process_opt_out(ctx, msg)
                await self.return_control(ctx)
                return

        intent = ctx.goal

        if intent == "Process_Opt_Out":
            await self._process_opt_out(ctx, msg)
        elif intent == "Book_Appointment_From_Outreach" or any(w in msg for w in ["yes", "book", "confirm", "wednesday", "thursday"]):
            await self._book_from_outreach(ctx, msg)
        elif intent == "Handle_Patient_Response" or "decline" in msg or "no" in msg:
            await self._handle_response(ctx, msg)
        else:
            await self._send_personalised_message(ctx)

        await self.return_control(ctx)

    async def _send_personalised_message(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        patient_name = pv.get("name", "Mr. Sharma")
        doctor_name = pv.get("treating_doctor", "Dr. Rao")
        hospital_name = ctx.context.hospital_view.get("name", "Apollo Hospital")
        elapsed = pv.get("months_since_last_visit", "almost a year")
        slot = pv.get("suggested_slot", "this Wednesday at 10:30 AM")

        response = (
            f"Hello {patient_name}, I'm calling from {hospital_name}. "
            f"We noticed it's been {elapsed} since your last check-up with {doctor_name}. "
            f"We have a convenient slot available {slot}. "
            "Would you like me to book that for you?"
        )
        # GUARDRAIL: never mention specific clinical findings
        self._set_response(ctx, response, structured_data={"outreach_type": "care_reminder"})

    async def _book_from_outreach(self, ctx: SessionContextBlock, msg: str):
        pv = ctx.context.patient_view
        patient_name = pv.get("name", "the patient")
        slot = pv.get("suggested_slot", "Wednesday at 10:30 AM")
        ref = "APT-OUT-" + patient_name.split()[-1].upper()[:4] + "-001"
        response = (
            f"Excellent! I've confirmed your appointment for {slot}. "
            f"Reference: {ref}. "
            "You'll receive an SMS and WhatsApp confirmation shortly. "
            "Is there anything else you need?"
        )
        self._log_mutation(ctx, "fhir:Appointment", ref, "Booking from outreach campaign")
        self._set_response(ctx, response, outcome="success")

    async def _handle_response(self, ctx: SessionContextBlock, msg: str):
        pv = ctx.context.patient_view
        patient_name = pv.get("name", "")
        response = (
            f"No problem{', ' + patient_name if patient_name else ''}. "
            "Would an alternative date work better for you? "
            "I can check availability for next week as well."
        )
        self._log_mutation(ctx, "outreach_log", "declined", "Patient declined outreach slot")
        self._set_response(ctx, response)

    async def _process_opt_out(self, ctx: SessionContextBlock, msg: str):
        pv = ctx.context.patient_view
        patient_id = pv.get("patient_id", "unknown")
        self._log_mutation(ctx, "patient.opt_out_outreach", True, "Patient requested opt-out")
        response = (
            "I've immediately removed you from all outreach lists. "
            "You will not receive any further calls or messages from us for appointments. "
            "If you change your mind, please contact us directly. "
            "Is there anything else I can help you with today?"
        )
        self._set_response(ctx, response, outcome="success",
                           structured_data={"opt_out": True, "patient_id": patient_id})
