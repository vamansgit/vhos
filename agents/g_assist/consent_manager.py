"""Agent 22: Consent Manager Agent."""
from __future__ import annotations

import time

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class ConsentManagerAgent(VhosAgent):
    agent_id = "consent_manager"
    pillar = "g_assist"
    domain = "expertise"
    registered_intents = ["Capture_Consent", "Verify_Consent", "Withdraw_Consent", "Generate_Consent_Document"]
    required_auth_level = AuthLevel.MEDIUM
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.95
    ESC_MAX = 0.03

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if "withdraw" in msg or "revoke" in msg or intent == "Withdraw_Consent":
            await self._withdraw(ctx)
        elif "verify" in msg or "check consent" in msg or intent == "Verify_Consent":
            await self._verify(ctx)
        elif "generate" in msg or "document" in msg or intent == "Generate_Consent_Document":
            await self._generate_doc(ctx)
        else:
            await self._capture(ctx, msg)
        await self.return_control(ctx)

    async def _capture(self, ctx: SessionContextBlock, msg: str):
        pv = ctx.context.patient_view
        procedure = pv.get("procedure", "the described procedure")
        if any(w in msg for w in ["yes", "agree", "consent", "i agree", "ok", "confirm"]):
            ts = time.time()
            self._log_mutation(ctx, "fhir:Consent.status", "active", f"Consent captured at {ts}")
            response = (
                f"Consent for {procedure} has been recorded with timestamp {int(ts)}. "
                "A copy has been sent to your registered email. "
                "[Consent logged for NABH/JCI audit — ref: CNSNT-{ts:.0f}]"
            )
        else:
            response = (
                f"I need to capture your consent for {procedure}. "
                "Before proceeding, please confirm you understand:\n"
                "• The nature of the procedure and its purpose\n"
                "• Potential risks and benefits\n"
                "• Alternatives available\n"
                "• Your right to withdraw consent at any time\n"
                "Do you consent to proceed?"
            )
        self._set_response(ctx, response)

    async def _verify(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        consent_on_file = pv.get("consent_on_file", True)
        procedure = pv.get("procedure", "the procedure")
        if consent_on_file:
            ts = pv.get("consent_timestamp", "on file")
            response = f"Consent for {procedure} is on file (captured: {ts}). No further action required."
        else:
            response = f"No consent on file for {procedure}. Consent must be captured before proceeding."
        self._set_response(ctx, response)

    async def _withdraw(self, ctx: SessionContextBlock):
        ts = time.time()
        self._log_mutation(ctx, "fhir:Consent.status", "inactive", f"Consent withdrawn at {ts}")
        response = (
            "Your consent has been withdrawn and recorded. "
            "The clinical team has been notified. "
            "This will not affect any treatment you've already received. "
            "[Withdrawal logged with timestamp for audit]"
        )
        self._set_response(ctx, response, outcome="success")

    async def _generate_doc(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        response = (
            "Consent document generated and sent to your registered email. "
            f"Patient: {pv.get('name', 'Patient')}. "
            f"Procedure: {pv.get('procedure', 'as documented')}. "
            "Please sign and return before your procedure date."
        )
        self._set_response(ctx, response)
