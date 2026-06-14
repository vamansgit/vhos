"""Tests for all VHOS agents."""
from __future__ import annotations

import pytest

from agents.base import AuthLevel, SessionContextBlock


# ─── Registry ────────────────────────────────────────────────────────────────

def test_registry_loads_all_agents():
    from agents.registry import list_agents
    agents = list_agents()
    assert len(agents) >= 43, f"Expected 43 agents, got {len(agents)}"


def test_registry_get_agent():
    from agents.registry import get
    agent = get("triage")
    assert agent is not None
    assert agent.agent_id == "triage"


def test_registry_all_expected_agents():
    from agents.registry import get
    expected = [
        "access_query", "scheduling", "insurance_tpa", "patient_routing",
        "opd_queue", "proactive_outreach", "competitor_counter", "medical_records",
        "medicine_adherence", "preventive_wellness", "lifestyle_coach", "family_comms",
        "post_discharge", "preopprep", "population_campaign",
        "triage", "nurse_copilot", "doctor_copilot", "diagnostic_summarizer",
        "pharmacy_checker", "clinical_decision", "consent_manager",
        "diet_nutrition", "pain_assessment", "mental_health", "rehabilitation",
        "resource_coordination", "workflow_automation", "billing_coordinator",
        "discharge_planner", "referral_manager", "bed_management", "ot_scheduler",
        "supply_chain", "treatment_tracker",
        "risk_detection", "quality_monitor", "yield_agent", "outcome_tracker",
        "cost_analytics", "operational_insights",
        "emergency_escalation",
    ]
    for agent_id in expected:
        assert get(agent_id) is not None, f"Agent '{agent_id}' not found in registry"


# ─── Agent Base ──────────────────────────────────────────────────────────────

def test_auth_level_validation(demo_ctx):
    from agents.g_connect.scheduling import SchedulingAgent
    agent = SchedulingAgent()
    assert agent.required_auth_level == AuthLevel.MEDIUM
    demo_ctx.principal.auth_level = AuthLevel.LOW
    assert not agent._validate_auth(demo_ctx)
    demo_ctx.principal.auth_level = AuthLevel.MEDIUM
    assert agent._validate_auth(demo_ctx)
    demo_ctx.principal.auth_level = AuthLevel.HIGH
    assert agent._validate_auth(demo_ctx)


# ─── G-CONNECT ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_access_query_hospital_info(demo_ctx):
    from agents.g_connect.access_query import AccessQueryAgent
    agent = AccessQueryAgent()
    demo_ctx.goal = "Query_Hospital_Info"
    demo_ctx.add_turn("user", "what departments do you have")
    await agent.execute(demo_ctx)
    assert demo_ctx.response_in_progress.text
    assert len(demo_ctx.response_in_progress.text) > 10


@pytest.mark.asyncio
async def test_access_query_find_doctor(demo_ctx):
    from agents.g_connect.access_query import AccessQueryAgent
    agent = AccessQueryAgent()
    demo_ctx.goal = "Find_Doctor"
    demo_ctx.add_turn("user", "I need a cardiologist doctor")
    await agent.execute(demo_ctx)
    assert demo_ctx.response_in_progress.text


@pytest.mark.asyncio
async def test_scheduling_auth_required(demo_ctx):
    from agents.g_connect.scheduling import SchedulingAgent
    agent = SchedulingAgent()
    demo_ctx.principal.auth_level = AuthLevel.NONE
    demo_ctx.add_turn("user", "book an appointment")
    await agent.execute(demo_ctx)
    assert demo_ctx.response_in_progress.outcome == "error"
    assert "authentication" in demo_ctx.response_in_progress.text.lower() or "verify" in demo_ctx.response_in_progress.text.lower()


