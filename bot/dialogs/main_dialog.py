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
    def __init__(self, user_state: UserState):
        dialog_id = "MainDialog"
        super(MainDialog, self).__init__(dialog_id, user_state)
        self.user_state = user_state

        # Add dialogs to set
        taxi_dialog = TaxiScenarioDialog(user_state)
        hotel_dialog = HotelScenarioDialog(user_state)
        job_interview_dialog = JobInterviewScenarioDialog(user_state)
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
        await step_context.context.send_activity("Welcome to LingoLizard! Let's start improving your language skills.")
        return await step_context.next(None)

    async def language_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt the user for the language they want to improve."""
        # Display the hero card with language options
        card_actions = [
            {"type": "imBack", "title": "Spanish", "value": "Es"},
            {"type": "imBack", "title": "French", "value": "Fr"},
            {"type": "imBack", "title": "Portuguese", "value": "Pt"},
        ]
        prompt_message = MessageFactory.suggested_actions(card_actions, "Please select the language you would like to practise:")
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=prompt_message))
    
    async def verify_language(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Confirm the selected language and prompt for proficiency level."""
        if step_context.result:
            language = step_context.result.strip().capitalize()
            self.user_state.set_language(language)
            await step_context.context.send_activity(f"Selected language: {language}.")
            return await step_context.next(None)
        return await step_context.replace_dialog(self.id)

    async def proficiency_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt the user for proficiency level."""
        # Prompt the user for proficiency level
        card_actions = [
            {"type": "imBack", "title": "Beginner", "value": "Beginner"},
            {"type": "imBack", "title": "Intermediate", "value": "Intermediate"},
            {"type": "imBack", "title": "Advanced", "value": "Advanced"},
        ]
        prompt_message = MessageFactory.suggested_actions(card_actions, "What is your proficiency level?")
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=prompt_message))
    
    async def verify_proficiency(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Confirm the selected proficiency level and proceed to scenario handling."""
        if step_context.result:
            proficiency_level = step_context.result.strip().capitalize()
            self.user_state.set_proficiency_level(proficiency_level)
            await step_context.context.send_activity(f"Proficiency level set to {proficiency_level}.")
            return await step_context.next(None)
        return await step_context.replace_dialog(self.id)
    
    async def handle_scenario_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Trigger the appropriate scenario based on proficiency."""
        if self.user_state.proficiency_level == "Beginner":
            print("Debug: Starting TaxiScenarioDialog")
            return await step_context.begin_dialog("TaxiScenarioDialog")
        elif self.user_state.proficiency_level == "Intermediate":
            print("Debug: Starting HotelScenarioDialog")
            return await step_context.begin_dialog("HotelScenarioDialog")
        else:
            print("Debug: job_interview_scenario")
            return await step_context.begin_dialog("JobInterviewScenarioDialog")        