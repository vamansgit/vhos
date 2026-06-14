"""Agent 41: Operational Insights Agent."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class OperationalInsightsAgent(VhosAgent):
    agent_id = "operational_insights"
    pillar = "g_insights"
    domain = "insights"
    registered_intents = ["Daily_Operations_Brief", "Identify_Bottleneck", "Capacity_Forecast", "Staff_Utilisation"]
    required_auth_level = AuthLevel.PROVIDER
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.85
    ESC_MAX = 0.02

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if "bottleneck" in msg or intent == "Identify_Bottleneck":
            await self._bottleneck(ctx)
        elif "forecast" in msg or "capacity" in msg or intent == "Capacity_Forecast":
            await self._forecast(ctx)
        elif "staff" in msg or intent == "Staff_Utilisation":
            await self._staff(ctx)
        else:
            await self._daily_brief(ctx)
        await self.return_control(ctx)

    async def _daily_brief(self, ctx: SessionContextBlock):
        response = (
            "Daily operations brief — 14 Jun 2026, 08:00:\n"
            "• Bed occupancy: 87% (116/133)\n"
            "• Emergency admissions (last 24h): 14\n"
            "• Elective admissions today: 8 planned\n"
            "• Planned discharges today: 11\n"
            "• OT: 4 cases scheduled, 1 in progress\n"
            "• Staff: All wards fully staffed\n"
            "• Alerts: 2 deteriorating patients (reviewed)\n"
            "• Quality: No critical incidents last 24h ✅"
        )
        self._set_response(ctx, response)

    async def _bottleneck(self, ctx: SessionContextBlock):
        response = (
            "Operational bottlenecks identified:\n"
            "🔴 ED waiting time: 3.2h average (target: <2h)\n"
            "🔴 Lab TAT for urgent: 92min (SLA: <90min)\n"
            "⚠️ OPD registration queue: 18 patients waiting (avg 22 min wait)\n"
            "✅ Pharmacy dispensing: Within target\n"
            "Root cause: Radiology reporting backlog affecting ED clearance"
        )
        self._set_response(ctx, response, structured_data={"critical_bottlenecks": ["ED wait time", "Lab TAT"]})

    async def _forecast(self, ctx: SessionContextBlock):
        response = (
            "Capacity forecast (next 7 days):\n"
            "• Mon: High demand (89% projected occupancy)\n"
            "• Tue: Very high (94% — consider elective review)\n"
            "• Wed: Moderate (79%)\n"
            "• Thu–Fri: High (86–88%)\n"
            "• Weekend: Low (68–72%)\n"
            "Recommendation: Review Tuesday elective list by Sunday."
        )
        self._set_response(ctx, response)

    async def _staff(self, ctx: SessionContextBlock):
        response = (
            "Staff utilisation (today):\n"
            "• Doctors: 94% (18/19 rostered in)\n"
            "• Nurses: 97% (32/33 rostered)\n"
            "• Ward 3A: 1 nurse short — covered by float nurse\n"
            "• OT: Fully staffed\n"
            "• Bank/agency usage: 1 HCA (3% premium cost)"
        )
        self._set_response(ctx, response)
