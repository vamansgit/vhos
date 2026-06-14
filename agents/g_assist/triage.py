"""Agent 16: Triage Agent — MTS v2 / POPS / OETP protocols. Advisory only."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent

EMERGENCY_RED_FLAGS = [
    "chest pain with radiation", "can't breathe", "shortness of breath at rest",
    "fainting", "fainted", "stroke", "slurred speech", "one-sided weakness",
    "sudden vision loss", "sudden severe headache", "uncontrolled bleeding",
    "unconscious", "not breathing", "suicidal ideation", "want to die", "kill myself",
    "anaphylaxis", "throat swelling", "can't swallow", "heart attack",
]

MENTAL_HEALTH_KEYWORDS = [
    "hopeless", "don't want to go on", "harming myself", "ending it",
    "no point", "better off dead", "self-harm", "hurting myself",
]

OBSTETRIC_KEYWORDS = ["pregnant", "pregnancy", "contractions", "bleeding in pregnancy", "baby not moving", "labour"]

MTS_CATEGORIES = {
    1: "Immediate (Red) — life-threatening, needs emergency response now",
    2: "Very Urgent (Orange) — serious condition, seen within 10 minutes",
    3: "Urgent (Yellow) — needs prompt medical attention, within 60 minutes",
    4: "Standard (Green) — less urgent, GP same-day",
    5: "Non-urgent (Blue) — can wait, self-care with 24h follow-up",
}


class TriageAgent(VhosAgent):
    agent_id = "triage"
    pillar = "g_assist"
    domain = "expertise"
    registered_intents = [
        "Analyze_Symptoms", "Determine_Severity", "Route_Specialist",
        "Mental_Health_Triage", "Obstetric_Triage",
    ]
    required_auth_level = AuthLevel.MEDIUM
    fallback_safe = False
    streaming_voice_compatible = True
    mdsw_scope = "Pending CDSCO SaMD — advisory only"
    KPI_TARGET = 0.82
    ESC_MAX = 0.15
    RED_FLAGS = EMERGENCY_RED_FLAGS
    OPENING_STATEMENT = (
        "I'm here to help assess your symptoms and make sure you get to the right care. "
        "Please describe what you're experiencing. "
        "[I'm an AI assistant — this is for guidance only, not a medical diagnosis.]"
    )

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message()
        lower = msg.lower()

        # Red flag — immediate escalation <800ms
        for flag in EMERGENCY_RED_FLAGS:
            if flag in lower:
                self._escalate(ctx, reason=f"Emergency red flag: {flag}", target="emergency_escalation")
                ctx.response_in_progress.text = (
                    "This sounds like it could be a medical emergency. "
                    "Please call 112 (or your local emergency number) immediately. "
                    "I'm alerting the emergency team right now. Do not wait."
                )
                await self.return_control(ctx)
                return

        # Mental health triage
        for kw in MENTAL_HEALTH_KEYWORDS:
            if kw in lower:
                await self._mental_health_triage(ctx)
                await self.return_control(ctx)
                return

        # Obstetric triage
        if any(kw in lower for kw in OBSTETRIC_KEYWORDS):
            await self._obstetric_triage(ctx, msg)
            await self.return_control(ctx)
            return

        # Standard triage flow
        workspace = ctx.agent_workspace.scratch
        if not workspace.get("complaint"):
            await self._collect_complaint(ctx, msg)
        elif not workspace.get("duration"):
            workspace["complaint"] = msg
            await self._collect_duration(ctx)
        elif not workspace.get("severity"):
            workspace["duration"] = msg
            await self._collect_severity(ctx)
        elif not workspace.get("associated_symptoms"):
            workspace["severity"] = msg
            await self._collect_associated(ctx)
        elif not workspace.get("history"):
            workspace["associated_symptoms"] = msg
            await self._collect_history(ctx)
        else:
            workspace["history"] = msg
            await self._determine_severity(ctx)

        await self.return_control(ctx)

    async def _collect_complaint(self, ctx: SessionContextBlock, msg: str):
        ctx.agent_workspace.scratch["complaint"] = msg
        response = (
            "Thank you for telling me. How long have you been experiencing this? "
            "(For example: 'just started', 'a few hours', 'a few days')"
        )
        self._set_response(ctx, response)

    async def _collect_duration(self, ctx: SessionContextBlock):
        self._set_response(ctx, "On a scale of 0 to 10, how severe would you say this is? (0 = no discomfort, 10 = worst imaginable)")

    async def _collect_severity(self, ctx: SessionContextBlock):
        self._set_response(ctx, "Are there any other symptoms alongside this? For example, fever, nausea, sweating, or anything else unusual?")

    async def _collect_associated(self, ctx: SessionContextBlock):
        self._set_response(ctx, "Do you have any relevant medical history I should know about? For example, heart disease, diabetes, or current medications?")

    async def _collect_history(self, ctx: SessionContextBlock):
        self._set_response(ctx, "Thank you. One more moment while I assess this for you.")

    async def _determine_severity(self, ctx: SessionContextBlock):
        ws = ctx.agent_workspace.scratch
        complaint = ws.get("complaint", "")
        severity_str = ws.get("severity", "5")
        try:
            severity_num = int("".join(filter(str.isdigit, severity_str)) or "5")
        except Exception:
            severity_num = 5

        # MTS-based category determination
        if severity_num >= 8 or any(w in complaint.lower() for w in ["very severe", "worst", "unbearable"]):
            category = 2
        elif severity_num >= 6:
            category = 3
        elif severity_num >= 4:
            category = 4
        else:
            category = 5

        category_desc = MTS_CATEGORIES[category]

        # Routing
        if category <= 2:
            route = "Emergency department immediately"
            self._escalate(ctx, reason=f"MTS Category {category}", target="emergency_escalation")
        elif category == 3:
            route = "Urgent care / ED — please attend within 1 hour"
        elif category == 4:
            route = "GP appointment same day — I can book that for you"
        else:
            route = "Self-care at home — with 24-hour follow-up call from us"

        # MANDATORY advisory framing — never state diagnosis
        response = (
            f"Based on what you've described and standard triage guidelines, "
            f"this sounds like it would be in the {category_desc.split('—')[0].strip()} band — "
            f"meaning {category_desc.split('—')[1].strip() if '—' in category_desc else ''}. "
            f"I'd recommend: {route}. "
            "Can I help arrange that? "
            "[This is a triage assessment to help guide you — it is not a diagnosis. "
            "Please consult a doctor for a proper medical evaluation.]"
        )
        self._log_mutation(ctx, "fhir:Encounter.triage_category", category,
                           f"MTS triage: complaint={complaint[:50]}, severity={severity_num}")
        self._set_response(ctx, response, structured_data={
            "triage_category": category, "protocol": "MTS_v2",
            "complaint": complaint, "severity": severity_num
        })
        if category <= 2:
            ctx.response_in_progress.next_intent_hint = "emergency_escalation"

    async def _mental_health_triage(self, ctx: SessionContextBlock):
        # PHQ-2 screening — NEVER leave patient alone in distress
        response = (
            "I hear you, and I want you to know you're not alone. "
            "I'm connecting you right now to a mental health support specialist who can talk with you. "
            "Please stay with me — help is on the way. "
            "If you're in immediate danger, please call iCall: 9152987821 or Vandrevala Foundation: 1860-2662-345 (24/7)."
        )
        self._escalate(ctx, reason="Mental health crisis keywords detected", target="mental_health_crisis")
        ctx.response_in_progress.text = response

    async def _obstetric_triage(self, ctx: SessionContextBlock, msg: str):
        lower = msg.lower()
        # Maternal red flags → immediate emergency escalation
        if any(w in lower for w in ["bleeding", "fetal movement", "baby not moving", "contractions every", "severe headache", "vision"]):
            self._escalate(ctx, reason="Obstetric red flag", target="emergency_escalation")
            response = (
                "What you're describing needs immediate medical attention. "
                "Please go to the obstetric emergency unit immediately or call 112. "
                "I'm alerting the obstetric team now."
            )
        else:
            ws = ctx.agent_workspace.scratch
            gestational_age = ws.get("gestational_age", "unknown")
            response = (
                "I'm switching to the obstetric triage protocol. "
                "A few important questions:\n"
                "• How many weeks pregnant are you?\n"
                "• Is the baby moving normally?\n"
                "• Any vaginal bleeding or fluid leaking?\n"
                "• Are you having regular contractions?"
            )
        self._set_response(ctx, response)
