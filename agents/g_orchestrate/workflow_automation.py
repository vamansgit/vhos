"""Agent 28: Workflow Automation Agent."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class WorkflowAutomationAgent(VhosAgent):
    agent_id = "workflow_automation"
    pillar = "g_orchestrate"
    domain = "orchestration"
    registered_intents = ["Trigger_Clinical_Workflow", "Monitor_Workflow_Status", "Escalate_Bottleneck", "Auto_Route_Task"]
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

        if "bottleneck" in msg or "delay" in msg or "stuck" in msg or intent == "Escalate_Bottleneck":
            await self._escalate_bottleneck(ctx)
        elif "status" in msg or "monitor" in msg or intent == "Monitor_Workflow_Status":
            await self._status(ctx)
        elif "route" in msg or "assign" in msg or intent == "Auto_Route_Task":
            await self._route_task(ctx, msg)
        else:
            await self._trigger_workflow(ctx, msg)
        await self.return_control(ctx)

    async def _trigger_workflow(self, ctx: SessionContextBlock, msg: str):
        response = (
            "Clinical workflow triggered:\n"
            "• Admission workflow: Initiated\n"
            "• Tasks created: Nursing assessment, vitals, medication reconciliation\n"
            "• Notifications sent to: Ward nurse, Admitting doctor, Pharmacy\n"
            "All tasks tracked in workflow dashboard."
        )
        self._log_mutation(ctx, "workflow.triggered", True, "Admission workflow initiated")
        self._set_response(ctx, response, outcome="success")

    async def _status(self, ctx: SessionContextBlock):
        response = (
            "Active workflow status:\n"
            "✅ Admission: Complete\n"
            "⏳ Nursing assessment: In progress (Nurse Deepa)\n"
            "⏳ Doctor review: Pending (scheduled 14:00)\n"
            "❌ Pharmacy order: Delayed — pharmacist queried a drug interaction\n"
            "SLA: 2 tasks approaching deadline"
        )
        self._set_response(ctx, response)

    async def _escalate_bottleneck(self, ctx: SessionContextBlock):
        response = (
            "Bottleneck identified and escalated:\n"
            "• Issue: Pharmacy order delayed >2 hours\n"
            "• Escalated to: Chief Pharmacist (auto-notified)\n"
            "• SLA breach logged\n"
            "Resolution target: 30 minutes"
        )
        self._log_mutation(ctx, "workflow.escalation", "pharmacy_delay", "Bottleneck escalated to chief pharmacist")
        self._set_response(ctx, response)

    async def _route_task(self, ctx: SessionContextBlock, msg: str):
        response = (
            "Task routed automatically:\n"
            "• Task: Clinical documentation review\n"
            "• Assigned to: Available junior doctor (Dr. Singh)\n"
            "• Due: Within 2 hours\n"
            "• Notification sent"
        )
        self._set_response(ctx, response)
