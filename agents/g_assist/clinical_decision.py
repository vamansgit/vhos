"""Agent 21: Clinical Decision Support Agent — evidence-based suggestions."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class ClinicalDecisionAgent(VhosAgent):
    agent_id = "clinical_decision"
    pillar = "g_assist"
    domain = "expertise"
    registered_intents = ["Suggest_Diagnostic_Workup", "Recommend_Treatment_Pathway", "Check_Clinical_Guidelines", "Differential_Diagnosis_Support"]
    required_auth_level = AuthLevel.PROVIDER
    fallback_safe = False
    mdsw_scope = "Pending CDSCO SaMD — advisory only"
    KPI_TARGET = 0.82
    ESC_MAX = 0.04

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if "differential" in msg or "ddx" in msg or intent == "Differential_Diagnosis_Support":
            await self._differential(ctx, msg)
        elif "guideline" in msg or "protocol" in msg or intent == "Check_Clinical_Guidelines":
            await self._guidelines(ctx, msg)
        elif "treatment" in msg or "pathway" in msg or intent == "Recommend_Treatment_Pathway":
            await self._pathway(ctx, msg)
        else:
            await self._diagnostic_workup(ctx, msg)
        await self.return_control(ctx)

    async def _diagnostic_workup(self, ctx: SessionContextBlock, msg: str):
        response = (
            "Suggested diagnostic workup [Evidence-based, advisory only]:\n"
            "• Complete blood count (CBC)\n"
            "• Metabolic panel (electrolytes, renal, liver function)\n"
            "• Relevant imaging as per clinical presentation\n"
            "• ECG if cardiovascular symptoms\n"
            "[Source: Current clinical guidelines | All suggestions require doctor review before ordering]"
        )
        self._set_response(ctx, response)

    async def _differential(self, ctx: SessionContextBlock, msg: str):
        response = (
            "Differential diagnosis support [Advisory — not a diagnosis]:\n"
            "Based on the clinical features described, consider:\n"
            "1. Most likely (common): [requires full clinical assessment]\n"
            "2. Important to exclude: [serious conditions per guidelines]\n"
            "3. Less likely but consider: [contextual differentials]\n"
            "[These are prompts to support clinical reasoning — final diagnosis is the doctor's responsibility]"
        )
        self._set_response(ctx, response)

    async def _guidelines(self, ctx: SessionContextBlock, msg: str):
        condition = "diabetes" if "diabet" in msg else "hypertension" if "hyper" in msg else "cardiac" if "cardio" in msg or "heart" in msg else "the condition"
        response = (
            f"Current guidelines for {condition} [Advisory]:\n"
            "Please refer to the relevant clinical guideline (NICE/WHO/Indian Council of Medical Research). "
            "Key principles: individualise treatment targets, consider comorbidities, follow stepped care. "
            "[Source: Referenced guideline database | Always verify against latest published guidance]"
        )
        self._set_response(ctx, response)

    async def _pathway(self, ctx: SessionContextBlock, msg: str):
        response = (
            "Treatment pathway recommendation [Evidence-based, advisory]:\n"
            "Step 1: Lifestyle modification (first-line)\n"
            "Step 2: Monotherapy (as per guideline)\n"
            "Step 3: Combination therapy if targets not met\n"
            "Step 4: Specialist referral\n"
            "[Pathway based on current guidelines — individualise per patient context]"
        )
        self._set_response(ctx, response)
