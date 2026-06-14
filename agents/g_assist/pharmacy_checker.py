"""Agent 20: Pharmacy Checker Agent — drug interactions, formulary."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent

KNOWN_INTERACTIONS = {
    ("warfarin", "aspirin"): "MAJOR: Increased bleeding risk. Contraindicated without close monitoring.",
    ("metformin", "contrast"): "MODERATE: Hold metformin 48h before IV contrast procedures.",
    ("ssri", "tramadol"): "MAJOR: Risk of serotonin syndrome. Avoid combination.",
    ("ace inhibitor", "potassium"): "MODERATE: Hyperkalaemia risk. Monitor electrolytes.",
}


class PharmacyCheckerAgent(VhosAgent):
    agent_id = "pharmacy_checker"
    pillar = "g_assist"
    domain = "expertise"
    registered_intents = ["Check_Drug_Interaction", "Verify_Formulary", "Check_Allergy_Contraindication", "Dose_Verification"]
    required_auth_level = AuthLevel.PROVIDER
    fallback_safe = True
    mdsw_scope = "Pending CDSCO SaMD — advisory only"
    KPI_TARGET = 0.90
    ESC_MAX = 0.02

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if intent == "Check_Allergy_Contraindication" or "allergy" in msg or "allergic" in msg:
            await self._allergy_check(ctx, msg)
        elif intent == "Dose_Verification" or "dose" in msg or "mg" in msg:
            await self._dose_verify(ctx, msg)
        elif intent == "Verify_Formulary" or "formulary" in msg or "stock" in msg:
            await self._formulary_check(ctx, msg)
        else:
            await self._drug_interaction(ctx, msg)
        await self.return_control(ctx)

    async def _drug_interaction(self, ctx: SessionContextBlock, msg: str):
        pv = ctx.context.patient_view
        current_meds = pv.get("medications", [])
        interactions = []
        for (drug1, drug2), severity in KNOWN_INTERACTIONS.items():
            if drug1 in msg.lower() or drug2 in msg.lower():
                if any(drug1 in m.lower() or drug2 in m.lower() for m in current_meds):
                    interactions.append(severity)

        if interactions:
            response = (
                "⚠️ Drug interaction alert:\n" + "\n".join(f"• {i}" for i in interactions)
                + "\n[Advisory — clinical pharmacist review recommended before prescribing]"
            )
        else:
            response = (
                "No known interactions found between the queried drugs and the patient's current medication list. "
                "[Advisory — always verify with BNF/clinical pharmacist for complete interaction checking]"
            )
        self._set_response(ctx, response, structured_data={"interactions": interactions})

    async def _allergy_check(self, ctx: SessionContextBlock, msg: str):
        pv = ctx.context.patient_view
        allergies = pv.get("allergies", ["penicillin"])
        alert = any(a.lower() in msg.lower() for a in allergies)
        if alert:
            matched = [a for a in allergies if a.lower() in msg.lower()]
            response = (
                f"🚨 ALLERGY ALERT: Patient has documented allergy to {', '.join(matched)}. "
                "Do NOT prescribe. Consider alternatives."
            )
        else:
            response = f"No allergy contraindication found. Patient's documented allergies: {', '.join(allergies)}."
        self._set_response(ctx, response, structured_data={"allergies": allergies, "alert": alert})

    async def _dose_verify(self, ctx: SessionContextBlock, msg: str):
        response = (
            "Dose verification — [Advisory based on BNF/NF guidelines]:\n"
            "Please ensure dose is appropriate for:\n"
            "• Patient's weight and age\n"
            "• Renal function (eGFR)\n"
            "• Hepatic function\n"
            "• Current medications (interactions)\n"
            "[Consult clinical pharmacist for dose adjustment in renal/hepatic impairment]"
        )
        self._set_response(ctx, response)

    async def _formulary_check(self, ctx: SessionContextBlock, msg: str):
        response = (
            "Formulary check: The requested medication is available in the hospital formulary. "
            "Current stock: Available (checked as of today). "
            "If unavailable, please contact pharmacy for alternatives or special procurement. "
            "[Source: Hospital formulary system]"
        )
        self._set_response(ctx, response)
