"""Agent 23: Diet & Nutrition Agent."""
from __future__ import annotations

from agents.base import AuthLevel, SessionContextBlock, VhosAgent


class DietNutritionAgent(VhosAgent):
    agent_id = "diet_nutrition"
    pillar = "g_assist"
    domain = "expertise"
    registered_intents = ["Create_Meal_Plan", "Check_Dietary_Restrictions", "Track_Nutritional_Goals", "Provide_Dietary_Guidance"]
    required_auth_level = AuthLevel.LOW
    fallback_safe = True
    mdsw_scope = "Not a medical device"
    KPI_TARGET = 0.75
    ESC_MAX = 0.04

    async def execute(self, ctx: SessionContextBlock) -> None:
        error = self.validate_block(ctx)
        if error:
            self._set_response(ctx, error, outcome="error")
            await self.return_control(ctx)
            return

        msg = ctx.last_user_message().lower()
        intent = ctx.goal
        pv = ctx.context.patient_view
        condition = pv.get("primary_condition", "general").lower()

        if "meal plan" in msg or intent == "Create_Meal_Plan":
            await self._meal_plan(ctx, condition)
        elif "restriction" in msg or "can i eat" in msg or "avoid" in msg or intent == "Check_Dietary_Restrictions":
            await self._restrictions(ctx, condition)
        elif "track" in msg or "goal" in msg or intent == "Track_Nutritional_Goals":
            await self._track(ctx)
        else:
            await self._guidance(ctx, condition)
        await self.return_control(ctx)

    async def _meal_plan(self, ctx: SessionContextBlock, condition: str):
        if "diabet" in condition:
            plan = (
                "Sample diabetic meal plan (aligned to your care plan):\n"
                "• Breakfast: Oats with nuts + egg white omelette\n"
                "• Mid-morning: Apple or 10 almonds\n"
                "• Lunch: Brown rice + dal + sabzi + curd\n"
                "• Evening: Green tea + handful of roasted chana\n"
                "• Dinner: Chapati (2) + vegetable curry + salad\n"
                "[Tailored to your care plan — your dietitian's specific guidance takes precedence]"
            )
        elif "cardiac" in condition:
            plan = (
                "Heart-healthy meal plan:\n"
                "• Low sodium (< 2g/day)\n"
                "• Low saturated fat\n"
                "• High fibre\n"
                "Focus on: Fish, nuts, olive oil, fruits, vegetables, whole grains\n"
                "Avoid: Processed food, fried items, excess red meat\n"
                "[Per your cardiac care plan — always follow your doctor's specific guidance]"
            )
        else:
            plan = (
                "Balanced meal plan (general wellness):\n"
                "• 5 portions of fruit and vegetables daily\n"
                "• Whole grains over refined carbohydrates\n"
                "• Lean protein sources\n"
                "• Adequate hydration (6–8 glasses water)\n"
                "[General guidance — consult your dietitian for personalised plan]"
            )
        self._set_response(ctx, plan)

    async def _restrictions(self, ctx: SessionContextBlock, condition: str):
        pv = ctx.context.patient_view
        allergies = pv.get("food_allergies", [])
        allergy_note = f"Documented food allergies: {', '.join(allergies)}. " if allergies else ""
        if "renal" in condition or "kidney" in condition:
            response = (
                f"{allergy_note}Renal diet restrictions: "
                "Limit potassium-rich foods (bananas, potatoes, tomatoes). "
                "Limit phosphorus (dairy, nuts, cola). "
                "Restrict fluid intake as per your nephrologist's instruction. "
                "[Always follow your nephrologist's specific dietary prescription]"
            )
        elif "diabet" in condition:
            response = (
                f"{allergy_note}Diabetic dietary cautions: "
                "Avoid: sugary drinks, white rice in excess, maida products, fried foods. "
                "Choose: low glycaemic index foods, spread carbs evenly through the day. "
                "[Per your diabetic care plan]"
            )
        else:
            response = f"{allergy_note}Please follow your care plan dietary guidelines. Consult your dietitian for specific restrictions."
        self._set_response(ctx, response)

    async def _track(self, ctx: SessionContextBlock):
        pv = ctx.context.patient_view
        weight = pv.get("current_weight_kg", None)
        target = pv.get("target_weight_kg", None)
        response = (
            f"Nutritional tracking: "
            + (f"Current weight: {weight} kg. Target: {target} kg. " if weight else "")
            + "Please log your meals in the patient app for accurate tracking. "
            "I'll review your nutritional goals at your next check-in."
        )
        self._set_response(ctx, response)

    async def _guidance(self, ctx: SessionContextBlock, condition: str):
        response = (
            "Key nutritional principles for your care:\n"
            "• Eat regular meals — don't skip\n"
            "• Choose whole foods over processed\n"
            "• Stay hydrated\n"
            "• Limit salt, sugar, and saturated fats\n"
            "[This is general guidance. Your dietitian's personalised advice takes priority.]"
        )
        self._set_response(ctx, response)
