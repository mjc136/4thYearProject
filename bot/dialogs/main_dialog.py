from botbuilder.core import MessageFactory
from botbuilder.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
    TextPrompt,
    PromptOptions,
)
from bot.state.user_state import UserState
from .taxi_scenario import TaxiScenarioDialog
from .hotel_scenario import HotelScenarioDialog
from .job_interview_scenario import JobInterviewScenarioDialog
from .base_dialog import BaseDialog

class MainDialog(BaseDialog):
    """
    Main entry point for user interactions.
    This dialog guides users through selecting a language, proficiency level,
    and scenario for practicing language skills.
    """
    def __init__(self, user_state: UserState):
        dialog_id = "MainDialog"
        super(MainDialog, self).__init__(dialog_id, user_state)
        self.user_state = user_state

        # Define scenario dialogs
        taxi_dialog = TaxiScenarioDialog(user_state)
        hotel_dialog = HotelScenarioDialog(user_state)
        job_interview_dialog = JobInterviewScenarioDialog(user_state)

        # Add all available dialogs
        self.add_dialog(taxi_dialog)
        self.add_dialog(hotel_dialog)
        self.add_dialog(job_interview_dialog)
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(WaterfallDialog(f"{dialog_id}.waterfall", [
            self.intro_step,
            self.language_step,
            self.verify_language,
            self.proficiency_step,
            self.verify_proficiency,
            self.handle_scenario_step,
        ]))

        self.initial_dialog_id = f"{dialog_id}.waterfall"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Welcomes the user to LingoLizard and initiates the conversation."""
        await step_context.context.send_activity("Welcome to LingoLizard! Let's start improving your language skills.")
        return await step_context.next(None)  # Proceed to next step

    async def language_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompts the user to select a language to practice."""
        card_actions = [
            {"type": "imBack", "title": "Spanish", "value": "Es"},
            {"type": "imBack", "title": "French", "value": "Fr"},
            {"type": "imBack", "title": "Portuguese", "value": "Pt"},
        ]
        prompt_message = MessageFactory.suggested_actions(card_actions, "Please select the language you would like to practise:")
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=prompt_message))
    
    async def verify_language(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Stores the selected language and moves to proficiency selection."""
        if step_context.result:
            language = step_context.result.strip().capitalize()
            self.user_state.set_language(language)
            await step_context.context.send_activity(f"Selected language: {language}.")
            return await step_context.next(None)
        return await step_context.replace_dialog(self.id)  # Restart dialog if input is invalid

    async def proficiency_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompts the user to select their proficiency level."""
        card_actions = [
            {"type": "imBack", "title": "Beginner", "value": "Beginner"},
            {"type": "imBack", "title": "Intermediate", "value": "Intermediate"},
            {"type": "imBack", "title": "Advanced", "value": "Advanced"},
        ]
        prompt_message = MessageFactory.suggested_actions(card_actions, "What is your proficiency level?")
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=prompt_message))
    
    async def verify_proficiency(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Stores the user's proficiency level and proceeds to scenario selection."""
        if step_context.result:
            proficiency_level = step_context.result.strip().capitalize()
            self.user_state.set_proficiency_level(proficiency_level)
            await step_context.context.send_activity(f"Proficiency level set to {proficiency_level}.")
            return await step_context.next(None)
        return await step_context.replace_dialog(self.id)  # Restart dialog if input is invalid
    
    async def handle_scenario_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Triggers the appropriate scenario based on the selected proficiency level."""
        if self.user_state.proficiency_level == "Beginner":
            return await step_context.begin_dialog("TaxiScenarioDialog")
        elif self.user_state.proficiency_level == "Intermediate":
            return await step_context.begin_dialog("HotelScenarioDialog")
        else:
            return await step_context.begin_dialog("JobInterviewScenarioDialog")