@pytest.mark.asyncio
async def test_scheduling_book_appointment(demo_ctx):
    from agents.g_connect.scheduling import SchedulingAgent
    agent = SchedulingAgent()
    demo_ctx.goal = "Book_Appointment"
    demo_ctx.add_turn("user", "I want to book an appointment")
    await agent.execute(demo_ctx)
    assert demo_ctx.response_in_progress.text
    assert "slot" in demo_ctx.response_in_progress.text.lower() or "appointment" in demo_ctx.response_in_progress.text.lower()


@pytest.mark.asyncio
async def test_patient_routing_emergency(demo_ctx):
    from agents.g_connect.patient_routing import PatientRoutingAgent
    agent = PatientRoutingAgent()
    demo_ctx.principal.auth_level = AuthLevel.NONE
    demo_ctx.add_turn("user", "I have chest pain and can't breathe")
    await agent.execute(demo_ctx)
    assert demo_ctx.response_in_progress.outcome == "escalate"
    assert demo_ctx.response_in_progress.escalation_target == "emergency_escalation"


@pytest.mark.asyncio
async def test_patient_routing_appointment(demo_ctx):
    from agents.g_connect.patient_routing import PatientRoutingAgent
    agent = PatientRoutingAgent()
    demo_ctx.principal.auth_level = AuthLevel.NONE
    demo_ctx.add_turn("user", "I want to book an appointment")
    await agent.execute(demo_ctx)
    assert demo_ctx.response_in_progress.outcome in ("handback", "success")


# ─── G-CARE ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_medicine_adherence_taken(demo_ctx):
    from agents.g_care.medicine_adherence import MedicineAdherenceAgent
    agent = MedicineAdherenceAgent()
    demo_ctx.goal = "Log_Medication_Intake"
    demo_ctx.add_turn("user", "yes I have taken my medication")
    await agent.execute(demo_ctx)
    assert "logged" in demo_ctx.response_in_progress.text.lower() or "taken" in demo_ctx.response_in_progress.text.lower()


@pytest.mark.asyncio
async def test_medicine_adherence_adverse_effect(demo_ctx):
    from agents.g_care.medicine_adherence import MedicineAdherenceAgent
    agent = MedicineAdherenceAgent()
    demo_ctx.add_turn("user", "I have a rash and allergic reaction")
    await agent.execute(demo_ctx)
    assert demo_ctx.response_in_progress.outcome == "handback"
    assert demo_ctx.response_in_progress.next_intent_hint == "triage"


@pytest.mark.asyncio
async def test_family_comms_unauthorised(demo_ctx):
    from agents.g_care.family_comms import FamilyCommsAgent
    agent = FamilyCommsAgent()
    demo_ctx.context.patient_view["authorised_contacts"] = ["OTHER-001", "OTHER-002"]
    demo_ctx.principal.principal_id = "NOT-AUTHORISED"
    demo_ctx.add_turn("user", "how is my family member")
    await agent.execute(demo_ctx)
    assert demo_ctx.response_in_progress.outcome == "error"


@pytest.mark.asyncio
async def test_post_discharge_red_flag(demo_ctx):
    from agents.g_care.post_discharge import PostDischargeAgent
    agent = PostDischargeAgent()
    demo_ctx.context.patient_view["procedure"] = "cardiac"
    demo_ctx.add_turn("user", "I have chest pain since this morning")
    await agent.execute(demo_ctx)
    assert demo_ctx.response_in_progress.outcome == "handback"
    assert demo_ctx.response_in_progress.next_intent_hint == "triage"


# ─── G-ASSIST ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_triage_emergency_escalation(demo_ctx):
    from agents.g_assist.triage import TriageAgent
    agent = TriageAgent()
    demo_ctx.add_turn("user", "I have chest pain with radiation to my arm")
    await agent.execute(demo_ctx)
    assert demo_ctx.response_in_progress.outcome == "escalate"
    assert demo_ctx.response_in_progress.escalation_target == "emergency_escalation"


