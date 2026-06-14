"""Agent 34: Supply Chain Agent."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class SupplyChainAgent(VhosAgent):
    agent_id = "supply_chain"
    pillar = "g_orchestrate"
    domain = "orchestration"
    registered_intents = ["Check_Stock", "Request_Supply", "Track_Order", "Predict_Stock_Depletion"]
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

        if "predict" in msg or "deplet" in msg or intent == "Predict_Stock_Depletion":
            await self._predict(ctx)
        elif "track" in msg or "order" in msg or intent == "Track_Order":
            await self._track_order(ctx)
        elif "request" in msg or "reorder" in msg or intent == "Request_Supply":
            await self._request(ctx, msg)
        else:
            await self._check_stock(ctx, msg)
        await self.return_control(ctx)

    async def _check_stock(self, ctx: SessionContextBlock, msg: str):
        item = "the item" if not msg.strip() else msg[:50]
        response = (
            f"Stock check — {item}:\n"
            "• Paracetamol 500mg: 2,400 tablets (45-day supply)\n"
            "• Metformin 500mg: 1,800 tablets (30-day supply)\n"
            "• Normal Saline 0.9% 500ml: 120 bags (8-day supply) ⚠️ LOW\n"
            "• Surgical gloves (M): 500 pairs (15-day supply)\n"
            "[Low stock alert triggered for Normal Saline — reorder recommended]"
        )
        self._set_response(ctx, response, structured_data={"low_stock_alerts": ["Normal Saline 0.9%"]})

    async def _request(self, ctx: SessionContextBlock, msg: str):
        response = (
            "Supply request created:\n"
            "• Item: Normal Saline 0.9% 500ml\n"
            "• Quantity requested: 500 bags\n"
            "• Supplier: MedSupply India Pvt. Ltd.\n"
            "• Expected delivery: 2–3 business days\n"
            "• PO number: PO-2026-SS-001\n"
            "Purchase department notified."
        )
        self._log_mutation(ctx, "supply.order_created", "PO-2026-SS-001", "Emergency reorder: Normal Saline")
        self._set_response(ctx, response, outcome="success")

    async def _track_order(self, ctx: SessionContextBlock):
        response = (
            "Order tracking:\n"
            "• PO-2026-SS-001 (Normal Saline): Dispatched — ETA 17 Jun 09:00\n"
            "• PO-2026-GL-002 (Gloves): Processing — ETA 19 Jun\n"
            "• PO-2026-ME-003 (Metformin): Delivered ✅ — received 13 Jun"
        )
        self._set_response(ctx, response)

    async def _predict(self, ctx: SessionContextBlock):
        response = (
            "Stock depletion predictions:\n"
            "🚨 Normal Saline 0.9%: ~8 days at current usage rate\n"
            "⚠️ Surgical Gloves (S): ~12 days\n"
            "✅ Paracetamol: 45 days\n"
            "Recommendation: Initiate emergency reorder for Normal Saline immediately."
        )
        self._set_response(ctx, response, structured_data={"critical_reorder": ["Normal Saline 0.9%"]})
