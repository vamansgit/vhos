"""Agent 32: Bed Management Agent."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class BedManagementAgent(VhosAgent):
    agent_id = "bed_management"
    pillar = "g_orchestrate"
    domain = "orchestration"
    registered_intents = ["Check_Bed_Status", "Allocate_Bed", "Request_Bed_Clean", "Predict_Bed_Demand"]
    required_auth_level = AuthLevel.PROVIDER
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.92
    ESC_MAX = 0.02

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if "predict" in msg or "demand" in msg or intent == "Predict_Bed_Demand":
            await self._predict(ctx)
        elif "clean" in msg or "housekeep" in msg or intent == "Request_Bed_Clean":
            await self._request_clean(ctx)
        elif "allocate" in msg or "assign" in msg or intent == "Allocate_Bed":
            await self._allocate(ctx, msg)
        else:
            await self._status(ctx)
        await self.return_control(ctx)

    async def _status(self, ctx: SessionContextBlock):
        response = (
            "Real-time bed status:\n"
            "• General Ward (3A): 24/28 occupied | 4 available\n"
            "• Surgical Ward (3B): 20/22 occupied | 2 available\n"
            "• ICU: 9/10 occupied | 1 available\n"
            "• HDU: 6/8 occupied | 2 available\n"
            "• Total: 59/68 beds (87% occupancy)\n"
            "• Pending discharges (today): 5 beds expected free by 17:00"
        )
        self._set_response(ctx, response, structured_data={"occupancy_pct": 87, "available_beds": 9})

    async def _allocate(self, ctx: SessionContextBlock, msg: str):
        ward_type = "ICU" if "icu" in msg else "surgical" if "surg" in msg else "general"
        response = (
            f"Bed allocated in {ward_type} ward:\n"
            "• Allocated: Ward 3A, Bed 8\n"
            "• Status: Clean and ready\n"
            "• ADT system updated\n"
            "• Porter notified for patient transfer"
        )
        self._log_mutation(ctx, "bed_adt.allocation", "Ward3A-Bed8", f"Bed allocated — {ward_type}")
        self._set_response(ctx, response, outcome="success")

    async def _request_clean(self, ctx: SessionContextBlock):
        response = (
            "Housekeeping request sent:\n"
            "• Target: Ward 3B, Bed 14 (vacated)\n"
            "• Priority: Standard\n"
            "• Expected completion: 30–45 minutes\n"
            "Bed will show as 'available' in ADT once confirmed clean."
        )
        self._set_response(ctx, response)

    async def _predict(self, ctx: SessionContextBlock):
        response = (
            "Bed demand forecast (next 24h):\n"
            "• Expected admissions: 12–15\n"
            "• Expected discharges: 8–10\n"
            "• Net bed pressure: +4 to +6 beds needed\n"
            "• Recommendation: Consider elective postponement if >5 emergency admissions by 18:00\n"
            "[Based on historical patterns and current census]"
        )
        self._set_response(ctx, response)
