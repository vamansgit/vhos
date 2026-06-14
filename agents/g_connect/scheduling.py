"""Agent 2: Scheduling Agent — book, reschedule, cancel, modify appointments."""
from __future__ import annotations

import os
import random
import string
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

from agents.base import AuthLevel, DataWriteDeclaration, SessionContextBlock, VhosAgent


class SchedulingAgent(VhosAgent):
    agent_id = "scheduling"
    pillar = "g_connect"
    domain = "experience"
    registered_intents = [
        "Book_Appointment", "Reschedule_Appointment", "Cancel_Appointment",
        "Modify_Appointment", "Check_Availability", "View_Upcoming_Appointments",
    ]
    required_auth_level = AuthLevel.MEDIUM
    fallback_safe = True
    streaming_voice_compatible = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.90
    ESC_MAX = 0.05
    data_writes = [
        DataWriteDeclaration(
            target="fhir:Appointment", operation="create",
            idempotency_key_fields=["patient_id", "slot_id"],
            compensating_action=DataWriteDeclaration(
                target="fhir:Appointment", operation="cancel",
                reason_template="Saga rollback: step {step} failed"
            ),
        ),
        DataWriteDeclaration(target="sms:confirmation", operation="send"),
    ]
    OPENING_STATEMENT = "I can help you book, reschedule, or cancel appointments. What would you like to do?"

    def _demo_path(self, name: str) -> Path:
        return Path(os.getenv("DEMO_DATA_DIR", "demo_data")) / name

    def _load_appointments(self) -> pd.DataFrame:
        p = self._demo_path("appointments.xlsx")
        return pd.read_excel(p) if p.exists() else pd.DataFrame()

    def _load_availability(self) -> pd.DataFrame:
        p = self._demo_path("doctor_availability.xlsx")
        return pd.read_excel(p) if p.exists() else pd.DataFrame()

    def _load_patients(self) -> pd.DataFrame:
        p = self._demo_path("patients.xlsx")
        return pd.read_excel(p) if p.exists() else pd.DataFrame()

    def _generate_ref(self) -> str:
        return "APT-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        if intent == "Book_Appointment" or any(w in msg for w in ["book", "schedule", "appointment", "slot"]):
            await self._book_appointment(ctx, msg)
        elif intent == "Reschedule_Appointment" or "reschedule" in msg:
            await self._reschedule_appointment(ctx, msg)
        elif intent == "Cancel_Appointment" or "cancel" in msg:
            await self._cancel_appointment(ctx, msg)
        elif intent == "Modify_Appointment" or "modify" in msg or "change time" in msg:
            await self._modify_appointment(ctx, msg)
        elif intent == "Check_Availability" or "available" in msg or "availability" in msg:
            await self._check_availability(ctx, msg)
        elif intent == "View_Upcoming_Appointments" or "upcoming" in msg or "my appointment" in msg:
            await self._view_upcoming(ctx, msg)
        else:
            self._set_response(ctx, self.OPENING_STATEMENT)
        await self.return_control(ctx)

    async def _book_appointment(self, ctx: SessionContextBlock, msg: str):
        df = self._load_availability()
        now = datetime.now()
        slots = []
        if df.empty:
            # Demo slots
            for i in range(3):
                slot_time = now + timedelta(days=i + 1, hours=10 + i)
                slots.append({
                    "slot_id": f"SLT-{i+1:04d}",
                    "doctor": f"Dr. {'Priya Mehta' if i == 0 else 'Rajesh Kumar' if i == 1 else 'Anita Singh'}",
                    "datetime": slot_time.strftime("%A, %d %b %Y at %I:%M %p"),
                    "dept": ["Cardiology", "Orthopaedics", "General"][i],
                })
        else:
            avail_col = next((c for c in df.columns if "avail" in c.lower() or "slot" in c.lower()), None)
            doc_col = next((c for c in df.columns if "doctor" in c.lower() or "name" in c.lower()), df.columns[0])
            for _, row in df.head(3).iterrows():
                slots.append({
                    "slot_id": f"SLT-{random.randint(1000,9999)}",
                    "doctor": str(row[doc_col]),
                    "datetime": str(row[avail_col]) if avail_col else (now + timedelta(days=1)).strftime("%A, %d %b"),
                    "dept": str(row.get("department", "General")),
                })

        slot_text = "\n".join(
            f"{i+1}. {s['doctor']} ({s['dept']}) — {s['datetime']}"
            for i, s in enumerate(slots)
        )
        ref = self._generate_ref()

        response = (
            f"Here are the next available slots:\n{slot_text}\n\n"
            f"Which slot would you prefer? (Reply 1, 2, or 3)\n"
            f"I'll confirm the date and time before booking."
        )
        ctx.agent_workspace.scratch["pending_slots"] = slots
        ctx.agent_workspace.scratch["pending_ref"] = ref
        ctx.response_in_progress.requires_confirmation = True
        ctx.response_in_progress.confirmation_prompt = "Please confirm your slot selection."
        self._set_response(ctx, response, structured_data={"slots": slots, "ref": ref})
        self._log_mutation(ctx, "agent_workspace.pending_slots", slots, "Presented slots to patient for booking")

    async def _reschedule_appointment(self, ctx: SessionContextBlock, msg: str):
        df = self._load_appointments()
        patient_id = ctx.context.patient_view.get("patient_id", "P-DEMO-001")

        if df.empty:
            current = {"ref": "APT-DEMO-001", "doctor": "Dr. Priya Mehta", "datetime": "Monday 16 Jun at 10:00 AM"}
        else:
            pid_col = next((c for c in df.columns if "patient" in c.lower()), None)
            rows = df[df[pid_col] == patient_id] if pid_col else df
            row = rows.iloc[0] if not rows.empty else df.iloc[0]
            current = {"ref": str(row.get("appointment_id", "APT-DEMO")),
                       "doctor": str(row.get("doctor", "Dr. Demo")),
                       "datetime": str(row.get("datetime", "TBD"))}

        new_slots = [
            {"slot_id": "SLT-NEW-1", "datetime": (datetime.now() + timedelta(days=2)).strftime("%A, %d %b at 10:00 AM")},
            {"slot_id": "SLT-NEW-2", "datetime": (datetime.now() + timedelta(days=3)).strftime("%A, %d %b at 2:00 PM")},
        ]
        slot_text = "\n".join(f"{i+1}. {s['datetime']}" for i, s in enumerate(new_slots))
        response = (
            f"Your current appointment is: {current['datetime']} with {current['doctor']} (Ref: {current['ref']}).\n"
            f"Here are alternative slots:\n{slot_text}\n"
            "Which would you prefer? I'll cancel the old slot and confirm the new one."
        )
        self._set_response(ctx, response, structured_data={"current": current, "new_slots": new_slots})

    async def _cancel_appointment(self, ctx: SessionContextBlock, msg: str):
        response = (
            "To confirm: you'd like to cancel your appointment. "
            "Could you share the appointment reference number or date? "
            "Also, could you tell me the reason? (no-show / health issue / personal / other) — this helps us improve. "
            "Once confirmed, I'll send you a cancellation confirmation via SMS."
        )
        ctx.response_in_progress.requires_confirmation = True
        ctx.response_in_progress.confirmation_prompt = "Please confirm the appointment reference to cancel."
        self._set_response(ctx, response, structured_data={"intent": "Cancel_Appointment"})

    async def _modify_appointment(self, ctx: SessionContextBlock, msg: str):
        response = (
            "I can change the time of your appointment while keeping the same doctor. "
            "Please provide your appointment reference number and your preferred new time."
        )
        self._set_response(ctx, response)

    async def _check_availability(self, ctx: SessionContextBlock, msg: str):
        df = self._load_availability()
        now = datetime.now()
        if df.empty:
            slots = [
                f"• Tomorrow {(now + timedelta(days=1)).strftime('%d %b')} at 9:00 AM — Dr. Mehta",
                f"• {(now + timedelta(days=2)).strftime('%a %d %b')} at 11:30 AM — Dr. Kumar",
                f"• {(now + timedelta(days=3)).strftime('%a %d %b')} at 3:00 PM — Dr. Singh",
            ]
        else:
            doc_col = next((c for c in df.columns if "doctor" in c.lower() or "name" in c.lower()), df.columns[0])
            time_col = next((c for c in df.columns if "time" in c.lower() or "slot" in c.lower()), None)
            slots = []
            for _, row in df.head(3).iterrows():
                s = f"• {row[doc_col]}"
                if time_col:
                    s += f" — {row[time_col]}"
                slots.append(s)
        response = "Next available slots:\n" + "\n".join(slots) + "\nWould you like to book one?"
        self._set_response(ctx, response, next_intent="Book_Appointment")

    async def _view_upcoming(self, ctx: SessionContextBlock, msg: str):
        df = self._load_appointments()
        patient_id = ctx.context.patient_view.get("patient_id", "P-DEMO-001")
        if df.empty:
            response = (
                "Your upcoming appointments:\n"
                "1. Monday 16 Jun at 10:00 AM — Dr. Priya Mehta (Cardiology) — Ref: APT-001\n"
                "2. Wednesday 18 Jun at 2:30 PM — Dr. Rajesh Kumar (Orthopaedics) — Ref: APT-002\n"
                "Would you like to modify or cancel any of these?"
            )
        else:
            pid_col = next((c for c in df.columns if "patient" in c.lower()), None)
            if pid_col:
                rows = df[df[pid_col] == patient_id].head(3)
            else:
                rows = df.head(3)
            if rows.empty:
                response = "I don't see any upcoming appointments for you. Would you like to book one?"
            else:
                doc_col = next((c for c in df.columns if "doctor" in c.lower()), df.columns[0])
                dt_col = next((c for c in df.columns if "date" in c.lower() or "time" in c.lower()), None)
                lines = []
                for i, (_, row) in enumerate(rows.iterrows(), 1):
                    line = f"{i}. {row[doc_col]}"
                    if dt_col:
                        line += f" — {row[dt_col]}"
                    lines.append(line)
                response = "Your upcoming appointments:\n" + "\n".join(lines)
        self._set_response(ctx, response, structured_data={"intent": "View_Upcoming_Appointments"})
