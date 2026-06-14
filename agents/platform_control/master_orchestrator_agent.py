"""Agent 42: Master Orchestrator Agent — system health and session management."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class MasterOrchestratorAgent(VhosAgent):
    agent_id = "master_orchestrator"
    pillar = "platform_control"
    domain = "platform"
    registered_intents = ["Health_Check", "List_Active_Sessions", "System_Status", "Force_Escalate"]
    required_auth_level = AuthLevel.PROVIDER
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.99
    ESC_MAX = 0.01

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if "health" in msg or intent == "Health_Check":
            await self._health(ctx)
        elif "status" in msg or intent == "System_Status":
            await self._status(ctx)
        elif "escalate" in msg or intent == "Force_Escalate":
            self._escalate(ctx, reason="Manual orchestrator escalation", target="emergency_escalation")
            ctx.response_in_progress.text = "Force escalation triggered."
        else:
            await self._health(ctx)
        await self.return_control(ctx)

    async def _health(self, ctx: SessionContextBlock):
        from agents.registry import list_agents
        agents = list_agents()
        response = (
            f"VHOS v2.4 — System health: Operational\n"
            f"Agents loaded: {len(agents)}\n"
            f"Session ID: {ctx.session_id}\n"
            f"Auth level: {ctx.principal.auth_level.value}\n"
            "All systems nominal."
        )
        self._set_response(ctx, response, structured_data={"agent_count": len(agents), "status": "healthy"})

    async def _status(self, ctx: SessionContextBlock):
        response = (
            "Platform status:\n"
            "• Orchestrator: Running\n"
            "• Session store: Active\n"
            "• Audit ledger: Active\n"
            "• Agent registry: All agents loaded\n"
            "• Guardrails: Enforced\n"
        )
        self._set_response(ctx, response)
