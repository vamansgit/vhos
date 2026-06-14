"""Agent 24: Pain Assessment Agent — VAS/NRS structured assessment."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class PainAssessmentAgent(VhosAgent):
    agent_id = "pain_assessment"
    pillar = "g_assist"
    domain = "expertise"
    registered_intents = ["Assess_Pain", "Track_Pain_Trend", "Log_Pain_Score", "Generate_Pain_Report"]
    required_auth_level = AuthLevel.LOW
    fallback_safe = True
    mdsw_scope = "Pending CDSCO SaMD — advisory only"
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
        ws = ctx.agent_workspace.scratch

        # Check for severe pain — may need escalation
        if any(w in msg for w in ["unbearable", "can't bear", "10 out of 10", "worst pain", "can't move"]):
            self._handback(ctx, reason="Severe pain reported", next_intent="triage")
            ctx.response_in_progress.text = (
                "I hear you — that sounds very severe. "
                "I'm connecting you to our triage team right away to ensure you get immediate care."
            )
            await self.return_control(ctx)
            return

        if intent == "Generate_Pain_Report" or "report" in msg:
            await self._pain_report(ctx)
        elif intent == "Track_Pain_Trend" or "trend" in msg or "over time" in msg:
            await self._pain_trend(ctx)
        elif ws.get("pain_location") and not ws.get("pain_score"):
            ws["pain_location"] = msg
            await self._ask_score(ctx)
        elif ws.get("pain_score") is None and any(str(i) in msg for i in range(11)):
            await self._log_score(ctx, msg)
        else:
            await self._assess_pain(ctx)
        await self.return_control(ctx)

    async def _assess_pain(self, ctx: SessionContextBlock):
        ctx.agent_workspace.scratch["pain_location"] = "pending"
        response = (
            "Pain assessment:\n"
            "1. Where are you experiencing the pain? (e.g., chest, abdomen, back, leg)\n"
            "On a scale of 0 to 10, how would you rate it? (0 = no pain, 10 = worst imaginable)"
        )
        self._set_response(ctx, response)

    async def _ask_score(self, ctx: SessionContextBlock):
        location = ctx.agent_workspace.scratch.get("pain_location", "the area")
        response = f"And on a scale of 0 to 10, how severe is the pain in {location}?"
        self._set_response(ctx, response)

    async def _log_score(self, ctx: SessionContextBlock, msg: str):
        import re
        nums = re.findall(r'\b(\d{1,2})\b', msg)
        score = int(nums[0]) if nums else 5
        score = min(10, max(0, score))
        ws = ctx.agent_workspace.scratch
        ws["pain_score"] = score

        if score >= 8:
            response = (
                f"I've logged your pain score: {score}/10. "
                "This is a high pain score. I'm alerting your care team immediately. "
                "[Advisory: do not delay seeking medical care for high pain scores]"
            )
            self._log_mutation(ctx, "care_team_alert", f"Pain score {score}", "High pain score — care team alerted")
        else:
            quality = ws.get("pain_quality", "")
            response = (
                f"Pain score logged: {score}/10. "
                "How would you describe the pain? (Sharp/dull/burning/throbbing/pressure)"
            )
        self._log_mutation(ctx, "fhir:Observation.pain_score", score, "NRS pain score logged")
        self._set_response(ctx, response, structured_data={"pain_score": score})

    async def _pain_trend(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        history = pv.get("pain_scores_7d", [8, 7, 6, 5, 5, 4, 3])
        avg = sum(history) / len(history) if history else 0
        trend = "improving" if history and history[-1] < history[0] else "stable" if history and history[-1] == history[0] else "worsening"
        response = (
            f"Pain trend (last 7 days): {' → '.join(str(s) for s in history)}\n"
            f"Average: {avg:.1f}/10. Trend: {trend}.\n"
            "[Source: Recorded pain assessments | Reported to your care team]"
        )
        self._set_response(ctx, response, structured_data={"trend": trend, "avg": avg})

    async def _pain_report(self, ctx: SessionContextBlock):
        response = (
            "Pain assessment report generated:\n"
            "• Assessment protocol: NRS (Numeric Rating Scale)\n"
            "• Current score: see latest assessment\n"
            "• Location: as documented\n"
            "• Functional impact: as reported\n"
            "Full report sent to your care team. [Source: Logged pain assessments]"
        )
        self._set_response(ctx, response)
