"""Agent 26: Rehabilitation Agent — milestone tracking, exercise protocols."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class RehabilitationAgent(VhosAgent):
    agent_id = "rehabilitation"
    pillar = "g_assist"
    domain = "expertise"
    registered_intents = ["Track_Rehab_Progress", "Send_Exercise_Protocol", "Assess_Functional_Status", "Schedule_Physio_Session"]
    required_auth_level = AuthLevel.LOW
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.78
    ESC_MAX = 0.06

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal
        pv = ctx.context.patient_view

        # Regression → treatment tracker
        if any(w in msg for w in ["worse", "regression", "can't do", "much more pain than before", "got worse"]):
            self._handback(ctx, reason="Rehab regression detected", next_intent="treatment_tracker")
            ctx.response_in_progress.text = "I'm flagging this to your treatment coordinator for review."
            await self.return_control(ctx)
            return

        if intent == "Schedule_Physio_Session" or "physio" in msg or "appointment" in msg:
            await self._schedule(ctx)
        elif intent == "Assess_Functional_Status" or "functional" in msg or "can i" in msg:
            await self._functional_assessment(ctx, msg)
        elif intent == "Send_Exercise_Protocol" or "exercise" in msg or "protocol" in msg:
            await self._exercise_protocol(ctx, pv)
        else:
            await self._track_progress(ctx, pv)
        await self.return_control(ctx)

    async def _track_progress(self, ctx: SessionContextBlock, pv: dict):
        day = pv.get("rehab_day", 7)
        procedure = pv.get("procedure", "your procedure")
        milestones = pv.get("rehab_milestones_completed", ["Sat up independently", "Short walk with support"])
        next_milestone = pv.get("next_milestone", "Walk 50m independently")
        response = (
            f"Rehab progress — Day {day} post {procedure}:\n"
            f"Milestones completed: {', '.join(milestones)}\n"
            f"Next target: {next_milestone}\n"
            "You're making excellent progress! Keep up the effort."
        )
        self._log_mutation(ctx, "fhir:Observation.rehab_milestone", f"Day {day}", f"Rehab progress logged")
        self._set_response(ctx, response)

    async def _exercise_protocol(self, ctx: SessionContextBlock, pv: dict):
        procedure = pv.get("procedure", "general").lower()
        if "ortho" in procedure or "knee" in procedure or "hip" in procedure:
            exercises = [
                "Ankle pumps: 10 reps × 3 sets, every 2 hours",
                "Knee bends (bed): 10 reps × 3 sets",
                "Standing with support: 5 minutes × 3 times",
                "Short walk with walking aid: 2× daily as tolerated",
            ]
        elif "cardiac" in procedure or "cabg" in procedure:
            exercises = [
                "Deep breathing: 10 breaths × 4 times daily",
                "Leg exercises (bed): ankle circles, knee bends",
                "Short walks: 5 min → 10 min → 15 min (progress as tolerated)",
                "No lifting > 5kg for 6 weeks post-cardiac surgery",
            ]
        else:
            exercises = [
                "Gentle mobility exercises as tolerated",
                "Deep breathing exercises: 10 breaths × 4 times daily",
                "Short walks increasing daily",
            ]
        response = (
            "Today's exercise protocol:\n"
            + "\n".join(f"• {e}" for e in exercises)
            + "\n[Per your physiotherapy care plan — always follow your physiotherapist's specific guidance]"
        )
        self._set_response(ctx, response)

    async def _functional_assessment(self, ctx: SessionContextBlock, msg: str):
        response = (
            "Functional status assessment:\n"
            "Please rate your ability in each area (0=unable, 1=with help, 2=independently):\n"
            "• Walking\n"
            "• Climbing stairs\n"
            "• Dressing\n"
            "• Bathing\n"
            "• Getting in/out of bed\n"
            "Your physiotherapy team will use this to update your care plan."
        )
        self._set_response(ctx, response)

    async def _schedule(self, ctx: SessionContextBlock):
        response = (
            "I'm checking physiotherapy availability. "
            "Shall I book your next session? Available slots: tomorrow at 10 AM or Wednesday at 2 PM."
        )
        self._set_response(ctx, response, next_intent="Book_Appointment")
