"""Guardrails catalogue — master rules applied to all agents."""
from __future__ import annotations

from agents.base import GuardrailInstruction

MASTER_GUARDRAILS = [
    GuardrailInstruction(
        guardrail_id="G-001",
        rule="Never provide a diagnosis. Use advisory framing: 'based on what you've described...'",
        action="enforce",
    ),
    GuardrailInstruction(
        guardrail_id="G-002",
        rule="Never fabricate clinical data, timings, or availability. If data unavailable, say so.",
        action="enforce",
    ),
    GuardrailInstruction(
        guardrail_id="G-003",
        rule="AI disclosure in opening statement per EU AI Act §52 / TPG 2020.",
        action="enforce",
    ),
    GuardrailInstruction(
        guardrail_id="G-004",
        rule="Emergency red flags: escalate within 800ms. No exception.",
        action="enforce",
    ),
    GuardrailInstruction(
        guardrail_id="G-005",
        rule="Mental health crisis: never dismiss, never leave patient alone. Warm handoff only.",
        action="enforce",
    ),
    GuardrailInstruction(
        guardrail_id="G-006",
        rule="Out-of-scope clinical questions: offer human handback after max 3 turns.",
        action="enforce",
    ),
    GuardrailInstruction(
        guardrail_id="G-007",
        rule="Patient data: only share with authorised parties. Apply DPDP/GDPR data minimisation.",
        action="enforce",
    ),
    GuardrailInstruction(
        guardrail_id="G-008",
        rule="Opt-out requests: process immediately and permanently. No retry.",
        action="enforce",
    ),
    GuardrailInstruction(
        guardrail_id="G-009",
        rule="Medical records: never read aloud over voice channel.",
        action="enforce",
    ),
    GuardrailInstruction(
        guardrail_id="G-010",
        rule="Clinical notes and orders: always DRAFT until clinician confirms. Never auto-commit.",
        action="enforce",
    ),
]


class GuardrailsCatalogue:
    def get_all(self) -> list[GuardrailInstruction]:
        return MASTER_GUARDRAILS

    def get_for_agent(self, agent_id: str) -> list[GuardrailInstruction]:
        """Returns guardrails applicable to the given agent."""
        return [g for g in MASTER_GUARDRAILS if not g.applies_to_agents or agent_id in g.applies_to_agents]

    def check_response(self, text: str, agent_id: str) -> list[str]:
        """Returns list of potential guardrail violations found in response text."""
        violations = []
        diagnosis_patterns = [
            "you have ", "you are suffering from", "this is a diagnosis of",
            "you are diagnosed with", "the diagnosis is "
        ]
        for pattern in diagnosis_patterns:
            if pattern in text.lower():
                violations.append(f"G-001: Possible diagnosis statement detected: '{pattern}'")
        return violations
