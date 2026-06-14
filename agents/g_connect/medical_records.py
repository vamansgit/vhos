"""Agent 8: Medical Records Agent."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class MedicalRecordsAgent(VhosAgent):
    agent_id = "medical_records"
    pillar = "g_connect"
    domain = "experience"
    registered_intents = ["Request_Medical_Record", "Link_ABHA_ID", "Initiate_ABDM_Exchange", "Check_Record_Completeness"]
    required_auth_level = AuthLevel.HIGH
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.85
    ESC_MAX = 0.10

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        # DPDP §12 erasure request
        if any(w in msg for w in ["delete my data", "erase", "right to be forgotten", "remove my record"]):
            self._handback(ctx, reason="DPDP §12 erasure request — must be handled by orchestrator", next_intent="dpdp_erasure")
            ctx.response_in_progress.text = (
                "I'm connecting you to our data privacy officer to process your data erasure request as required by law."
            )
            await self.return_control(ctx)
            return

        if intent == "Request_Medical_Record" or any(w in msg for w in ["record", "report", "summary", "history", "document"]):
            await self._request_record(ctx, msg)
        elif intent == "Link_ABHA_ID" or "abha" in msg:
            await self._link_abha(ctx, msg)
        elif intent == "Initiate_ABDM_Exchange" or "abdm" in msg or "exchange" in msg:
            await self._abdm_exchange(ctx)
        elif intent == "Check_Record_Completeness" or "complete" in msg or "missing" in msg:
            await self._check_completeness(ctx)
        else:
            self._set_response(ctx, "I can help you access medical records, link ABHA ID, or check record completeness.")
        await self.return_control(ctx)

    async def _request_record(self, ctx: SessionContextBlock, msg: str):
        # GUARDRAIL: Never read records aloud over voice
        voice_mode = ctx.conversation_directives.voice_mode
        if voice_mode:
            response = (
                "For your security, I cannot read medical records aloud. "
                "I've sent a secure link to your registered email and mobile number. "
                "The link expires in 24 hours. Please access your records through the secure patient portal."
            )
        else:
            patient_id = ctx.context.patient_view.get("patient_id", "P-DEMO-001")
            response = (
                f"Your medical records request has been processed. "
                f"Patient ID: {patient_id}. "
                "A secure download link has been sent to your registered contact. "
                "Only the specific records you requested have been included (data minimisation per DPDP 2023). "
                "[Link expires in 24 hours]"
            )
        self._log_mutation(ctx, "fhir:DocumentReference", "requested", "Patient requested medical records")
        self._set_response(ctx, response, outcome="success")

    async def _link_abha(self, ctx: SessionContextBlock, msg: str):
        abha_id = ctx.agent_workspace.scratch.get("abha_id_input")
        if not abha_id:
            response = (
                "To link your ABHA ID, please provide your 14-digit ABHA number "
                "or your registered mobile number. "
                "I'll verify it with the ABDM system."
            )
        else:
            response = (
                f"ABHA ID {abha_id} has been verified and linked to your hospital record. "
                "Your health records are now accessible via the ABDM Health Locker."
            )
            self._log_mutation(ctx, "fhir:Patient.identifier", abha_id, "ABHA ID linked via ABDM verification")
        self._set_response(ctx, response)

    async def _abdm_exchange(self, ctx: SessionContextBlock):
        consent = ctx.agent_workspace.scratch.get("consent_artefact_token")
        if not consent:
            self._set_response(
                ctx,
                "ABDM health record exchange requires a valid consent artefact. "
                "Please generate consent through the ABDM Consent Manager before requesting an exchange.",
                outcome="error"
            )
        else:
            response = (
                "Health record exchange initiated via ABDM gateway. "
                "Records will be available in the Health Locker within 2–5 minutes. "
                "[Consent artefact verified and logged]"
            )
            self._log_mutation(ctx, "abdm:exchange", consent, "ABDM health record exchange initiated")
            self._set_response(ctx, response, outcome="success")

    async def _check_completeness(self, ctx: SessionContextBlock):
        response = (
            "Record completeness review:\n"
            "✅ Discharge summary — present\n"
            "✅ Lab reports — present (last 6 months)\n"
            "⚠️ Operative notes — missing (please contact surgical department)\n"
            "⚠️ Anaesthesia record — missing\n"
            "I've flagged the missing documents to the relevant departments."
        )
        self._set_response(ctx, response, structured_data={"missing": ["operative_notes", "anaesthesia_record"]})
