"""Agent 31: Referral Manager Agent."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class ReferralManagerAgent(VhosAgent):
    agent_id = "referral_manager"
    pillar = "g_orchestrate"
    domain = "orchestration"
    registered_intents = ["Create_Referral", "Track_Referral", "Accept_Referral", "Reject_Referral"]
    required_auth_level = AuthLevel.PROVIDER
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.88
    ESC_MAX = 0.04

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if "track" in msg or "status" in msg or intent == "Track_Referral":
            await self._track(ctx)
        elif "accept" in msg or intent == "Accept_Referral":
            await self._accept(ctx)
        elif "reject" in msg or "decline" in msg or intent == "Reject_Referral":
            await self._reject(ctx, msg)
        else:
            await self._create(ctx, msg)
        await self.return_control(ctx)

    async def _create(self, ctx: SessionContextBlock, msg: str):
        pv = ctx.context.patient_view
        patient = pv.get("name", "Patient")
        ref_id = "REF-2026-" + patient.split()[-1].upper()[:4] + "-001"
        specialty = "Cardiology" if "cardiac" in msg or "cardio" in msg else "the requested specialty"
        response = (
            f"Referral created:\n"
            f"• Ref ID: {ref_id}\n"
            f"• Patient: {patient}\n"
            f"• Referred to: {specialty}\n"
            "• Urgency: Routine (can be changed if needed)\n"
            "• Referral letter: Generated and sent\n"
            "• Expected appointment: Within 2 weeks\n"
            "Patient and receiving team notified."
        )
        self._log_mutation(ctx, "fhir:ServiceRequest.referral", ref_id, f"Referral to {specialty}")
        self._set_response(ctx, response, outcome="success")

    async def _track(self, ctx: SessionContextBlock):
        response = (
            "Referral status:\n"
            "• REF-2026-DEMO-001: Accepted by Cardiology — appointment confirmed for 20 Jun\n"
            "• REF-2026-DEMO-002: Awaiting acceptance from Neurology (2 days pending)\n"
            "[Automated chase sent if no response in 48h]"
        )
        self._set_response(ctx, response)

    async def _accept(self, ctx: SessionContextBlock):
        self._log_mutation(ctx, "referral.status", "accepted", "Referral accepted by specialist")
        response = "Referral accepted. Patient has been notified and appointment is being confirmed."
        self._set_response(ctx, response, outcome="success")

    async def _reject(self, ctx: SessionContextBlock, msg: str):
        self._log_mutation(ctx, "referral.status", "rejected", "Referral rejected — reason captured")
        response = (
            "Referral rejected. Reason has been logged. "
            "The referring doctor has been notified with the reason. "
            "An alternative pathway will be suggested."
        )
        self._set_response(ctx, response)
