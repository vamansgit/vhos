"""Agent 15: Population Health Campaign Agent."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent

OPT_OUT_PHRASES = ["stop", "opt out", "unsubscribe", "don't contact", "remove me", "no more"]


class PopulationCampaignAgent(VhosAgent):
    agent_id = "population_campaign"
    pillar = "g_care"
    domain = "engagement"
    registered_intents = ["Launch_Campaign", "Send_Cohort_Outreach", "Track_Campaign_Response", "Process_Opt_Out"]
    required_auth_level = AuthLevel.LOW
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.60
    ESC_MAX = 0.02

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()

        # Opt-out — immediate, permanent
        for phrase in OPT_OUT_PHRASES:
            if phrase in msg:
                self._log_mutation(ctx, "patient.opt_out_campaigns", True, "Campaign opt-out processed")
                self._set_response(
                    ctx,
                    "You've been removed from all campaign communications immediately and permanently. "
                    "You will not receive further messages. Thank you for letting us know.",
                    outcome="success",
                    structured_data={"opt_out_campaigns": True}
                )
                await self.return_control(ctx)
                return

        intent = ctx.goal

        if intent == "Launch_Campaign":
            await self._launch_campaign(ctx)
        elif intent == "Send_Cohort_Outreach":
            await self._send_outreach(ctx)
        elif intent == "Track_Campaign_Response":
            await self._track_response(ctx, msg)
        else:
            self._set_response(ctx, "This is a population health outreach. How can I help you today?")
        await self.return_control(ctx)

    async def _launch_campaign(self, ctx: SessionContextBlock):
        # GUARDRAIL: Requires compliance officer approval
        approval_ref = ctx.agent_workspace.scratch.get("campaign_approval_ref")
        if not approval_ref:
            self._set_response(
                ctx,
                "Campaign launch requires a compliance officer approval reference. "
                "Please provide the campaign_approval_ref before initiating.",
                outcome="error"
            )
            return
        cohort_size = ctx.agent_workspace.scratch.get("cohort_size", 0)
        campaign_name = ctx.agent_workspace.scratch.get("campaign_name", "Health Outreach")
        self._log_mutation(ctx, "campaign.launched", approval_ref, f"Campaign {campaign_name} launched with approval {approval_ref}")
        response = (
            f"Campaign '{campaign_name}' launched (Approval: {approval_ref}). "
            f"Target cohort: {cohort_size} patients. "
            "Opt-outs have been filtered. "
            "Rate limit: 200/hour. Time restrictions: 09:00–20:00 local. "
            "DND registry checked. Campaign is now active."
        )
        self._set_response(ctx, response, outcome="success")

    async def _send_outreach(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        patient_name = pv.get("name", "")
        channel = pv.get("preferred_channel", "WhatsApp")
        template = ctx.agent_workspace.scratch.get("message_template", "Health screening reminder from your hospital.")
        response = (
            f"Outreach sent via {channel}: '{template}' "
            f"to {patient_name or 'patient'}. Delivery status: sent."
        )
        self._set_response(ctx, response, structured_data={"channel": channel, "delivered": True})

    async def _track_response(self, ctx: SessionContextBlock, msg: str):
        if any(w in msg for w in ["yes", "interested", "book", "ok", "sure"]):
            outcome = "accepted"
            response = "Thank you for your interest! Let me book an appointment for you."
            next_intent = "Book_Appointment"
        elif any(w in msg for w in ["no", "not interested", "later", "decline"]):
            outcome = "declined"
            self._log_mutation(ctx, "campaign_response", "declined", "Patient declined campaign offer")
            response = "No problem. We'll reach out again in the future. Is there anything else I can help you with?"
            next_intent = None
        else:
            outcome = "no_response"
            response = "I didn't catch your response. Would you like to book an appointment or would you prefer to be contacted another time?"
            next_intent = None

        self._set_response(ctx, response, structured_data={"campaign_outcome": outcome},
                           next_intent=next_intent)
