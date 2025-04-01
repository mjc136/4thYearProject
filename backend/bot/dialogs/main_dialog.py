from botbuilder.core import MessageFactory, TurnContext
from botbuilder.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
    TextPrompt,
    DialogTurnStatus,
    DialogSet,
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
        self.add_dialog(TextPrompt(TextPrompt.__name__))

        self.add_dialog(WaterfallDialog(f"{dialog_id}.waterfall", [
            self.intro_step,
            self.handle_scenario_step,
            self.continue_step
        ]))

        self.initial_dialog_id = f"{dialog_id}.waterfall"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Welcome user and confirm loaded preferences."""
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
        if step_context.options and step_context.options.get("continue_conversation"):
            return await step_context.next(None)

        language = self.user_state.get_language()
        proficiency = self.user_state.get_proficiency_level().lower()

        await step_context.context.send_activity(
            f"Starting your scenario now... (Language: {language}, Level: {proficiency})"
        )

        dialog_id = None
        if proficiency == "beginner":
            dialog_id = "TaxiScenarioDialog"
        elif proficiency == "intermediate":
            dialog_id = "HotelScenarioDialog"
        elif proficiency == "advanced":
            dialog_id = "JobInterviewScenarioDialog"

        if not dialog_id:
            await step_context.context.send_activity("No matching scenario for your proficiency level.")
            return await step_context.end_dialog()

        self.user_state.set_active_dialog(dialog_id)
        return await step_context.begin_dialog(dialog_id)

    async def continue_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Handle ongoing conversation within the active scenario."""
        active_dialog = self.user_state.get_active_dialog()
        if active_dialog:
            return await step_context.replace_dialog(active_dialog)
        return await step_context.replace_dialog(self.id)

    async def run(self, turn_context: TurnContext, dialog_state):
        """Run the dialog with the given turn context and state."""
        dialog_set = DialogSet(dialog_state)
        dialog_set.add(self)

        dialog_context = await dialog_set.create_context(turn_context)
        results = await dialog_context.continue_dialog()

        if results.status == DialogTurnStatus.Empty:
            options = {"continue_conversation": True} if self.user_state.get_active_dialog() else {}
            await dialog_context.begin_dialog(self.id, options)

        return True
