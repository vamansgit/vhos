"""Pytest configuration and shared fixtures."""
from __future__ import annotations

import asyncio
import os

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Set demo data dir before imports
os.environ.setdefault("DEMO_DATA_DIR", "demo_data")

from api.main import app
from agents.base import AuthLevel, AuthPrincipal, ContextView, SessionContextBlock
from vhos_platform.orchestrator.master import MasterOrchestrator


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def orchestrator():
    return MasterOrchestrator(use_llm_intent=False)


@pytest.fixture
def demo_ctx():
    """A demo SessionContextBlock for testing agents."""
    return SessionContextBlock(
        session_id="test-session-001",
        tenant_id="test-tenant",
        capability_token="test-token",
        principal=AuthPrincipal(
            principal_id="test-patient",
            auth_level=AuthLevel.MEDIUM,
        ),
        goal="greeting",
        context=ContextView(
            patient_view={
                "patient_id": "UHID-1001",
                "name": "Mr. Test Patient",
                "age": 55,
                "gender": "Male",
                "primary_condition": "Hypertension, Type 2 Diabetes",
                "treating_doctor": "Dr. Priya Mehta",
                "medications": ["metformin 500mg", "amlodipine 5mg"],
                "allergies": ["penicillin"],
                "conditions": ["hypertension", "type 2 diabetes"],
            },
            hospital_view={
                "name": "VHOS Test Hospital",
                "tenant_id": "test-tenant",
            }
        ),
    )


@pytest.fixture
def provider_ctx(demo_ctx):
    """Context with provider auth level."""
    demo_ctx.principal.auth_level = AuthLevel.PROVIDER
    return demo_ctx


@pytest.fixture
def high_auth_ctx(demo_ctx):
    """Context with high auth level."""
    demo_ctx.principal.auth_level = AuthLevel.HIGH
    return demo_ctx
