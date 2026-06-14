"""Agent 7: Hyper-Personalised Onboarding Agent (competitor_counter)."""
from __future__ import annotations

import re

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class CompetitorCounterAgent(VhosAgent):
    agent_id = "competitor_counter"
    pillar = "g_connect"
    domain = "experience"
    registered_intents = [
        "Handle_Natural_Language_Query", "Match_Complex_Slot_Request",
        "Close_First_Visit_Booking", "Onboard_New_Patient", "Answer_Specialty_Query",
    ]
    required_auth_level = AuthLevel.LOW
    fallback_safe = True
    streaming_voice_compatible = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.65
    ESC_MAX = 0.06
    OPENING_STATEMENT = (
        "Welcome! Let me find the right doctor for you in seconds. "
        "Just tell me what kind of specialist you need and when works best — "
        "I'll show you available slots right away."
    )

    def _extract_params(self, msg: str) -> dict:
        params = {}
        specialties = ["orthopaedic", "cardiac", "cardio", "neuro", "gynaec", "paediatric",
                       "oncol", "radiol", "urolog", "ophthal", "dermat", "psychiatr", "general"]
        for s in specialties:
            if s in msg.lower():
                params["specialty"] = s
                break
        if "senior" in msg.lower():
            params["seniority"] = "senior"
        if "consultant" in msg.lower():
            params["seniority"] = "consultant"
        time_match = re.search(r"(\d{1,2})\s*(am|pm|:00)", msg.lower())
        if time_match:
            params["time_preference"] = time_match.group(0)
        day_match = re.search(r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", msg.lower())
        if day_match:
            params["day_preference"] = day_match.group(1).capitalize()
        lang_match = re.search(r"(hindi|tamil|telugu|kannada|malayalam|marathi|bengali|gujarati)", msg.lower())
        if lang_match:
            params["language"] = lang_match.group(1).capitalize()
        return params

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message()
        lower = msg.lower()

        # Urgency signals → triage
        if any(w in lower for w in ["urgent", "emergency", "immediately", "right now", "very sick"]):
            self._handback(ctx, reason="Urgency signal detected", next_intent="triage")
            ctx.response_in_progress.text = "I can see you need help urgently. Let me connect you to our triage team immediately."
            await self.return_control(ctx)
            return

        intent = ctx.goal
        workspace = ctx.agent_workspace.scratch

        if "book" in lower and workspace.get("selected_slot"):
            await self._close_booking(ctx, msg)
        elif workspace.get("slots_shown"):
            await self._handle_slot_selection(ctx, msg)
        else:
            await self._handle_nl_query(ctx, msg)

        await self.return_control(ctx)

    async def _handle_nl_query(self, ctx: SessionContextBlock, msg: str):
        params = self._extract_params(msg)
        specialty = params.get("specialty", "general")
        seniority = params.get("seniority", "")
        day = params.get("day_preference", "tomorrow")
        time_pref = params.get("time_preference", "morning")
        language = params.get("language", "")

        doctor_name = "Dr. Arjun Mehta" if "orthopaedic" in specialty else "Dr. Priya Rao"
        qualifier = f"senior {specialty}" if seniority else specialty
        lang_note = f" (speaks {language})" if language else ""

        slots = [
            {"slot_id": "SLT-NP-001", "doctor": doctor_name, "qualifier": qualifier,
             "datetime": f"{day} at 5:15 PM", "lang": lang_note},
            {"slot_id": "SLT-NP-002", "doctor": doctor_name, "qualifier": qualifier,
             "datetime": f"{day} at 6:00 PM", "lang": lang_note},
            {"slot_id": "SLT-NP-003", "doctor": doctor_name, "qualifier": qualifier,
             "datetime": f"Next day at 9:00 AM", "lang": lang_note},
        ]
        ctx.agent_workspace.scratch["slots_shown"] = slots
        ctx.agent_workspace.scratch["params"] = params

        slot_text = "\n".join(f"{i+1}. {s['datetime']} — {s['doctor']}, {s['qualifier']}{s['lang']}" for i, s in enumerate(slots))
        response = (
            f"I found the following available slots:\n{slot_text}\n\n"
            "Which slot would you like? Just say '1', '2', or '3'. "
            "(No registration needed to hold a slot — I just need your name and phone number after you pick.)"
        )
        self._set_response(ctx, response, structured_data={"slots": slots, "params": params})

    async def _handle_slot_selection(self, ctx: SessionContextBlock, msg: str):
        slots = ctx.agent_workspace.scratch.get("slots_shown", [])
        selected_idx = None
        for i, c in enumerate(["1", "2", "3", "first", "second", "third"]):
            if c in msg.lower():
                selected_idx = i % 3
                break
        if selected_idx is None:
            self._set_response(ctx, "Which slot would you prefer? Please say 1, 2, or 3.")
            return
        selected = slots[selected_idx]
        ctx.agent_workspace.scratch["selected_slot"] = selected
        response = (
            f"Great! I've selected {selected['datetime']} with {selected['doctor']}. "
            "To hold this slot, I just need your name and mobile number."
        )
        self._set_response(ctx, response, structured_data={"selected_slot": selected})

    async def _close_booking(self, ctx: SessionContextBlock, msg: str):
        slot = ctx.agent_workspace.scratch.get("selected_slot", {})
        pv = ctx.context.patient_view
        name = pv.get("name", "the patient")
        ref = f"APT-NEW-{name.split()[-1].upper()[:4]}-001"
        response = (
            f"Your appointment is confirmed!\n"
            f"• Doctor: {slot.get('doctor', 'TBD')}\n"
            f"• When: {slot.get('datetime', 'TBD')}\n"
            f"• Reference: {ref}\n"
            "You'll receive an SMS and WhatsApp confirmation. "
            "Would you like to complete your registration now (optional — takes 2 minutes)?"
        )
        self._log_mutation(ctx, "fhir:Appointment+Patient", ref, "First-visit booking via onboarding agent")
        self._set_response(ctx, response, outcome="success")
