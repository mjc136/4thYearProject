from botbuilder.dialogs import (
    ComponentDialog, DialogSet, DialogTurnStatus,
    WaterfallDialog, WaterfallStepContext, DialogTurnResult, TextPrompt
)
from botbuilder.core import TurnContext
from botbuilder.schema import ActivityTypes
from backend.bot.state.user_state import UserState
from .taxi_scenario import TaxiScenarioDialog
from .hotel_scenario import HotelScenarioDialog
from .job_interview_scenario import JobInterviewScenarioDialog
from .restaurant_scenario import RestaurantScenarioDialog
from .shopping_scenario import ShoppingScenarioDialog
from .doctor_visit_scenario import DoctorVisitScenarioDialog
from .base_dialog import BaseDialog


class MainDialog(BaseDialog):
    """
    Main entry point for user interactions.
    This dialog routes users to a scenario based on URL-passed `scenario`,
    or falls back to user proficiency level if not provided.
    """

    def __init__(self, user_state: UserState, scenario: str = None):
        dialog_id = "MainDialog"
        super(MainDialog, self).__init__(dialog_id, user_state)
        self.user_state = user_state
        self.scenario = scenario.lower() if scenario else None
        
        self.add_dialog(WaterfallDialog(f"{dialog_id}.waterfall", [
            self.select_scenario_step,
            self.continue_step
        ]))

        # Register scenario dialogs
        self.add_dialog(TaxiScenarioDialog(user_state))
        self.add_dialog(HotelScenarioDialog(user_state))
        self.add_dialog(JobInterviewScenarioDialog(user_state))
        self.add_dialog(RestaurantScenarioDialog(user_state))
        self.add_dialog(ShoppingScenarioDialog(user_state))
        self.add_dialog(DoctorVisitScenarioDialog(user_state))
        self.add_dialog(TextPrompt(TextPrompt.__name__))

        self.initial_dialog_id = f"{dialog_id}.waterfall"

    async def select_scenario_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Route to the appropriate scenario based on passed-in scenario or user proficiency."""
        dialog_id = None

        if self.scenario == "taxi":
            dialog_id = "TaxiScenarioDialog"
        elif self.scenario == "restaurant":
            dialog_id = "RestaurantScenarioDialog"
        elif self.scenario == "shopping":
            dialog_id = "ShoppingScenarioDialog"
        elif self.scenario == "hotel":
            dialog_id = "HotelScenarioDialog"
        elif self.scenario == "doctor":
            dialog_id = "DoctorVisitScenarioDialog"
        else:
            dialog_id = "JobInterviewScenarioDialog"

        if not dialog_id:
            await step_context.context.send_activity("No matching scenario available for your settings.")
            return await step_context.end_dialog()

        self.user_state.set_active_dialog(dialog_id)
        return await step_context.begin_dialog(dialog_id)

    async def continue_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Do not restart the scenario if it just ended."""
        active_dialog = self.user_state.get_active_dialog()

        # Do not re-enter the same dialog if we just completed it
        if step_context.result is not None:
            await step_context.context.send_activity("Scenario completed.")
            return await step_context.end_dialog()

        # Otherwise, re-launch the dialog (e.g., user wants to retry)
        if active_dialog:
            return await step_context.begin_dialog(active_dialog)

        return await step_context.replace_dialog(self.id)

    async def update_user_streak(self, step_context: WaterfallStepContext):
        """Update the user's streak after completing a scenario."""
        from datetime import datetime, timedelta
        
        # Get current user data
        user_profile = await self.user_state.get_user_profile(step_context.context)
        
        # Get the current date (in user's timezone if available)
        current_date = datetime.now().date()
        
        # If this is the first activity, initialize streak data
        if not hasattr(user_profile, "streak_count"):
            user_profile.streak_count = 1
            user_profile.last_activity_date = current_date
            user_profile.highest_streak = 1
            await step_context.context.send_activity("Congratulations on starting your learning streak! 🔥 Day 1!")
            return
            
        # Get the last activity date
        last_date = user_profile.last_activity_date
        
        # If it's the same day, don't update streak
        if current_date == last_date:
            return
            
        # If it's the next day, increment streak
        if current_date == last_date + timedelta(days=1):
            user_profile.streak_count += 1
            # Update highest streak if current streak is higher
            if user_profile.streak_count > user_profile.highest_streak:
                user_profile.highest_streak = user_profile.streak_count
            await step_context.context.send_activity(f"🔥 You're on a {user_profile.streak_count}-day streak! Keep it up!")
        # If more than one day has passed, reset streak
        elif current_date > last_date + timedelta(days=1):
            previous_streak = user_profile.streak_count
            user_profile.streak_count = 1
            await step_context.context.send_activity(f"Welcome back! Your previous streak was {previous_streak} days. You're now on day 1 of a new streak! 🔥")
        
        # Update the last activity date to today
        user_profile.last_activity_date = current_date

    async def run(self, turn_context: TurnContext, dialog_state):
        """Run the main dialog."""
        try:
            dialog_set = DialogSet(dialog_state)
            dialog_set.add(self)

            dialog_context = await dialog_set.create_context(turn_context)
            results = await dialog_context.continue_dialog()

            if results is None or results.status == DialogTurnStatus.Empty:
                await dialog_context.begin_dialog(self.id)

            return True
        except Exception as e:
            print(f"Error in MainDialog.run: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
