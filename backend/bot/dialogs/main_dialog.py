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
        # placeholder for other scenario dialogs
        self.add_dialog(WaterfallDialog("RestaurantScenarioDialog", []))
        self.add_dialog(WaterfallDialog("ShoppingScenarioDialog", []))
        self.add_dialog(WaterfallDialog("DoctorScenarioDialog", []))
        self.add_dialog(TextPrompt(TextPrompt.__name__))

        self.initial_dialog_id = f"{dialog_id}.waterfall"

    async def select_scenario_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Route to the appropriate scenario based on passed-in scenario or user proficiency."""
        dialog_id = None

        # Scenario explicitly passed from request
        if self.scenario == "taxi":
            dialog_id = "TaxiScenarioDialog"
        elif self.scenario == "restaurant":
            dialog_id = "RestaurantScenarioDialog"
        elif self.scenario == "shopping":
            dialog_id = "ShoppingScenarioDialog"
        elif self.scenario == "hotel":
            dialog_id = "HotelScenarioDialog"
        elif self.scenario == "doctor":
            dialog_id = "DoctorScenarioDialog"
        else:
            dialog_id = "JobInterviewScenarioDialog"

        if not dialog_id:
            await step_context.context.send_activity("❗ No matching scenario available for your settings.")
            return await step_context.end_dialog()

        self.user_state.set_active_dialog(dialog_id)
        return await step_context.begin_dialog(dialog_id)

    async def continue_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Re-enter the active scenario dialog."""
        active_dialog = self.user_state.get_active_dialog()
        if active_dialog:
            return await step_context.replace_dialog(active_dialog)
        return await step_context.replace_dialog(self.id)

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
