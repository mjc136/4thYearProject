from botbuilder.core import MessageFactory
from botbuilder.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
    TextPrompt,
)
from backend.bot.state.user_state import UserState
from .taxi_scenario import TaxiScenarioDialog
from .hotel_scenario import HotelScenarioDialog
from .job_interview_scenario import JobInterviewScenarioDialog
from .base_dialog import BaseDialog

class MainDialog(BaseDialog):
    """
    Main entry point for user interactions.
    This dialog guides users through a scenario based on stored language and proficiency level.
    """
    def __init__(self, user_state: UserState):
        dialog_id = "MainDialog"
        super(MainDialog, self).__init__(dialog_id, user_state)
        self.user_state = user_state

        # Define scenario dialogs
        self.add_dialog(TaxiScenarioDialog(user_state))
        self.add_dialog(HotelScenarioDialog(user_state))
        self.add_dialog(JobInterviewScenarioDialog(user_state))
        self.add_dialog(TextPrompt(TextPrompt.__name__))  # required for WaterfallDialog

        self.add_dialog(WaterfallDialog(f"{dialog_id}.waterfall", [
            self.intro_step,
            self.handle_scenario_step
        ]))

        self.initial_dialog_id = f"{dialog_id}.waterfall"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Welcome user and confirm loaded preferences."""
        language = self.user_state.get_language()
        proficiency = self.user_state.get_proficiency_level()

        await step_context.context.send_activity(
            f"Welcome to LingoLizard! You've selected {language.capitalize()} at {proficiency.capitalize()} level."
        )
        return await step_context.next(None)

    async def handle_scenario_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Automatically route to the correct scenario based on DB user preferences."""
        language = self.user_state.get_language()
        proficiency = self.user_state.get_proficiency_level()

        await step_context.context.send_activity(
            f"Starting your scenario now... (Language: {language}, Level: {proficiency})"
        )

        if proficiency == "beginner":
            return await step_context.begin_dialog("TaxiScenarioDialog")
        elif proficiency == "intermediate":
            return await step_context.begin_dialog("HotelScenarioDialog")
        else:
            return await step_context.begin_dialog("JobInterviewScenarioDialog")
