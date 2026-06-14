"""VHOS FastAPI Application — REST + WebSocket."""
from __future__ import annotations

import json
import time
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from vhos_platform.orchestrator.master import MasterOrchestrator

app = FastAPI(
    title="VHOS v2.4 — Virtual Hospital Operating System",
    description="Graviton Systems | 43 AI Agents | Production API",
    version="2.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_orchestrator: Optional[MasterOrchestrator] = None


def get_orchestrator() -> MasterOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MasterOrchestrator(use_llm_intent=False)
    return _orchestrator


# ─── Pydantic models ────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    tenant_id: str = "default"
    auth_level: str = "none"
    principal_id: str = "anonymous"
    patient_view: dict = {}
    hospital_view: dict = {}


class SendMessageRequest(BaseModel):
    message: str
    auth_level: Optional[str] = None


class ConfirmRequest(BaseModel):
    confirmed: bool
    confirmation_data: dict = {}


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "VHOS v2.4",
        "timestamp": time.time(),
        "agents_loaded": len(get_orchestrator().list_agents()),
    }


@app.get("/agents")
async def list_agents():
    return {
        "total": len(get_orchestrator().list_agents()),
        "agents": get_orchestrator().list_agents(),
    }


@app.post("/session")
async def create_session(req: CreateSessionRequest):
    orch = get_orchestrator()
    session = orch.create_session(
        tenant_id=req.tenant_id,
        auth_level=req.auth_level,
        principal_id=req.principal_id,
        patient_view=req.patient_view,
        hospital_view=req.hospital_view,
    )
    # Auto-send greeting
    greeting = await orch.process_message(session["session_id"], "hello")
    session["greeting"] = greeting.get("text", "")
    return session


@app.post("/session/{session_id}/message")
async def send_message(session_id: str, req: SendMessageRequest):
    orch = get_orchestrator()
    result = await orch.process_message(session_id, req.message, req.auth_level)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/session/{session_id}/status")
async def session_status(session_id: str):
    orch = get_orchestrator()
    status = orch.get_session_status(session_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    return status


@app.get("/session/{session_id}/audit")
async def session_audit(session_id: str):
    orch = get_orchestrator()
    log = orch.get_audit_log(session_id)
    return {"session_id": session_id, "entries": log, "count": len(log)}


@app.delete("/session/{session_id}")
async def end_session(session_id: str):
    orch = get_orchestrator()
    orch.session_store.delete(session_id)
    return {"session_id": session_id, "status": "ended"}


# ─── WebSocket (voice/chat stream) ───────────────────────────────────────────

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    orch = get_orchestrator()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                message = data.get("message", "")
                auth_level = data.get("auth_level")
            except json.JSONDecodeError:
                message = raw
                auth_level = None

            if not message:
                continue

            result = await orch.process_message(session_id, message, auth_level)
            await websocket.send_json(result)
    except WebSocketDisconnect:
        orch.session_store.delete(session_id)
    except Exception as e:
        try:
            await websocket.send_json({"error": str(e), "outcome": "error"})
        except Exception:
            pass


# ─── Demo / convenience endpoints ─────────────────────────────────────────────

@app.post("/demo/chat")
async def demo_chat(body: dict):
    """Quick demo endpoint: creates session and sends one message."""
    orch = get_orchestrator()
    patient_view = body.get("patient_view", {})
    session = orch.create_session(
        tenant_id=body.get("tenant_id", "demo"),
        auth_level=body.get("auth_level", "medium"),
        principal_id=body.get("principal_id", "demo-user"),
        patient_view=patient_view,
    )
    message = body.get("message", "hello")
    result = await orch.process_message(session["session_id"], message)
    return {
        "session_id": session["session_id"],
        "message": message,
        "response": result,
    }
