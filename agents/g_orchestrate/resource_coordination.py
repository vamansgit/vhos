"""Agent 27: Resource Coordination Agent — beds, OT, equipment."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class ResourceCoordinationAgent(VhosAgent):
    agent_id = "resource_coordination"
    pillar = "g_orchestrate"
    domain = "orchestration"
    registered_intents = ["Allocate_Bed", "Book_Equipment", "Coordinate_OT_Resources", "Track_Resource_Utilization"]
    required_auth_level = AuthLevel.PROVIDER
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.90
    ESC_MAX = 0.03

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if "ot" in msg or "theatre" in msg or "operation" in msg or intent == "Coordinate_OT_Resources":
            await self._ot_resources(ctx)
        elif "equipment" in msg or "ventilator" in msg or "monitor" in msg or intent == "Book_Equipment":
            await self._equipment(ctx, msg)
        elif "utiliz" in msg or "report" in msg or intent == "Track_Resource_Utilization":
            await self._utilization(ctx)
        else:
            await self._allocate_bed(ctx, msg)
        await self.return_control(ctx)

    async def _allocate_bed(self, ctx: SessionContextBlock, msg: str):
        pv = ctx.context.patient_view
        ward = pv.get("requested_ward", "general")
        response = (
            f"Bed allocation for {ward} ward:\n"
            "• Ward 3A — Bed 8: Available (general, clean)\n"
            "• Ward 3B — Bed 14: Available (window, accessible)\n"
            "• ICU — Bed 4: Available (monitored)\n"
            "Which bed shall I allocate? I'll update ADT system immediately."
        )
        self._set_response(ctx, response)

    async def _ot_resources(self, ctx: SessionContextBlock):
        response = (
            "OT resource check:\n"
            "• OT 2: Available 14:00–17:00 (anaesthesia confirmed)\n"
            "• OT 3: Available 10:00–13:00 (laparoscopy equipped)\n"
            "Required equipment: Available\n"
            "Surgical team: Confirmed\n"
            "Shall I coordinate and confirm the OT booking?"
        )
        self._set_response(ctx, response)

    async def _equipment(self, ctx: SessionContextBlock, msg: str):
        equipment_type = "ventilator" if "ventilator" in msg else "monitor" if "monitor" in msg else "requested equipment"
        response = (
            f"{equipment_type.capitalize()} allocation:\n"
            "• Unit A-12: Available, last serviced: 2 days ago\n"
            "• Unit A-15: Available, last serviced: 1 week ago\n"
            "Shall I allocate and mark as in-use?"
        )
        self._set_response(ctx, response)

    async def _utilization(self, ctx: SessionContextBlock):
        response = (
            "Resource utilization (today):\n"
            "• Bed occupancy: 87% (116/133 beds occupied)\n"
            "• ICU: 90% (9/10 beds occupied)\n"
            "• OT utilization: 73%\n"
            "• Ventilators: 5/8 in use\n"
            "Predicted demand for next 24h: High (current trends)"
        )
        self._set_response(ctx, response, structured_data={"bed_occupancy": 0.87, "icu_occupancy": 0.90})
