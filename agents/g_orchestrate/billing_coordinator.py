"""Agent 29: Billing Coordinator Agent."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class BillingCoordinatorAgent(VhosAgent):
    agent_id = "billing_coordinator"
    pillar = "g_orchestrate"
    domain = "orchestration"
    registered_intents = ["Generate_Bill", "Process_Pre_Auth", "Handle_Payment_Query", "Reconcile_Insurance_Claim"]
    required_auth_level = AuthLevel.MEDIUM
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.88
    ESC_MAX = 0.05

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if "pre-auth" in msg or "pre auth" in msg or "authorization" in msg or intent == "Process_Pre_Auth":
            await self._pre_auth(ctx)
        elif "reconcile" in msg or "claim" in msg or intent == "Reconcile_Insurance_Claim":
            await self._reconcile(ctx)
        elif "payment" in msg or "pay" in msg or intent == "Handle_Payment_Query":
            await self._payment_query(ctx, msg)
        else:
            await self._generate_bill(ctx)
        await self.return_control(ctx)

    async def _generate_bill(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        patient_name = pv.get("name", "Patient")
        response = (
            f"Bill generated for {patient_name}:\n"
            "• Consultation: ₹1,500\n"
            "• Lab tests: ₹3,200\n"
            "• Medications: ₹800\n"
            "• Room charges: ₹4,500/day × 3 days = ₹13,500\n"
            "• Total (gross): ₹19,000\n"
            "• Insurance deduction: ₹15,000\n"
            "• Patient out-of-pocket: ₹4,000\n"
            "[Draft bill — pending final discharge charges]"
        )
        self._set_response(ctx, response, structured_data={"total": 19000, "patient_payable": 4000})

    async def _pre_auth(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        procedure = pv.get("procedure", "the procedure")
        response = (
            f"Pre-authorisation request submitted for {procedure}:\n"
            "• TPA: Star Health\n"
            "• Estimated cost: ₹50,000\n"
            "• Requested pre-auth: ₹45,000\n"
            "• Status: Submitted (ref: PA-2026-001)\n"
            "Expected response within 4 hours. You'll be notified via SMS."
        )
        self._log_mutation(ctx, "preauth.submitted", "PA-2026-001", f"Pre-auth submitted for {procedure}")
        self._set_response(ctx, response, outcome="success")

    async def _payment_query(self, ctx: SessionContextBlock, msg: str):
        response = (
            "Payment options available:\n"
            "• Cash at billing counter\n"
            "• Card/UPI at billing counter\n"
            "• Online payment via patient portal (link sent to mobile)\n"
            "• EMI options available for bills above ₹25,000\n"
            "Is there a specific payment concern I can help with?"
        )
        self._set_response(ctx, response)

    async def _reconcile(self, ctx: SessionContextBlock):
        response = (
            "Insurance claim reconciliation:\n"
            "• Claim submitted: ₹45,000\n"
            "• Approved: ₹40,000\n"
            "• Rejected items: Comfort items (₹2,000) — not covered\n"
            "• Under review: Day 3 room upgrade (₹3,000)\n"
            "Patient out-of-pocket after insurance: ₹5,000\n"
            "[If you wish to dispute rejected items, I'll initiate the appeals process]"
        )
        self._set_response(ctx, response)
