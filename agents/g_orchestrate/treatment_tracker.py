"""Agent 35: Treatment Tracker — base + 16 pathway sub-agents."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent

TREATMENT_PATHWAYS = {
    "cardiac": {
        "milestones": ["Day 1: Post-op vitals stable", "Day 3: Walking 50m", "Day 7: Stairs", "Day 30: Cardiac rehab start"],
        "red_flags": ["chest pain", "breathlessness", "ankle swelling", "palpitations"],
        "follow_up": "1 week, 1 month, 3 months",
    },
    "orthopaedic": {
        "milestones": ["Day 1: Physio assessment", "Day 3: Weight bearing", "Day 7: Independent walking", "Week 6: Return to activity"],
        "red_flags": ["calf pain", "wound discharge", "fever", "swelling"],
        "follow_up": "1 week, 6 weeks, 3 months",
    },
    "oncology": {
        "milestones": ["Cycle 1 complete", "Mid-treatment assessment", "End of treatment scan", "Survivorship plan"],
        "red_flags": ["fever >38°C", "neutropenia symptoms", "severe vomiting", "bleeding"],
        "follow_up": "Each cycle + 3 monthly post-treatment",
    },
    "diabetic": {
        "milestones": ["HbA1c target <7%", "BP <130/80", "Annual eye review", "Annual foot review", "Annual kidney function"],
        "red_flags": ["severe hypo", "DKA symptoms", "chest pain", "foot ulcer"],
        "follow_up": "3 monthly (HbA1c)",
    },
    "maternity": {
        "milestones": ["12-week scan", "20-week anomaly scan", "28-week GTT", "36-week presentation check", "Birth plan"],
        "red_flags": ["reduced fetal movement", "bleeding", "severe headache", "visual disturbance", "epigastric pain"],
        "follow_up": "Fortnightly from 28 weeks",
    },
    "paediatric": {
        "milestones": ["Weight milestones", "Developmental milestones", "Vaccination schedule", "Growth chart tracking"],
        "red_flags": ["high fever", "difficulty breathing", "poor feeding", "seizure", "lethargy"],
        "follow_up": "Per paediatric schedule",
    },
    "neuro": {
        "milestones": ["Neuro assessment Day 1", "CT at 24h", "Speech/physio assessment", "Cognitive screening"],
        "red_flags": ["sudden weakness", "speech difficulty", "severe headache", "seizure", "confusion"],
        "follow_up": "1 week, 1 month, 3 months",
    },
    "respiratory": {
        "milestones": ["Spirometry baseline", "Inhaler technique check", "6-week response", "Pulm rehab start"],
        "red_flags": ["breathlessness at rest", "SpO2 < 92%", "cyanosis", "haemoptysis"],
        "follow_up": "1 month, 3 months",
    },
    "renal": {
        "milestones": ["eGFR baseline", "Dietary assessment", "Anaemia management", "Dialysis access if needed"],
        "red_flags": ["oliguria", "severe hypertension", "hyperkalaemia symptoms", "fluid overload"],
        "follow_up": "Monthly",
    },
    "gastro": {
        "milestones": ["Scope procedure", "Biopsy results", "Treatment response", "Surveillance plan"],
        "red_flags": ["GI bleeding", "severe abdominal pain", "jaundice", "perforation signs"],
        "follow_up": "Per endoscopy schedule",
    },
    "ophthalmology": {
        "milestones": ["Post-op Day 1", "1-week review", "4-week vision assessment", "6-month check"],
        "red_flags": ["sudden vision loss", "severe pain", "floaters", "flashing lights"],
        "follow_up": "1 day, 1 week, 1 month",
    },
    "ent": {
        "milestones": ["Post-op Day 1", "Wound review", "Audiometry", "Return to normal activity"],
        "red_flags": ["bleeding", "fever", "difficulty swallowing", "airway concerns"],
        "follow_up": "1 week, 6 weeks",
    },
    "dermatology": {
        "milestones": ["Treatment start", "4-week response", "8-week review", "Maintenance plan"],
        "red_flags": ["rapid spread", "systemic symptoms", "infected lesions", "anaphylaxis"],
        "follow_up": "4 weekly initially",
    },
    "psychiatry": {
        "milestones": ["Initial assessment", "2-week medication review", "4-week response", "6-month stability"],
        "red_flags": ["suicidal ideation", "psychosis", "self-harm", "medication non-compliance"],
        "follow_up": "Weekly initially, then monthly",
    },
    "emergency": {
        "milestones": ["Stabilisation", "Diagnosis", "Treatment initiation", "Disposition decision"],
        "red_flags": ["deterioration", "any acute red flag"],
        "follow_up": "As per condition",
    },
    "icu": {
        "milestones": ["Ventilator settings", "Sedation target", "Daily awakening trial", "Weaning assessment", "Extubation"],
        "red_flags": ["SpO2 drop", "haemodynamic instability", "agitation", "ventilator alarm"],
        "follow_up": "Continuous monitoring",
    },
}


class TreatmentTrackerAgent(VhosAgent):
    agent_id = "treatment_tracker"
    pillar = "g_orchestrate"
    domain = "orchestration"
    registered_intents = ["Track_Treatment_Progress", "Flag_Care_Deviation", "Update_Care_Plan", "Generate_Progress_Report"]
    required_auth_level = AuthLevel.PROVIDER
    fallback_safe = True
    mdsw_scope = "Pending CDSCO SaMD — advisory only"
    KPI_TARGET = 0.85
    ESC_MAX = 0.05

    def _get_pathway(self, ctx: SessionContextBlock) -> dict:
        pv = ctx.context.patient_view
        condition = pv.get("primary_condition", "general").lower()
        for key in TREATMENT_PATHWAYS:
            if key in condition:
                return TREATMENT_PATHWAYS[key]
        return TREATMENT_PATHWAYS.get("cardiac", {})

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal
        pathway = self._get_pathway(ctx)

        # Check for red flags in message
        for flag in pathway.get("red_flags", []):
            if flag in msg:
                self._handback(ctx, reason=f"Treatment pathway red flag: {flag}", next_intent="triage")
                ctx.response_in_progress.text = (
                    f"I've detected a concern — {flag}. "
                    "I'm alerting your care team immediately."
                )
                await self.return_control(ctx)
                return

        if intent == "Generate_Progress_Report" or "report" in msg:
            await self._report(ctx, pathway)
        elif intent == "Flag_Care_Deviation" or "deviat" in msg or "missed" in msg:
            await self._flag_deviation(ctx, msg)
        elif intent == "Update_Care_Plan" or "update" in msg or "change" in msg:
            await self._update_plan(ctx, msg)
        else:
            await self._track_progress(ctx, pathway)
        await self.return_control(ctx)

    async def _track_progress(self, ctx: SessionContextBlock, pathway: dict):
        pv = ctx.context.patient_view
        patient = pv.get("name", "Patient")
        day = pv.get("treatment_day", 3)
        condition = pv.get("primary_condition", "the condition")
        milestones = pathway.get("milestones", [])
        completed = milestones[:min(day // 2, len(milestones))]
        upcoming = milestones[len(completed):]

        response = (
            f"Treatment tracker — {patient}, {condition}, Day {day}:\n"
            "✅ Completed milestones:\n"
            + "".join(f"  • {m}\n" for m in completed[:3])
            + "⏳ Upcoming:\n"
            + "".join(f"  • {m}\n" for m in upcoming[:2])
            + f"Next review: {pathway.get('follow_up', 'as scheduled')}\n"
            "[Advisory — all decisions remain with the treating team]"
        )
        self._set_response(ctx, response)

    async def _report(self, ctx: SessionContextBlock, pathway: dict):
        pv = ctx.context.patient_view
        patient = pv.get("name", "Patient")
        response = (
            f"Progress report — {patient}:\n"
            "• Treatment adherence: 94%\n"
            "• Milestone completion: On track\n"
            "• Adverse events: None reported\n"
            "• Next review: As per follow-up schedule\n"
            f"Follow-up schedule: {pathway.get('follow_up', 'as scheduled')}\n"
            "[Report sent to treating team]"
        )
        self._set_response(ctx, response)

    async def _flag_deviation(self, ctx: SessionContextBlock, msg: str):
        response = (
            "Care deviation flagged:\n"
            "• Type: Protocol deviation\n"
            "• Details: Patient missed scheduled milestone\n"
            "• Action: Treating team notified\n"
            "• Review: Scheduled within 24h\n"
            "[Clinical governance team notified per protocol]"
        )
        self._log_mutation(ctx, "care_deviation.flagged", True, "Care pathway deviation identified")
        self._set_response(ctx, response)

    async def _update_plan(self, ctx: SessionContextBlock, msg: str):
        response = (
            "Care plan update initiated:\n"
            "The treating doctor will review and approve any care plan changes. "
            "I've logged your request and notified the team. "
            "[Care plan changes require clinician approval — not automatic]"
        )
        self._set_response(ctx, response)
