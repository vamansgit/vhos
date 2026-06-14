"""VHOS Agent Registry — all 43 agents registered."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.base import VhosAgent

_REGISTRY: dict[str, "VhosAgent"] = {}


def register(agent: "VhosAgent") -> None:
    _REGISTRY[agent.agent_id] = agent


def get(agent_id: str) -> "VhosAgent | None":
    return _REGISTRY.get(agent_id)


def list_agents() -> list[dict]:
    return [
        {
            "agent_id": a.agent_id,
            "pillar": a.pillar,
            "domain": a.domain,
            "registered_intents": a.registered_intents,
            "auth_level": a.required_auth_level.value,
            "mdsw_scope": a.mdsw_scope,
            "fallback_safe": a.fallback_safe,
            "kpi_target": a.KPI_TARGET,
        }
        for a in _REGISTRY.values()
    ]


def _load_all() -> None:
    """Import and register all agents."""
    from agents.g_connect.access_query import AccessQueryAgent
    from agents.g_connect.scheduling import SchedulingAgent
    from agents.g_connect.insurance_tpa import InsuranceTpaAgent
    from agents.g_connect.patient_routing import PatientRoutingAgent
    from agents.g_connect.opd_queue import OpdQueueAgent
    from agents.g_connect.proactive_outreach import ProactiveOutreachAgent
    from agents.g_connect.competitor_counter import CompetitorCounterAgent
    from agents.g_connect.medical_records import MedicalRecordsAgent

    from agents.g_care.medicine_adherence import MedicineAdherenceAgent
    from agents.g_care.preventive_wellness import PreventiveWellnessAgent
    from agents.g_care.lifestyle_coach import LifestyleCoachAgent
    from agents.g_care.family_comms import FamilyCommsAgent
    from agents.g_care.post_discharge import PostDischargeAgent
    from agents.g_care.preopprep import PreOpPrepAgent
    from agents.g_care.population_campaign import PopulationCampaignAgent

    from agents.g_assist.triage import TriageAgent
    from agents.g_assist.nurse_copilot import NurseCopilotAgent
    from agents.g_assist.doctor_copilot import DoctorCopilotAgent
    from agents.g_assist.diagnostic_summarizer import DiagnosticSummarizerAgent
    from agents.g_assist.pharmacy_checker import PharmacyCheckerAgent
    from agents.g_assist.clinical_decision import ClinicalDecisionAgent
    from agents.g_assist.consent_manager import ConsentManagerAgent
    from agents.g_assist.diet_nutrition import DietNutritionAgent
    from agents.g_assist.pain_assessment import PainAssessmentAgent
    from agents.g_assist.mental_health import MentalHealthAgent
    from agents.g_assist.rehabilitation import RehabilitationAgent

    from agents.g_orchestrate.resource_coordination import ResourceCoordinationAgent
    from agents.g_orchestrate.workflow_automation import WorkflowAutomationAgent
    from agents.g_orchestrate.billing_coordinator import BillingCoordinatorAgent
    from agents.g_orchestrate.discharge_planner import DischargePlannerAgent
    from agents.g_orchestrate.referral_manager import ReferralManagerAgent
    from agents.g_orchestrate.bed_management import BedManagementAgent
    from agents.g_orchestrate.ot_scheduler import OtSchedulerAgent
    from agents.g_orchestrate.supply_chain import SupplyChainAgent
    from agents.g_orchestrate.treatment_tracker import TreatmentTrackerAgent

    from agents.g_insights.risk_detection import RiskDetectionAgent
    from agents.g_insights.quality_monitor import QualityMonitorAgent
    from agents.g_insights.yield_agent import YieldAgent
    from agents.g_insights.outcome_tracker import OutcomeTrackerAgent
    from agents.g_insights.cost_analytics import CostAnalyticsAgent
    from agents.g_insights.operational_insights import OperationalInsightsAgent

    from agents.platform_control.emergency_escalation import EmergencyEscalationAgent
    from agents.platform_control.master_orchestrator_agent import MasterOrchestratorAgent

    all_agents = [
        # G-CONNECT
        AccessQueryAgent(), SchedulingAgent(), InsuranceTpaAgent(), PatientRoutingAgent(),
        OpdQueueAgent(), ProactiveOutreachAgent(), CompetitorCounterAgent(), MedicalRecordsAgent(),
        # G-CARE
        MedicineAdherenceAgent(), PreventiveWellnessAgent(), LifestyleCoachAgent(),
        FamilyCommsAgent(), PostDischargeAgent(), PreOpPrepAgent(), PopulationCampaignAgent(),
        # G-ASSIST
        TriageAgent(), NurseCopilotAgent(), DoctorCopilotAgent(), DiagnosticSummarizerAgent(),
        PharmacyCheckerAgent(), ClinicalDecisionAgent(), ConsentManagerAgent(),
        DietNutritionAgent(), PainAssessmentAgent(), MentalHealthAgent(), RehabilitationAgent(),
        # G-ORCHESTRATE
        ResourceCoordinationAgent(), WorkflowAutomationAgent(), BillingCoordinatorAgent(),
        DischargePlannerAgent(), ReferralManagerAgent(), BedManagementAgent(),
        OtSchedulerAgent(), SupplyChainAgent(), TreatmentTrackerAgent(),
        # G-INSIGHTS
        RiskDetectionAgent(), QualityMonitorAgent(), YieldAgent(),
        OutcomeTrackerAgent(), CostAnalyticsAgent(), OperationalInsightsAgent(),
        # PLATFORM
        EmergencyEscalationAgent(),
        MasterOrchestratorAgent(),
    ]
    for agent in all_agents:
        register(agent)


# Auto-load all agents on import
_load_all()
