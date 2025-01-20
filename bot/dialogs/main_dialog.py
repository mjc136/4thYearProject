from botbuilder.core import MessageFactory
from botbuilder.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
    TextPrompt,
    PromptOptions,
)
from state.user_state import UserState
from .taxi_scenario import TaxiScenarioDialog
from .base_dialog import BaseDialog  

class MainDialog(BaseDialog):
    def __init__(self, user_state: UserState):
        super(MainDialog, self).__init__("MainDialog")
        self.user_state = user_state

        self.add_dialog(TaxiScenarioDialog())
        self.add_dialog(WaterfallDialog("main_dialog", [
            self.intro_step,
            self.language_step,
            self.proficiency_step,
            self.confirm_selection,
            self.handle_scenario_step,
            self.final_step
        ]))
        self.add_dialog(TextPrompt(TextPrompt.__name__))

        self.initial_dialog_id = "main_dialog"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity("Welcome to LingoLizard! Let's start improving your language skills.")
        return await step_context.next(None)

    async def language_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt the user for the language they want to improve."""
        if step_context.result:
            # Save the language to UserState
            language = step_context.result.strip().capitalize()
            self.user_state.set_language(language)
            return await step_context.next(None)

        # Display the hero card with language options
        card_actions = [
            {"type": "imBack", "title": "Spanish", "value": "Spanish"},
            {"type": "imBack", "title": "French", "value": "French"},
            {"type": "imBack", "title": "Portuguese", "value": "Portuguese"},
        ]
        prompt_message = MessageFactory.suggested_actions(card_actions, "Please select the language you would like to practise:")
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=prompt_message))

    async def proficiency_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt the user for proficiency level."""
        if step_context.result:
            # Save the language to UserState
            language = step_context.result.strip().capitalize()
            self.user_state.set_language(language)

        # Prompt the user for proficiency level
        card_actions = [
            {"type": "imBack", "title": "Beginner", "value": "Beginner"},
            {"type": "imBack", "title": "Intermediate", "value": "Intermediate"},
            {"type": "imBack", "title": "Advanced", "value": "Advanced"},
        ]
        prompt_message = MessageFactory.suggested_actions(card_actions, "What is your proficiency level?")
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=prompt_message))
    
    async def handle_scenario_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Trigger the appropriate scenario based on proficiency."""
        print(f"Debug: Proficiency Level = {self.user_state.proficiency_level}")
        if self.user_state.proficiency_level == "Beginner":
            print("Debug: Starting TaxiScenarioDialog")
            await step_context.begin_dialog("taxi_dialog")
            return await step_context.replace_dialog("main_dialog")
        else:
            print("Debug: No scenario matched.")
            await step_context.context.send_activity("No scenario available for this proficiency level.")
            return await step_context.next(None)

    async def confirm_selection(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Save proficiency and proceed to scenario handling."""
        proficiency_level = step_context.result.strip().capitalize()
        try:
            # Validate and save the proficiency level
            self.user_state.set_proficiency_level(proficiency_level)
        except ValueError as e:
            await step_context.context.send_activity(str(e))
            return await step_context.replace_dialog(self.id)

        # Proceed to handle the scenario
        return await step_context.next(None)
    
    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """End the dialog."""
        await step_context.context.send_activity("You have completed the scenario.")
        return await step_context.end_dialog()
