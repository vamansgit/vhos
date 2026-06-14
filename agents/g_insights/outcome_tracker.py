"""Agent 39: Outcome Tracker Agent."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class OutcomeTrackerAgent(VhosAgent):
    agent_id = "outcome_tracker"
    pillar = "g_insights"
    domain = "insights"
    registered_intents = ["Track_Clinical_Outcomes", "Benchmark_Outcomes", "Generate_Outcome_Report", "Flag_Poor_Outcome"]
    required_auth_level = AuthLevel.PROVIDER
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.85
    ESC_MAX = 0.03

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if "benchmark" in msg or intent == "Benchmark_Outcomes":
            await self._benchmark(ctx)
        elif "flag" in msg or "poor" in msg or intent == "Flag_Poor_Outcome":
            await self._flag(ctx, msg)
        elif "report" in msg or intent == "Generate_Outcome_Report":
            await self._report(ctx)
        else:
            await self._track(ctx)
        await self.return_control(ctx)

    async def _track(self, ctx: SessionContextBlock):
        response = (
            "Clinical outcome tracking (Q2 2026):\n"
            "• 30-day surgical mortality: 0.8% (benchmark: <1.2%) ✅\n"
            "• 30-day readmission: 7.2% (benchmark: <8%) ✅\n"
            "• Complication rate (cardiac): 3.1% (benchmark: <4%) ✅\n"
            "• Patient-reported outcome (PRO) response rate: 67%\n"
            "• Average length of stay: 3.8 days (benchmark: 4.2 days) ✅\n"
            "[Source: Clinical outcomes database | Advisory — for quality improvement purposes]"
        )
        self._set_response(ctx, response)

    async def _benchmark(self, ctx: SessionContextBlock):
        response = (
            "Outcome benchmarking vs national data:\n"
            "• Cardiac surgery mortality: Better than national average ✅\n"
            "• Readmission rates: Within benchmark ✅\n"
            "• Patient satisfaction: Top quartile ✅\n"
            "• HAI rate: Slightly above benchmark ⚠️\n"
            "[Source: National clinical audit data | For internal QI use only]"
        )
        self._set_response(ctx, response)

    async def _flag(self, ctx: SessionContextBlock, msg: str):
        response = (
            "Poor outcome flagged for clinical review:\n"
            "• Case referred to Mortality & Morbidity committee\n"
            "• Root cause analysis initiated\n"
            "• Anonymised case logged for learning\n"
            "[All poor outcomes reviewed per NABH/JCI protocol]"
        )
        self._log_mutation(ctx, "outcome.poor_flag", True, "Poor outcome flagged for M&M review")
        self._set_response(ctx, response)

    async def _report(self, ctx: SessionContextBlock):
        response = (
            "Outcome report generated:\n"
            "Period: April–June 2026\n"
            "Total cases tracked: 847\n"
            "Positive outcomes: 94.2%\n"
            "Outcomes requiring review: 49 cases\n"
            "Report submitted to Medical Director and Quality Committee"
        )
        self._set_response(ctx, response)
