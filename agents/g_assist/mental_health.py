"""Agent 25: Mental Health Agent — PHQ-9/GAD-7, crisis pathway."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent

CRISIS_KEYWORDS = [
    "suicide", "suicidal", "kill myself", "end my life", "don't want to live",
    "better off dead", "harming myself", "self-harm", "overdose intentional",
    "no reason to live", "want to die",
]

PHQ9_QUESTIONS = [
    "Little interest or pleasure in doing things",
    "Feeling down, depressed, or hopeless",
    "Trouble sleeping or sleeping too much",
    "Feeling tired or having little energy",
    "Poor appetite or overeating",
    "Feeling bad about yourself",
    "Trouble concentrating",
    "Moving or speaking slowly (or being fidgety/restless)",
    "Thoughts of being better off dead or hurting yourself",
]


class MentalHealthAgent(VhosAgent):
    agent_id = "mental_health"
    pillar = "g_assist"
    domain = "expertise"
    registered_intents = ["PHQ9_Screening", "GAD7_Screening", "Crisis_Response", "Mental_Health_Referral"]
    required_auth_level = AuthLevel.MEDIUM
    fallback_safe = False
    mdsw_scope = "Pending CDSCO SaMD — advisory only"
    KPI_TARGET = 0.85
    ESC_MAX = 0.15

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message()
        lower = msg.lower()

        # Crisis check — NEVER leave patient alone
        for kw in CRISIS_KEYWORDS:
            if kw in lower:
                await self._crisis_response(ctx)
                await self.return_control(ctx)
                return

        intent = ctx.goal
        ws = ctx.agent_workspace.scratch

        if intent == "GAD7_Screening" or "anxiety" in lower or "anxious" in lower or "worry" in lower:
            await self._gad7(ctx, ws)
        elif intent == "Mental_Health_Referral" or "referral" in lower:
            await self._referral(ctx)
        elif ws.get("phq9_in_progress"):
            await self._phq9_continue(ctx, msg, ws)
        else:
            await self._phq9_start(ctx)
        await self.return_control(ctx)

    async def _crisis_response(self, ctx: SessionContextBlock):
        self._escalate(ctx, reason="Mental health crisis keywords", target="mental_health_crisis")
        response = (
            "I hear you, and I want you to know your feelings are valid. "
            "You're not alone — I'm connecting you right now to a mental health specialist who can talk with you. "
            "Please stay with me. Help is here.\n\n"
            "If you're in immediate danger, please call:\n"
            "• iCall: 9152987821\n"
            "• Vandrevala Foundation: 1860-2662-345 (24/7, free)\n"
            "• NIMHANS: 080-46110007\n"
            "[This conversation is being escalated to our mental health team right now]"
        )
        ctx.response_in_progress.text = response

    async def _phq9_start(self, ctx: SessionContextBlock):
        ctx.agent_workspace.scratch["phq9_in_progress"] = True
        ctx.agent_workspace.scratch["phq9_q"] = 0
        ctx.agent_workspace.scratch["phq9_scores"] = []
        response = (
            "I'd like to check in on your mental wellbeing with a brief screening. "
            "Over the last 2 weeks, how often have you been bothered by:\n\n"
            f"1. {PHQ9_QUESTIONS[0]}\n\n"
            "Please answer: Not at all / Several days / More than half the days / Nearly every day"
        )
        self._set_response(ctx, response)

    async def _phq9_continue(self, ctx: SessionContextBlock, msg: str, ws: dict):
        score_map = {"not at all": 0, "several days": 1, "more than half": 2, "nearly every day": 3}
        score = next((v for k, v in score_map.items() if k in msg.lower()), 1)
        ws["phq9_scores"].append(score)
        q_num = ws["phq9_q"] + 1
        ws["phq9_q"] = q_num

        # Crisis check on Q9 (suicidal ideation)
        if q_num - 1 == 8 and score >= 1:
            await self._crisis_response(ctx)
            return

        if q_num >= len(PHQ9_QUESTIONS):
            # Calculate and present result
            total = sum(ws["phq9_scores"])
            if total >= 20:
                severity = "Severe depression"
            elif total >= 15:
                severity = "Moderately severe depression"
            elif total >= 10:
                severity = "Moderate depression"
            elif total >= 5:
                severity = "Mild depression"
            else:
                severity = "Minimal depression"

            ws["phq9_in_progress"] = False
            response = (
                f"PHQ-9 screening complete. Score: {total}/27 — {severity}.\n"
                "[Advisory only — this is a screening tool, not a diagnosis. "
                "Please discuss results with your doctor or mental health professional.]\n"
                + ("I'd strongly recommend speaking to a mental health professional soon." if total >= 10 else
                   "Thank you for completing this screening. Your care team has been notified of your results.")
            )
            self._log_mutation(ctx, "fhir:Observation.phq9", total, f"PHQ-9 score: {total} — {severity}")
        else:
            response = (
                f"{q_num + 1}. {PHQ9_QUESTIONS[q_num]}\n\n"
                "Not at all / Several days / More than half the days / Nearly every day"
            )
        self._set_response(ctx, response)

    async def _gad7(self, ctx: SessionContextBlock, ws: dict):
        response = (
            "GAD-7 Anxiety Screening:\n"
            "Over the last 2 weeks, how often have you been bothered by:\n"
            "• Feeling nervous, anxious, or on edge\n"
            "• Not being able to stop or control worrying\n"
            "(0-3 scale: Not at all / Several days / More than half / Nearly every day)\n"
            "[This is a screening tool — not a diagnosis. Results shared with your care team.]"
        )
        self._set_response(ctx, response)

    async def _referral(self, ctx: SessionContextBlock):
        response = (
            "I'm arranging a referral to our mental health team. "
            "You'll be contacted within 48 hours. "
            "In the meantime, if you feel you need immediate support, "
            "please call iCall: 9152987821 (Mon–Sat, 8 AM–10 PM)."
        )
        self._log_mutation(ctx, "fhir:ServiceRequest.mental_health_referral", "active", "Mental health referral created")
        self._set_response(ctx, response, outcome="success")
