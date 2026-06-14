"""Agent 12: Family Communication Agent — privacy-class gated updates."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent

PRIVACY_CLASSES = {
    "logistic": ["pickup time", "ward location", "visiting hours"],
    "clinical_summary": ["procedure done", "post-op status"],
    "clinical_detail": ["complications", "prognosis"],
}


class FamilyCommsAgent(VhosAgent):
    agent_id = "family_comms"
    pillar = "g_care"
    domain = "engagement"
    registered_intents = ["Send_Caregiver_Update", "Coordinate_Family_Logistics", "ICU_Family_Update"]
    required_auth_level = AuthLevel.MEDIUM
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.80
    ESC_MAX = 0.12

    def _verify_authorised_contact(self, ctx: SessionContextBlock) -> tuple[bool, str]:
        """Returns (is_authorised, privacy_class)."""
        pv = ctx.context.patient_view
        caller_id = ctx.principal.principal_id
        authorised = pv.get("authorised_contacts", [])
        primary_caregiver = pv.get("primary_caregiver_id", "")

        if not authorised:
            return True, "logistic"  # Demo: allow logistic level

        if caller_id not in [str(c) for c in authorised]:
            return False, "none"

        if caller_id == primary_caregiver:
            patient_consent = pv.get("clinical_detail_consent", False)
            return True, "clinical_detail" if patient_consent else "clinical_summary"

        return True, "clinical_summary"

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        is_auth, privacy_class = self._verify_authorised_contact(ctx)
        if not is_auth:
            self._set_response(
                ctx,
                "I'm sorry, but I can only share patient information with authorised contacts. "
                "If you believe this is an error, please speak to the ward nurse or contact the hospital's patient relations team.",
                outcome="error"
            )
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal
        ctx.agent_workspace.scratch["privacy_class"] = privacy_class

        if intent == "ICU_Family_Update" or "icu" in msg or "critical" in msg:
            await self._icu_update(ctx, privacy_class)
        elif intent == "Coordinate_Family_Logistics" or any(w in msg for w in ["pickup", "discharge", "visit", "when can i come"]):
            await self._logistics(ctx, privacy_class)
        else:
            await self._caregiver_update(ctx, privacy_class)
        await self.return_control(ctx)

    async def _caregiver_update(self, ctx: SessionContextBlock, privacy_class: str):
        pv = ctx.context.patient_view
        patient_name = pv.get("name", "your family member")

        if privacy_class == "logistic":
            response = (
                f"{patient_name} is in Ward {pv.get('ward', '3A')}, Bed {pv.get('bed', '12')}. "
                f"Visiting hours: {pv.get('visiting_hours', '10 AM–12 PM and 5 PM–7 PM')}. "
                "For clinical updates, please speak directly with the treating doctor."
            )
        elif privacy_class in ("clinical_summary", "clinical_detail"):
            response = (
                f"{patient_name}'s procedure went well. "
                f"Current status: {pv.get('post_op_status', 'stable, recovering')}. "
                f"Location: Ward {pv.get('ward', '3A')}. "
                + (
                    f"Additional details: {pv.get('clinical_details', 'no complications reported')}. "
                    if privacy_class == "clinical_detail" else ""
                )
                + "The doctor will provide a full update at the next scheduled review."
            )
        else:
            response = "I'm unable to provide information to unauthorised contacts. Please contact the ward directly."

        self._set_response(ctx, response, structured_data={"privacy_class": privacy_class})

    async def _logistics(self, ctx: SessionContextBlock, privacy_class: str):
        pv = ctx.context.patient_view
        discharge_date = pv.get("discharge_date", "tomorrow")
        home_prep = pv.get("home_preparation", ["mobility aids may be required"])
        response = (
            f"Discharge is planned for {discharge_date}. "
            f"Home preparation needed: {', '.join(home_prep)}. "
            "Please ensure someone is available for pickup. "
            "We'll confirm the exact time 2 hours before discharge."
        )
        self._set_response(ctx, response)

    async def _icu_update(self, ctx: SessionContextBlock, privacy_class: str):
        pv = ctx.context.patient_view
        # GUARDRAIL: Only clinician-approved templates, never improvise
        approved_template = pv.get("icu_approved_update_template")
        if not approved_template:
            response = (
                "I don't have a clinician-approved update available at this time. "
                "For ICU patient updates, please contact the ICU nursing station directly or speak to the attending physician. "
                "Would you like me to arrange a callback from the nurse in charge?"
            )
        else:
            response = approved_template  # Read ONLY approved text — no improvisation
        self._set_response(ctx, response)
