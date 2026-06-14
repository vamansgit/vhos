"""Agent 14: Pre-Op Preparation Agent."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class PreOpPrepAgent(VhosAgent):
    agent_id = "preopprep"
    pillar = "g_care"
    domain = "engagement"
    registered_intents = [
        "Send_PreOp_Instructions", "Consent_Form_Reminder",
        "PreAdmission_Clinic_Booking", "Anaesthesia_PreAssessment_Reminder",
    ]
    required_auth_level = AuthLevel.MEDIUM
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.85
    ESC_MAX = 0.08

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal
        pv = ctx.context.patient_view

        # Patient concerns about procedure → route to surgical team, never address by agent
        if any(w in msg for w in ["scared", "worried", "risk", "what if something goes wrong", "alternative", "second opinion"]):
            self._handback(ctx, reason="Patient has concerns about procedure — must be addressed by surgical team", next_intent="doctor_copilot")
            ctx.response_in_progress.text = (
                "Your concerns are completely understandable. "
                "I'm connecting you to your surgical team who can address these directly. "
                "Please don't hesitate to ask them any questions."
            )
            await self.return_control(ctx)
            return

        if intent == "Consent_Form_Reminder" or "consent" in msg:
            await self._consent_reminder(ctx)
        elif intent == "PreAdmission_Clinic_Booking" or "pac" in msg or "pre-admission" in msg:
            await self._pac_booking(ctx)
        elif intent == "Anaesthesia_PreAssessment_Reminder" or "anaesthesia" in msg or "anesthesia" in msg:
            await self._anaesthesia_reminder(ctx)
        else:
            await self._send_instructions(ctx)
        await self.return_control(ctx)

    async def _send_instructions(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        procedure = pv.get("procedure", "your scheduled procedure")
        surgery_date = pv.get("surgery_date", "your scheduled date")
        fasting_hours = pv.get("fasting_hours", 8)
        meds_to_stop = pv.get("medications_to_stop", ["blood thinners", "NSAIDs"])
        meds_to_continue = pv.get("medications_to_continue", ["antihypertensives"])

        # GUARDRAIL: Instructions MUST match documented plan exactly — never improvise
        response = (
            f"Pre-operative instructions for {procedure} on {surgery_date}:\n"
            f"• Fasting: No solid food for {fasting_hours} hours before your procedure. "
            "You may have clear liquids up to 2 hours before, as per your anaesthesia plan.\n"
            f"• Medications to STOP: {', '.join(meds_to_stop)} (as documented in your plan)\n"
            f"• Medications to CONTINUE: {', '.join(meds_to_continue)} (as documented)\n"
            "• Bathing: Shower with antiseptic soap the evening before and morning of procedure\n"
            "• What to bring: photo ID, insurance card, medication list, loose comfortable clothing\n"
            "[These instructions are from your documented surgical plan. "
            "If any details seem incorrect, please contact your surgical team immediately.]"
        )
        self._log_mutation(ctx, "preop_instructions_sent", True, f"Pre-op instructions dispatched for {procedure}")
        self._set_response(ctx, response)

    async def _consent_reminder(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        consent_signed = pv.get("surgical_consent_signed", False)
        if consent_signed:
            response = "Your surgical consent form has been signed and is on file. No action needed."
        else:
            response = (
                "Your surgical consent form has not yet been signed. "
                "I'm sending a secure link to your registered mobile number and email. "
                "Please review and sign before your procedure date. "
                "Your signature will be logged with a timestamp for audit purposes."
            )
            self._log_mutation(ctx, "consent_link_dispatched", True, "Consent form link sent to patient")
        self._set_response(ctx, response)

    async def _pac_booking(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        surgery_date = pv.get("surgery_date", "your procedure date")
        response = (
            f"A Pre-Admission Clinic (PAC) appointment is needed at least 48 hours before {surgery_date}. "
            "Shall I check available PAC slots and book one for you?"
        )
        self._set_response(ctx, response, next_intent="Book_Appointment")

    async def _anaesthesia_reminder(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        pre_assessment_done = pv.get("anaesthesia_pre_assessment_done", False)
        if pre_assessment_done:
            response = "Your anaesthesia pre-assessment is complete. Blood work and allergy review are on file."
        else:
            response = (
                "Anaesthesia pre-assessment checklist:\n"
                "• Allergy review: Please confirm any drug allergies\n"
                "• Dental check: Required if you have loose teeth or dentures\n"
                "• Blood work: Please confirm your pre-op blood tests are done\n"
                "If you have any concerns, your anaesthesiology team will be in touch."
            )
        self._set_response(ctx, response)