@pytest.mark.asyncio
async def test_triage_mental_health_crisis(demo_ctx):
    from agents.g_assist.triage import TriageAgent
    agent = TriageAgent()
    demo_ctx.add_turn("user", "I feel hopeless and don't want to go on")
    await agent.execute(demo_ctx)
    assert demo_ctx.response_in_progress.outcome == "escalate"


@pytest.mark.asyncio
async def test_triage_advisory_framing(demo_ctx):
    from agents.g_assist.triage import TriageAgent
    agent = TriageAgent()
    demo_ctx.goal = "Analyze_Symptoms"
    # Simulate multiple turns through triage flow
    demo_ctx.agent_workspace.scratch = {
        "complaint": "headache for 2 days",
        "duration": "2 days",
        "severity": "4",
        "associated_symptoms": "none",
        "history": "no significant history",
    }
    demo_ctx.add_turn("user", "no significant history")
    await agent.execute(demo_ctx)
    text = demo_ctx.response_in_progress.text.lower()
    # Must use advisory framing, never state diagnosis
    assert "based on what you've described" in text or "advisory" in text or "not a diagnosis" in text


@pytest.mark.asyncio
async def test_nurse_copilot_provider_only(demo_ctx):
    from agents.g_assist.nurse_copilot import NurseCopilotAgent
    agent = NurseCopilotAgent()
    demo_ctx.principal.auth_level = AuthLevel.MEDIUM
    demo_ctx.add_turn("user", "give me nursing summary")
    await agent.execute(demo_ctx)
    assert demo_ctx.response_in_progress.outcome == "error"


@pytest.mark.asyncio
async def test_nurse_copilot_summary_is_draft(provider_ctx):
    from agents.g_assist.nurse_copilot import NurseCopilotAgent
    agent = NurseCopilotAgent()
    provider_ctx.goal = "Generate_Nursing_Summary"
    provider_ctx.add_turn("user", "generate nursing summary for patient")
    await agent.execute(provider_ctx)
    assert provider_ctx.response_in_progress.requires_confirmation


@pytest.mark.asyncio
async def test_doctor_copilot_order_is_draft(provider_ctx):
    from agents.g_assist.doctor_copilot import DoctorCopilotAgent
    agent = DoctorCopilotAgent()
    provider_ctx.goal = "Draft_Clinical_Order"
    provider_ctx.agent_workspace.scratch["drug"] = "metformin"
    provider_ctx.agent_workspace.scratch["dose"] = "500mg"
    provider_ctx.agent_workspace.scratch["frequency"] = "twice daily"
    provider_ctx.agent_workspace.scratch["duration"] = "30 days"
    provider_ctx.add_turn("user", "prescribe metformin 500mg twice daily")
    await agent.execute(provider_ctx)
    assert provider_ctx.response_in_progress.requires_confirmation
    assert "DRAFT" in provider_ctx.response_in_progress.text


@pytest.mark.asyncio
async def test_mental_health_crisis_never_leaves_alone(demo_ctx):
    from agents.g_assist.mental_health import MentalHealthAgent
    agent = MentalHealthAgent()
    demo_ctx.add_turn("user", "I want to kill myself")
    await agent.execute(demo_ctx)
    text = demo_ctx.response_in_progress.text
    assert demo_ctx.response_in_progress.outcome == "escalate"
    # Must not leave patient alone — must provide crisis resources
    assert any(phrase in text for phrase in ["stay with", "not alone", "iCall", "crisis", "connecting"])


# ─── G-ORCHESTRATE ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_treatment_tracker_red_flag_escalation(provider_ctx):
    from agents.g_orchestrate.treatment_tracker import TreatmentTrackerAgent
    agent = TreatmentTrackerAgent()
    provider_ctx.context.patient_view["primary_condition"] = "cardiac"
    provider_ctx.add_turn("user", "patient reports chest pain since morning")
    await agent.execute(provider_ctx)
    assert provider_ctx.response_in_progress.outcome == "handback"


