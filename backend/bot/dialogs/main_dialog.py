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
            self.handle_scenario_step,
            self.continue_step
        ]))

        self.initial_dialog_id = f"{dialog_id}.waterfall"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Welcome user and confirm loaded preferences."""
        # Check if we're in an active dialog
        if step_context.options and step_context.options.get("continue_conversation"):
            return await step_context.next(None)
            
        language = self.user_state.get_language()
        proficiency = self.user_state.get_proficiency_level()

        await step_context.context.send_activity(
            f"Welcome to LingoLizard! You've selected {language.capitalize()} at {proficiency.capitalize()} level."
        )
        return await step_context.next(None)

    async def handle_scenario_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Automatically route to the correct scenario based on DB user preferences."""
        # If we're continuing a conversation, skip to continue step
        if step_context.options and step_context.options.get("continue_conversation"):
            return await step_context.next(None)

        language = self.user_state.get_language()
        proficiency = self.user_state.get_proficiency_level()

        await step_context.context.send_activity(
            f"Starting your scenario now... (Language: {language}, Level: {proficiency})"
        )

        dialog_id = None
        if proficiency == "beginner":
            dialog_id = "TaxiScenarioDialog"
        elif proficiency == "intermediate":
            dialog_id = "HotelScenarioDialog"
        else:
            dialog_id = "JobInterviewScenarioDialog"

        # Store the active dialog ID
        self.user_state.set_active_dialog(dialog_id)
        return await step_context.begin_dialog(dialog_id)

    async def continue_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Handle ongoing conversation within the active scenario."""
        active_dialog = self.user_state.get_active_dialog()
        if active_dialog:
            # Replace dialog with the active scenario to continue conversation
            return await step_context.replace_dialog(active_dialog)
        
        # If no active dialog, restart from beginning
        return await step_context.replace_dialog(self.id)

    async def run(self, turn_context, dialog_state):
        """Run the dialog."""
        # Check if we have an ongoing conversation
        active_dialog = self.user_state.get_active_dialog()
        dialog_set = self.create_child_dialog_set(dialog_state)
        
        dialog_context = await dialog_set.create_context(turn_context)
        results = await dialog_context.continue_dialog()
        
        if results.status == DialogTurnStatus.Empty:
            options = {"continue_conversation": True} if active_dialog else {}
            await dialog_context.begin_dialog(self.id, options)
        
        return True
