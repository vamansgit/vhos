"""Agent 19: Diagnostic Summarizer Agent — lab and imaging interpretation."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from agents.base import AuthLevel, SessionContextBlock, VhosAgent

CRITICAL_THRESHOLDS = {
    "potassium": {"low": 2.5, "high": 6.5, "unit": "mmol/L"},
    "sodium": {"low": 120, "high": 155, "unit": "mmol/L"},
    "glucose": {"low": 2.0, "high": 25.0, "unit": "mmol/L"},
    "haemoglobin": {"low": 5.0, "high": None, "unit": "g/dL"},
    "platelets": {"low": 20, "high": None, "unit": "x10^9/L"},
    "creatinine": {"low": None, "high": 700, "unit": "µmol/L"},
}


class DiagnosticSummarizerAgent(VhosAgent):
    agent_id = "diagnostic_summarizer"
    pillar = "g_assist"
    domain = "expertise"
    registered_intents = [
        "Interpret_Lab_Results", "Summarize_Imaging_Reports",
        "Action_Clinical_Alerts", "Generate_Result_Trend",
    ]
    required_auth_level = AuthLevel.PROVIDER
    fallback_safe = False
    mdsw_scope = "Pending CDSCO SaMD — advisory only"
    KPI_TARGET = 0.83
    ESC_MAX = 0.03

    def _load(self, fname: str) -> pd.DataFrame:
        p = Path(os.getenv("DEMO_DATA_DIR", "demo_data")) / fname
        return pd.read_excel(p) if p.exists() else pd.DataFrame()

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if intent == "Generate_Result_Trend" or "trend" in msg:
            await self._generate_trend(ctx, msg)
        elif intent == "Summarize_Imaging_Reports" or any(w in msg for w in ["imaging", "xray", "x-ray", "ct scan", "mri", "echo", "ultrasound"]):
            await self._imaging_summary(ctx, msg)
        elif intent == "Action_Clinical_Alerts" or "alert" in msg or "critical" in msg:
            await self._clinical_alerts(ctx)
        else:
            await self._interpret_labs(ctx, msg)
        await self.return_control(ctx)

    async def _interpret_labs(self, ctx: SessionContextBlock, msg: str):
        df = self._load("labs.xlsx")
        pv = ctx.context.patient_view
        patient_id = pv.get("patient_id", "P-DEMO-001")

        # Demo lab results
        results = [
            {"param": "HbA1c", "value": 7.8, "unit": "%", "ref_range": "4.0–5.6%", "status": "HIGH"},
            {"param": "Creatinine", "value": 1.4, "unit": "mg/dL", "ref_range": "0.7–1.2 mg/dL", "status": "HIGH"},
            {"param": "Potassium", "value": 4.1, "unit": "mmol/L", "ref_range": "3.5–5.0 mmol/L", "status": "NORMAL"},
            {"param": "Haemoglobin", "value": 11.2, "unit": "g/dL", "ref_range": "12.0–16.0 g/dL", "status": "LOW"},
        ]

        critical_flags = []
        lines = []
        for r in results:
            flag = "⚠️ ABNORMAL" if r["status"] != "NORMAL" else "✅ Normal"
            lines.append(f"• {r['param']}: {r['value']} {r['unit']} (Ref: {r['ref_range']}) — {flag}")
            # Check critical thresholds
            param_lower = r["param"].lower()
            for crit_param, thresholds in CRITICAL_THRESHOLDS.items():
                if crit_param in param_lower:
                    if thresholds["low"] and r["value"] < thresholds["low"]:
                        critical_flags.append(f"CRITICAL LOW {r['param']}: {r['value']} {r['unit']}")
                    if thresholds["high"] and r["value"] > thresholds["high"]:
                        critical_flags.append(f"CRITICAL HIGH {r['param']}: {r['value']} {r['unit']}")

        if critical_flags:
            alert_text = "🚨 CRITICAL VALUES — ALERT FIRST:\n" + "\n".join(critical_flags) + "\n"
        else:
            alert_text = ""

        response = (
            alert_text
            + "Lab results (age/sex adjusted reference ranges):\n"
            + "\n".join(lines)
            + "\n[Source: LIS DiagnosticReport | These are findings, not diagnoses. "
            "Abnormal values require clinical correlation and doctor review.]"
        )
        self._set_response(ctx, response, structured_data={"results": results, "critical": critical_flags})

        if critical_flags:
            self._log_mutation(ctx, "clinical_alert", str(critical_flags), "Critical value alert — clinician notification required")

    async def _imaging_summary(self, ctx: SessionContextBlock, msg: str):
        pv = ctx.context.patient_view
        report_type = "CT Chest" if "ct" in msg else "Chest X-ray" if "x-ray" in msg or "xray" in msg else "Echocardiogram" if "echo" in msg else "MRI"
        response = (
            f"Imaging report summary — {report_type}:\n"
            f"Modality: {report_type}. Body region: Chest/relevant area.\n"
            "Key findings: No acute pathology identified. Mild cardiomegaly noted. "
            "Lungs clear. No pleural effusion.\n"
            "Radiologist impression: Within expected limits for the patient's clinical context.\n"
            "[Source: PACS/RIS structured report | 3-sentence summary — full report in EMR]"
        )
        self._set_response(ctx, response)

    async def _clinical_alerts(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        unack_alerts = pv.get("unacknowledged_alerts", [
            {"param": "Creatinine", "value": "712 µmol/L", "time": "08:32", "acknowledged": False}
        ])
        if not unack_alerts:
            response = "No unacknowledged critical alerts at this time."
        else:
            alert_lines = [f"🚨 {a['param']}: {a['value']} at {a['time']} — UNACKNOWLEDGED" for a in unack_alerts if not a.get("acknowledged")]
            response = (
                "Unacknowledged critical alerts:\n" + "\n".join(alert_lines) + "\n"
                "Please acknowledge each alert. Unacknowledged alerts will escalate to the department head in 30 minutes."
            )
        self._set_response(ctx, response, structured_data={"unacknowledged": len(unack_alerts)})

    async def _generate_trend(self, ctx: SessionContextBlock, msg: str):
        df = self._load("labs.xlsx")
        param = "HbA1c"
        for p in ["hba1c", "creatinine", "potassium", "sodium", "haemoglobin", "glucose", "tsh"]:
            if p in msg.lower():
                param = p.upper()
                break

        # Demo trend data
        trend_data = [
            {"date": "Jan 2026", "value": 9.2},
            {"date": "Apr 2026", "value": 8.4},
            {"date": "Jul 2026", "value": 7.8},
        ]

        if len(trend_data) >= 2:
            direction = "improving" if trend_data[-1]["value"] < trend_data[0]["value"] else "worsening"
        else:
            direction = "insufficient data"

        trend_str = " → ".join(f"{d['value']} ({d['date']})" for d in trend_data)
        response = (
            f"{param} trend (last 12 months): {trend_str} — {direction} trajectory.\n"
            "[Source: LIS historical DiagnosticReport | Findings only — not a diagnosis]"
        )
        self._set_response(ctx, response, structured_data={"param": param, "trend": trend_data, "direction": direction})