@pytest.mark.asyncio
async def test_bed_management_status(provider_ctx):
    from agents.g_orchestrate.bed_management import BedManagementAgent
    agent = BedManagementAgent()
    provider_ctx.add_turn("user", "show me bed status")
    await agent.execute(provider_ctx)
    assert "occupancy" in provider_ctx.response_in_progress.text.lower() or "bed" in provider_ctx.response_in_progress.text.lower()


# ─── G-INSIGHTS ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_risk_detection_stratification(provider_ctx):
    from agents.g_insights.risk_detection import RiskDetectionAgent
    agent = RiskDetectionAgent()
    provider_ctx.add_turn("user", "stratify risk for this patient")
    await agent.execute(provider_ctx)
    text = provider_ctx.response_in_progress.text.lower()
    assert "risk" in text


# ─── PLATFORM CONTROL ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_emergency_escalation_response_structure(demo_ctx):
    from agents.platform_control.emergency_escalation import EmergencyEscalationAgent
    agent = EmergencyEscalationAgent()
    demo_ctx.response_in_progress.escalation_reason = "chest pain with radiation"
    demo_ctx.add_turn("user", "I have chest pain with radiation to my left arm")
    await agent.execute(demo_ctx)
    text = demo_ctx.response_in_progress.text
    assert "112" in text or "emergency" in text.lower()
    assert demo_ctx.response_in_progress.outcome == "escalate"
    assert demo_ctx.response_in_progress.structured_data.get("emergency_team_notified") is True


# ─── ORCHESTRATOR ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_orchestrator_session_lifecycle(orchestrator):
    session = orchestrator.create_session(tenant_id="test", auth_level="medium")
    assert "session_id" in session
    sid = session["session_id"]

    result = await orchestrator.process_message(sid, "hello")
    assert "text" in result
    assert result["text"]

    status = orchestrator.get_session_status(sid)
    assert status["lifecycle_state"] in ("active", "returned")


@pytest.mark.asyncio
async def test_orchestrator_emergency_routing(orchestrator):
    session = orchestrator.create_session(tenant_id="test")
    sid = session["session_id"]
    result = await orchestrator.process_message(sid, "I have chest pain and can't breathe")
    assert result.get("agent_id") == "emergency_escalation" or result.get("escalation_target") == "emergency_escalation"


# ─── API ENDPOINTS ───────────────────────────────────────────────────────────

def test_health_endpoint(test_client):
    resp = test_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["agents_loaded"] >= 43


def test_list_agents_endpoint(test_client):
    resp = test_client.get("/agents")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 43


def test_create_session_endpoint(test_client):
    resp = test_client.post("/session", json={
        "tenant_id": "test",
        "auth_level": "medium",
        "principal_id": "test-user",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert "greeting" in data


def test_send_message_endpoint(test_client):
    session_resp = test_client.post("/session", json={"tenant_id": "test"})
    sid = session_resp.json()["session_id"]
    resp = test_client.post(f"/session/{sid}/message", json={"message": "I need to book an appointment"})
    assert resp.status_code == 200
    data = resp.json()
    assert "text" in data
    assert data["text"]


def test_session_not_found(test_client):
    resp = test_client.post("/session/nonexistent-id/message", json={"message": "hello"})
    assert resp.status_code == 404


def test_demo_chat_endpoint(test_client):
    resp = test_client.post("/demo/chat", json={
        "message": "what are your timings",
        "auth_level": "none",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert data["response"]["text"]


def test_audit_endpoint(test_client):
    session_resp = test_client.post("/session", json={"tenant_id": "test"})
    sid = session_resp.json()["session_id"]
    test_client.post(f"/session/{sid}/message", json={"message": "hello"})
    resp = test_client.get(f"/session/{sid}/audit")
    assert resp.status_code == 200
    data = resp.json()
    assert "entries" in data
    assert data["count"] > 0
