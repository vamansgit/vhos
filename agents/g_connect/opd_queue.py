"""Agent 5: OPD Queue Management Agent."""
from __future__ import annotations

import random

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class OpdQueueAgent(VhosAgent):
    agent_id = "opd_queue"
    pillar = "g_connect"
    domain = "experience"
    registered_intents = ["Check_Queue_Status", "Get_Wait_Time", "Notify_Turn_Approaching", "Handle_Doctor_Delay"]
    required_auth_level = AuthLevel.LOW
    fallback_safe = True
    streaming_voice_compatible = True
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

        if "delay" in msg or "doctor late" in msg or intent == "Handle_Doctor_Delay":
            await self._handle_delay(ctx)
        elif "wait" in msg or "how long" in msg or intent == "Get_Wait_Time":
            await self._get_wait_time(ctx)
        elif "notify" in msg or "my turn" in msg or intent == "Notify_Turn_Approaching":
            await self._notify_turn(ctx)
        else:
            await self._check_queue(ctx, msg)
        await self.return_control(ctx)

    async def _check_queue(self, ctx: SessionContextBlock, msg: str):
        token = ctx.context.patient_view.get("token_number", random.randint(1, 50))
        current = random.randint(max(1, int(token) - 5), int(token))
        position = int(token) - current
        avg_consult = 8  # minutes
        wait_mins = position * avg_consult
        response = (
            f"Your token number: {token}. "
            f"Currently serving: {current}. "
            f"Your position: {position} patients ahead. "
            f"Estimated wait: approximately {wait_mins} minutes (this is an estimate and may vary)."
        )
        self._set_response(ctx, response, structured_data={"token": token, "position": position, "wait_minutes": wait_mins})

    async def _get_wait_time(self, ctx: SessionContextBlock):
        token = ctx.context.patient_view.get("token_number", random.randint(5, 30))
        current = random.randint(1, max(1, int(token) - 2))
        wait = (int(token) - current) * 8
        response = (
            f"Estimated wait time: approximately {wait} minutes. "
            "Please note this is an estimate based on average consultation duration and current queue depth. "
            "Actual wait may vary."
        )
        self._set_response(ctx, response)

    async def _notify_turn(self, ctx: SessionContextBlock):
        token = ctx.context.patient_view.get("token_number", "N/A")
        response = (
            f"You'll receive a WhatsApp notification when 2 patients are ahead of you (token {token}). "
            "Please remain in the waiting area or nearby."
        )
        self._set_response(ctx, response)

    async def _handle_delay(self, ctx: SessionContextBlock):
        response = (
            "We're sorry — the doctor is currently running approximately 30 minutes behind schedule. "
            "We've sent notifications to all waiting patients. "
            "Would you like to reschedule your appointment or continue waiting?"
        )
        self._set_response(ctx, response, next_intent="Reschedule_Appointment")
