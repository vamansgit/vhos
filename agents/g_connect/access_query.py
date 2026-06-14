"""Agent 1: Access & Query Agent — hospital info, find doctor, timings, navigation."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class AccessQueryAgent(VhosAgent):
    agent_id = "access_query"
    pillar = "g_connect"
    domain = "experience"
    registered_intents = ["Query_Hospital_Info", "Find_Doctor", "Check_Timings", "Navigate_Facility"]
    required_auth_level = AuthLevel.NONE
    fallback_safe = True
    streaming_voice_compatible = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.85
    ESC_MAX = 0.05
    OPENING_STATEMENT = (
        "Hello, I can help you with hospital information — doctors, departments, timings, or directions. "
        "What would you like to know? [AI Disclosure: I am an AI assistant, not a human staff member.]"
    )

    def _load_demo(self, sheet: str) -> pd.DataFrame:
        path = Path(os.getenv("DEMO_DATA_DIR", "demo_data")) / "hospital_master.xlsx"
        if path.exists():
            return pd.read_excel(path, sheet_name=sheet)
        return pd.DataFrame()

    async def execute(self, ctx: SessionContextBlock) -> None:
        msg = ctx.last_user_message().lower()
        intent = ctx.goal

        # First greeting / opening
        if not ctx.conversation_history or intent == "greeting":
            self._set_response(ctx, self.OPENING_STATEMENT, structured_data={"agent": self.agent_id})
            await self.return_control(ctx)
            return

        if intent == "Query_Hospital_Info" or any(w in msg for w in ["department", "service", "facility", "hospital", "what do you"]):
            await self._query_hospital_info(ctx, msg)
        elif intent == "Find_Doctor" or any(w in msg for w in ["doctor", "specialist", "physician", "dr.", "surgeon"]):
            await self._find_doctor(ctx, msg)
        elif intent == "Check_Timings" or any(w in msg for w in ["timing", "hours", "open", "close", "when"]):
            await self._check_timings(ctx, msg)
        elif intent == "Navigate_Facility" or any(w in msg for w in ["where", "how to get", "direction", "floor", "wing", "navigate"]):
            await self._navigate_facility(ctx, msg)
        else:
            self._set_response(
                ctx,
                "I can help with hospital information, finding doctors, timings, or directions. "
                "Could you be more specific about what you need?",
            )
        await self.return_control(ctx)

    async def _query_hospital_info(self, ctx: SessionContextBlock, msg: str):
        df = self._load_demo("Departments")
        if df.empty:
            departments = ["Cardiology", "Orthopaedics", "Neurology", "Oncology", "Emergency",
                           "Radiology", "Pathology", "Gynaecology", "Paediatrics", "Urology"]
            response = (
                f"We offer services across {len(departments)} departments including: "
                f"{', '.join(departments[:5])}, and more. "
                "Which specific department or service are you looking for?"
            )
        else:
            dept_names = df["department_name"].tolist() if "department_name" in df.columns else df.iloc[:, 0].tolist()
            # Simple keyword match
            matches = [d for d in dept_names if any(w in str(d).lower() for w in msg.split())]
            if matches:
                response = f"We have the following matching departments: {', '.join(matches[:3])}. Would you like more details on any of these?"
            else:
                response = (
                    f"Our hospital offers {len(dept_names)} departments including: "
                    f"{', '.join(str(d) for d in dept_names[:5])}. "
                    "What specific service are you looking for?"
                )
        self._set_response(ctx, response, structured_data={"intent": "Query_Hospital_Info"})

    async def _find_doctor(self, ctx: SessionContextBlock, msg: str):
        df = self._load_demo("Doctors")
        if df.empty:
            doctors = [
                {"name": "Dr. Priya Mehta", "specialty": "Cardiology", "available_today": True},
                {"name": "Dr. Rajesh Kumar", "specialty": "Orthopaedics", "available_today": True},
                {"name": "Dr. Sunita Sharma", "specialty": "Neurology", "available_today": False},
            ]
            response = (
                "Here are doctors available today:\n"
                "1. Dr. Priya Mehta — Cardiology (available)\n"
                "2. Dr. Rajesh Kumar — Orthopaedics (available)\n"
                "Would you like to book an appointment with any of them?"
            )
        else:
            name_col = next((c for c in df.columns if "name" in c.lower()), df.columns[0])
            spec_col = next((c for c in df.columns if "spec" in c.lower()), None)
            # Filter by keyword
            words = [w for w in msg.split() if len(w) > 3]
            mask = pd.Series([True] * len(df))
            for word in words:
                col_mask = df[name_col].str.lower().str.contains(word, na=False)
                if spec_col:
                    col_mask |= df[spec_col].str.lower().str.contains(word, na=False)
                mask &= col_mask
            results = df[mask].head(3) if mask.any() else df.head(3)
            lines = []
            for _, row in results.iterrows():
                line = f"Dr. {row[name_col]}"
                if spec_col:
                    line += f" — {row[spec_col]}"
                lines.append(line)
            response = (
                f"Here are up to 3 matching doctors:\n"
                + "\n".join(f"{i+1}. {l}" for i, l in enumerate(lines))
                + "\nWould you like to book an appointment?"
            )
        self._set_response(ctx, response, structured_data={"intent": "Find_Doctor"}, next_intent="Book_Appointment")

    async def _check_timings(self, ctx: SessionContextBlock, msg: str):
        df = self._load_demo("Timings")
        if df.empty:
            response = (
                "Our general OPD timings are Monday–Saturday, 8:00 AM to 8:00 PM. "
                "Emergency services are available 24/7. "
                "Specific department timings may vary — which department are you asking about?"
            )
        else:
            dept_col = next((c for c in df.columns if "dept" in c.lower() or "depart" in c.lower()), df.columns[0])
            time_col = next((c for c in df.columns if "time" in c.lower() or "hour" in c.lower()), None)
            words = [w for w in msg.split() if len(w) > 3]
            mask = df[dept_col].str.lower().str.contains("|".join(words), na=False) if words else pd.Series([True]*len(df))
            results = df[mask].head(3) if mask.any() else df.head(3)
            lines = []
            for _, row in results.iterrows():
                line = f"{row[dept_col]}"
                if time_col:
                    line += f": {row[time_col]}"
                lines.append(line)
            response = "Timings (as of today):\n" + "\n".join(lines) + "\n[Last updated from hospital master records]"
        self._set_response(ctx, response, structured_data={"intent": "Check_Timings"})

    async def _navigate_facility(self, ctx: SessionContextBlock, msg: str):
        df = self._load_demo("Map")
        if df.empty:
            response = (
                "From the main entrance:\n"
                "• OPD registration: Ground floor, straight ahead\n"
                "• Emergency: Ground floor, turn left at reception\n"
                "• Radiology/Lab: Basement level B1\n"
                "• ICU/Surgery: 3rd floor, use central lifts\n"
                "Please follow the colour-coded floor guide or ask a staff member for assistance."
            )
        else:
            dest_col = next((c for c in df.columns if "dest" in c.lower() or "location" in c.lower() or "place" in c.lower()), df.columns[0])
            dir_col = next((c for c in df.columns if "dir" in c.lower() or "route" in c.lower() or "instruction" in c.lower()), None)
            words = [w for w in msg.split() if len(w) > 3]
            mask = df[dest_col].str.lower().str.contains("|".join(words), na=False) if words else pd.Series([True]*len(df))
            results = df[mask].head(2) if mask.any() else df.head(2)
            lines = []
            for _, row in results.iterrows():
                line = f"• {row[dest_col]}"
                if dir_col:
                    line += f": {row[dir_col]}"
                lines.append(line)
            response = "From the main entrance:\n" + "\n".join(lines) if lines else "Please ask at the reception for directions to your destination."
        self._set_response(ctx, response, structured_data={"intent": "Navigate_Facility"})
