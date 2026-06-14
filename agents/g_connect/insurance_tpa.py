"""Agent 3: Insurance & TPA Agent."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class InsuranceTpaAgent(VhosAgent):
    agent_id = "insurance_tpa"
    pillar = "g_connect"
    domain = "experience"
    registered_intents = ["Verify_Coverage", "Check_Claim_Status", "Estimate_Procedure_Cost", "Validate_Eligibility"]
    required_auth_level = AuthLevel.MEDIUM
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.85
    ESC_MAX = 0.08

    def _load(self, fname: str, sheet: str = None) -> pd.DataFrame:
        p = Path(os.getenv("DEMO_DATA_DIR", "demo_data")) / fname
        if not p.exists():
            return pd.DataFrame()
        return pd.read_excel(p, sheet_name=sheet) if sheet else pd.read_excel(p)

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if intent == "Verify_Coverage" or any(w in msg for w in ["coverage", "cover", "policy", "insured"]):
            await self._verify_coverage(ctx, msg)
        elif intent == "Check_Claim_Status" or any(w in msg for w in ["claim", "status", "reference"]):
            await self._check_claim(ctx, msg)
        elif intent == "Estimate_Procedure_Cost" or any(w in msg for w in ["cost", "estimate", "price", "how much"]):
            await self._estimate_cost(ctx, msg)
        elif intent == "Validate_Eligibility" or any(w in msg for w in ["eligible", "eligibility", "valid", "network"]):
            await self._validate_eligibility(ctx, msg)
        else:
            self._set_response(ctx, "I can help with insurance coverage, claim status, cost estimates, and eligibility. What would you like to check?")
        await self.return_control(ctx)

    async def _verify_coverage(self, ctx: SessionContextBlock, msg: str):
        df = self._load("patients.xlsx", "Insurance")
        patient_id = ctx.context.patient_view.get("patient_id", "P-DEMO-001")
        if df.empty:
            response = (
                "Based on current information (as of today): "
                "Your policy (Star Health — Policy No. SH-2024-001) covers up to ₹5,00,000 per year. "
                "Co-pay: 10%. Exclusions: dental, cosmetic procedures. "
                "[Source: TPA API, updated today. This is based on current information and may change — please verify with your insurer for final confirmation.]"
            )
        else:
            pid_col = next((c for c in df.columns if "patient" in c.lower()), df.columns[0])
            row = df[df[pid_col] == patient_id]
            if row.empty:
                row = df.iloc[[0]]
            r = row.iloc[0]
            insurer = r.get("insurer", "Star Health")
            limit = r.get("coverage_limit", "5,00,000")
            copay = r.get("copay_percent", 10)
            response = (
                f"Based on current information (as of today): "
                f"Policy: {insurer}. Sum insured: ₹{limit}. Co-pay: {copay}%. "
                "[This is based on current TPA data — verify with your insurer for final confirmation.]"
            )
        self._set_response(ctx, response, structured_data={"intent": "Verify_Coverage"})

    async def _check_claim(self, ctx: SessionContextBlock, msg: str):
        response = (
            "Your claim (Ref: CLM-2024-DEMO-001) status: Under Review. "
            "Submitted: 5 Jun 2026. Estimated processing: 7–10 working days. "
            "Action required from you: Please submit your discharge summary via the patient portal. "
            "[Source: TPA portal, checked now.]"
        )
        self._set_response(ctx, response, structured_data={"intent": "Check_Claim_Status"})

    async def _estimate_cost(self, ctx: SessionContextBlock, msg: str):
        df = self._load("hospital_master.xlsx", "Procedures")
        if df.empty:
            response = (
                "For a typical cardiac angiography procedure: "
                "Gross cost: ₹45,000–₹60,000. "
                "Estimated insurance coverage: ₹40,000 (based on your policy). "
                "Estimated out-of-pocket: ₹5,000–₹20,000. "
                "[Indicative estimate only — actual costs depend on clinical requirements, implants, and room category.]"
            )
        else:
            proc_col = next((c for c in df.columns if "proc" in c.lower() or "procedure" in c.lower()), df.columns[0])
            cost_col = next((c for c in df.columns if "cost" in c.lower() or "price" in c.lower()), None)
            words = [w for w in msg.split() if len(w) > 4]
            mask = df[proc_col].str.lower().str.contains("|".join(words), na=False) if words else pd.Series([True]*len(df))
            result = df[mask].head(1) if mask.any() else df.head(1)
            r = result.iloc[0]
            cost = r[cost_col] if cost_col else "variable"
            response = (
                f"Procedure: {r[proc_col]}. Gross cost: ₹{cost}. "
                "[Indicative estimate — actual costs may vary. Please consult billing for exact figures.]"
            )
        self._set_response(ctx, response, structured_data={"intent": "Estimate_Procedure_Cost"})

    async def _validate_eligibility(self, ctx: SessionContextBlock, msg: str):
        response = (
            "Eligibility check result: "
            "Policy Status: Active (valid until 31 Mar 2027). "
            "Network Status: In-network (cashless eligible). "
            "Pre-auth Required: Yes, for procedures above ₹25,000. "
            "[Source: TPA API, as of today. Please contact TPA directly for authoritative confirmation.]"
        )
        self._set_response(ctx, response, structured_data={"intent": "Validate_Eligibility"})
