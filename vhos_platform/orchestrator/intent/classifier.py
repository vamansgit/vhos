"""Intent classifier — keyword-based with optional Claude Haiku."""
from __future__ import annotations

import re
from typing import Optional

INTENT_MAP = {
    # Emergency — highest priority
    r"(chest pain|heart attack|can't breathe|stroke|unconscious|bleeding severely|suicide|kill myself|anaphylaxis|seizure)": "emergency",
    # Appointments
    r"(book|schedule|appointment|slot|reserve)": "Book_Appointment",
    r"(reschedule|move.*appointment|change.*appointment)": "Reschedule_Appointment",
    r"(cancel.*appointment|cancel.*booking)": "Cancel_Appointment",
    r"(upcoming.*appointment|my appointment|view appointment)": "View_Upcoming_Appointments",
    r"(available|availability|free slot|open slot)": "Check_Availability",
    # Insurance
    r"(insurance|coverage|tpa|claim|co.?pay|policy)": "Verify_Coverage",
    # Information
    r"(doctor|specialist|physician|surgeon)": "Find_Doctor",
    r"(timing|hours|open|close|when.*open)": "Check_Timings",
    r"(where|direction|navigate|floor|wing)": "Navigate_Facility",
    r"(department|service|facility|hospital info)": "Query_Hospital_Info",
    # Care
    r"(medication|medicine|tablet|pill|dose|drug)": "Log_Medication_Intake",
    r"(symptom|pain|sick|fever|hurt|unwell)": "Analyze_Symptoms",
    r"(record|discharge summary|report|history)": "Request_Medical_Record",
    # Queue
    r"(queue|token|wait|my turn|position)": "Check_Queue_Status",
    # Mental health
    r"(hopeless|depressed|anxious|mental|sad|lonely|worthless)": "PHQ9_Screening",
    # Clinical provider
    r"(nursing summary|ward round|ward summary|sbar|handover|falls risk|news2)": "Generate_Nursing_Summary",
    r"(summarize patient|clinical summary|soap note|clinical order|prescribe|ward briefing|patient record)": "Summarize_Patient_Record",
    r"(lab result|diagnostic|hba1c|creatinine|lab trend|imaging report)": "Interpret_Lab_Results",
    # Greeting
    r"(hello|hi|hey|good morning|good afternoon|start|help)": "greeting",
}


class IntentClassifier:
    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
                from config import settings
                if settings.anthropic_api_key:
                    self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            except Exception:
                pass
        return self._client

    def classify_keyword(self, text: str) -> tuple[str, float]:
        """Fast keyword-based classification. Returns (intent, confidence)."""
        text_lower = text.lower()
        for pattern, intent in INTENT_MAP.items():
            if re.search(pattern, text_lower):
                return intent, 0.85
        return "general_query", 0.40

    async def classify(self, text: str, session_context: dict = None) -> tuple[str, float]:
        """Returns (intent, confidence). Falls back to keyword if LLM unavailable."""
        keyword_intent, keyword_conf = self.classify_keyword(text)

        # Emergency always takes precedence
        if keyword_intent == "emergency":
            return "emergency", 1.0

        if not self.use_llm or keyword_conf >= 0.85:
            return keyword_intent, keyword_conf

        # Try LLM classification (Claude Haiku)
        client = self._get_client()
        if client is None:
            return keyword_intent, keyword_conf

        try:
            from config import settings
            resp = await client.messages.create(
                model=settings.intent_model,
                max_tokens=50,
                system=(
                    "You are an intent classifier for a hospital AI system. "
                    "Classify the user message into ONE of these intents: "
                    "emergency, Book_Appointment, Reschedule_Appointment, Cancel_Appointment, "
                    "View_Upcoming_Appointments, Check_Availability, Verify_Coverage, "
                    "Find_Doctor, Check_Timings, Navigate_Facility, Query_Hospital_Info, "
                    "Log_Medication_Intake, Analyze_Symptoms, Request_Medical_Record, "
                    "Check_Queue_Status, PHQ9_Screening, greeting, general_query. "
                    "Reply with ONLY the intent name and a confidence 0.0-1.0 separated by comma."
                ),
                messages=[{"role": "user", "content": text}],
            )
            result = resp.content[0].text.strip()
            parts = result.split(",")
            intent = parts[0].strip()
            conf = float(parts[1].strip()) if len(parts) > 1 else 0.75
            return intent, conf
        except Exception:
            return keyword_intent, keyword_conf

    def route_to_agent(self, intent: str) -> str:
        """Map intent to agent_id."""
        routing = {
            "emergency": "emergency_escalation",
            "Book_Appointment": "scheduling",
            "Reschedule_Appointment": "scheduling",
            "Cancel_Appointment": "scheduling",
            "View_Upcoming_Appointments": "scheduling",
            "Check_Availability": "scheduling",
            "Verify_Coverage": "insurance_tpa",
            "Check_Claim_Status": "insurance_tpa",
            "Estimate_Procedure_Cost": "insurance_tpa",
            "Find_Doctor": "access_query",
            "Check_Timings": "access_query",
            "Navigate_Facility": "access_query",
            "Query_Hospital_Info": "access_query",
            "Log_Medication_Intake": "medicine_adherence",
            "Analyze_Symptoms": "triage",
            "Request_Medical_Record": "medical_records",
            "Check_Queue_Status": "opd_queue",
            "PHQ9_Screening": "mental_health",
            "Generate_Nursing_Summary": "nurse_copilot",
            "Summarize_Patient_Record": "doctor_copilot",
            "Interpret_Lab_Results": "diagnostic_summarizer",
            "greeting": "patient_routing",
            "general_query": "patient_routing",
        }
        return routing.get(intent, "patient_routing")
