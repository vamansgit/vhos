"""Agent 38: Yield Agent — revenue optimisation, capacity."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class YieldAgent(VhosAgent):
    agent_id = "yield_agent"
    pillar = "g_insights"
    domain = "insights"
    registered_intents = ["Analyse_Revenue_Opportunity", "Optimise_Capacity", "Generate_Campaign_Brief", "Track_Yield_Metrics"]
    required_auth_level = AuthLevel.PROVIDER
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.80
    ESC_MAX = 0.02

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if "campaign" in msg or intent == "Generate_Campaign_Brief":
            await self._campaign_brief(ctx)
        elif "capacity" in msg or intent == "Optimise_Capacity":
            await self._capacity(ctx)
        elif "metric" in msg or "kpi" in msg or intent == "Track_Yield_Metrics":
            await self._metrics(ctx)
        else:
            await self._revenue_opportunity(ctx)
        await self.return_control(ctx)

    async def _revenue_opportunity(self, ctx: SessionContextBlock):
        response = (
            "Revenue opportunity analysis:\n"
            "• Unfilled OT slots (this week): 6 cases lost — est. ₹3.2L revenue\n"
            "• Lapsed patients (12+ months): 342 patients eligible for re-engagement\n"
            "• Preventive health check-up programme: 45% below target conversion\n"
            "• High-value specialty: Cardiology — 18% slot underutilisation\n"
            "Recommended action: Re-engagement campaign + OT slot optimisation"
        )
        self._set_response(ctx, response, structured_data={"opportunity_value_lakhs": 3.2})

    async def _capacity(self, ctx: SessionContextBlock):
        response = (
            "Capacity optimisation:\n"
            "• Peak hours: 10 AM–1 PM (OPD) — 93% utilisation\n"
            "• Off-peak: 2–5 PM — 61% utilisation\n"
            "• OT: Tuesday/Thursday 65% vs Monday/Wednesday 91%\n"
            "• Recommendation: Incentivise afternoon appointments, redistribute OT list\n"
            "• Potential efficiency gain: +12% throughput without adding capacity"
        )
        self._set_response(ctx, response)

    async def _campaign_brief(self, ctx: SessionContextBlock):
        response = (
            "Campaign brief generated:\n"
            "• Target cohort: Cardiac patients, last visit > 9 months, age 45–70\n"
            "• Campaign: Annual cardiac check-up re-engagement\n"
            "• Cohort size: 127 patients (opt-outs excluded)\n"
            "• Target conversion: 30%\n"
            "• Estimated revenue: ₹6.4L\n"
            "• Requires compliance officer approval before launch\n"
            "Brief sent to Proactive Outreach Agent for execution upon approval."
        )
        self._set_response(ctx, response)

    async def _metrics(self, ctx: SessionContextBlock):
        response = (
            "Yield KPIs (current month):\n"
            "• Revenue per bed day: ₹12,400 (target: ₹12,000) ✅\n"
            "• ALOS: 3.8 days (target: ≤4.0) ✅\n"
            "• OPD conversion (repeat visit): 68% (target: ≥65%) ✅\n"
            "• Package utilisation: 52% ⚠️ (target: ≥60%)\n"
            "• Campaign conversion: 28% ⚠️ (target: ≥30%)"
        )
        self._set_response(ctx, response)
