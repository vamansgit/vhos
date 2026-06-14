"""Agent 11: Lifestyle Coach Agent — nutrition, activity, milestones with IoT integration."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class LifestyleCoachAgent(VhosAgent):
    agent_id = "lifestyle_coach"
    pillar = "g_care"
    domain = "engagement"
    registered_intents = ["Provide_Nutrition_Advice", "Track_Activity_Goals", "Motivate_Patient", "Recovery_Milestone_Check"]
    required_auth_level = AuthLevel.LOW
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.72
    ESC_MAX = 0.05

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if intent == "Recovery_Milestone_Check" or "milestone" in msg or "recovery" in msg:
            await self._milestone_check(ctx, msg)
        elif intent == "Track_Activity_Goals" or any(w in msg for w in ["steps", "walk", "exercise", "activity", "heart rate"]):
            await self._track_activity(ctx)
        elif intent == "Motivate_Patient" or any(w in msg for w in ["motivat", "encourag", "keep going", "struggling"]):
            await self._motivate(ctx)
        else:
            await self._nutrition_advice(ctx, msg)
        await self.return_control(ctx)

    async def _nutrition_advice(self, ctx: SessionContextBlock, msg: str):
        pv = ctx.context.patient_view
        condition = pv.get("primary_condition", "general")
        if "diabet" in condition.lower():
            advice = (
                "Pre-meal tip: start with a small portion of complex carbohydrates (like a handful of whole grains) "
                "before eating protein and vegetables. This helps manage blood sugar levels. "
                "[This reinforces your care plan — always follow your dietitian's specific guidance]"
            )
        elif "cardiac" in condition.lower() or "heart" in condition.lower():
            advice = (
                "Heart-healthy meal reminder: choose foods low in saturated fat and sodium. "
                "Good choices include fish, nuts, fruits, and vegetables. "
                "[As recommended in your care plan — always follow your doctor's specific dietary instructions]"
            )
        else:
            advice = (
                "General nutrition reminder: aim for a balanced plate — "
                "half vegetables, quarter whole grains, quarter lean protein. "
                "Stay hydrated with 6–8 glasses of water daily. "
                "[General wellness guidance — consult your dietitian for personalised advice]"
            )
        self._set_response(ctx, advice)

    async def _track_activity(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        # In production: fetch from Graviton IoT Cloud (mTLS, vital_signal_v1)
        steps_today = pv.get("iot_steps_today", 4200)
        target = pv.get("care_plan_steps_target", 6000)
        remaining = max(0, target - steps_today)
        hr = pv.get("iot_heart_rate_avg", 72)

        if remaining == 0:
            response = (
                f"Excellent! You've hit your daily step goal of {target:,} steps. "
                f"Average heart rate today: {hr} bpm. "
                "Keep it up — consistency is the key to recovery!"
            )
        else:
            response = (
                f"You've taken {steps_today:,} steps today — {remaining:,} more to reach your goal of {target:,}. "
                f"Average heart rate: {hr} bpm. "
                "You're making great progress — even a short walk counts!"
            )
        self._set_response(ctx, response, structured_data={"steps": steps_today, "target": target, "hr": hr})

    async def _motivate(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        streak_days = pv.get("activity_streak_days", 14)
        if streak_days > 0:
            response = (
                f"This is your {streak_days}th day of consistent activity — that's a streak worth celebrating! "
                "Each day you stay on track strengthens your recovery. "
                "You're doing wonderfully!"
            )
        else:
            response = (
                "It's completely okay to have an off day. "
                "What matters is that you're here and ready to try again. "
                "Is everything okay? Would you like me to let your care team know?"
            )
        self._set_response(ctx, response)

    async def _milestone_check(self, ctx: SessionContextBlock, msg: str):
        pv = ctx.context.patient_view
        day = pv.get("recovery_day", 14)
        procedure = pv.get("procedure", "your procedure")
        pain_vas = pv.get("pain_vas", None)
        mobility_score = pv.get("mobility_score", None)

        questions = []
        if pain_vas is None:
            questions.append("On a scale of 0 to 10, how would you rate your pain right now?")
        if mobility_score is None:
            questions.append("How would you describe your mobility — normal, slightly limited, or significantly limited?")

        if questions:
            response = (
                f"You're on day {day} of recovery from {procedure}. "
                "I'd like to record a milestone check. " + " ".join(questions)
            )
        else:
            # Flag if regression
            if int(pain_vas or 0) > 7 or str(mobility_score) == "significantly limited":
                self._handback(ctx, reason="Regression detected at milestone check", next_intent="treatment_tracker")
                response = (
                    "I've noted some concerns in your recovery progress. "
                    "I'm flagging this to your treatment coordinator for review."
                )
            else:
                response = (
                    f"Day {day} milestone check complete. "
                    f"Pain: {pain_vas}/10. Mobility: {mobility_score}. "
                    "Your recovery looks on track! I'll update your care team."
                )
            self._log_mutation(ctx, "fhir:Observation.milestone", f"Day {day}", f"Milestone check: pain={pain_vas}, mobility={mobility_score}")
        self._set_response(ctx, response)
