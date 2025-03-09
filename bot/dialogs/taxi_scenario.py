from botbuilder.core import MessageFactory
from botbuilder.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
    TextPrompt,
    PromptOptions,
)
from state.user_state import UserState
from .base_dialog import BaseDialog

class TaxiScenarioDialog(BaseDialog):
    """Dialog for practising taxi-related conversations."""
    
    def __init__(self, user_state: UserState):
        """Initialise the taxi scenario dialog."""
        dialog_id = "TaxiScenarioDialog"
        super(TaxiScenarioDialog, self).__init__(dialog_id, user_state)
        self.user_state = user_state
        
        # Initialise dialogues
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        waterfall_dialog = WaterfallDialog(
            f"{dialog_id}.waterfall",
            [
                self.intro_step,
                self.ask_direction_step,
                self.analysis_ask_direction_step,
                self.confirmation_step,
                self.final_step
            ]
        )
        self.add_dialog(waterfall_dialog)
        self.initial_dialog_id = f"{dialog_id}.waterfall"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Initialise dialog state and display welcome message."""
        # Welcome message
        welcome_text = "Welcome to the Taxi Scenario! Let's practice ordering a taxi."
        translated_text = self.translate_text(welcome_text, self.user_state.language)
        await step_context.context.send_activity(welcome_text)
        await step_context.context.send_activity(translated_text)
        return await step_context.next(None)

    async def ask_direction_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Step where user provides their destination."""
        prompt_text = "Where would you like to go?"
        translated_prompt = self.translate_text(prompt_text, self.user_state.language)
        await step_context.context.send_activity(prompt_text)
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(translated_prompt))
        )

    async def analysis_ask_direction_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Extract relevant entities from user input for further processing."""
        user_input = step_context.result
        step_context.active_dialog.state["values"]["user_input"] = user_input
        analysis_results = self.process_text_analysis(user_input)
        
        # Extract relevant entities
        location_entity = next((key for key, value in analysis_results['entities'].items() if "Location" in value), None)
        
        if location_entity:
            step_context.active_dialog.state["values"]["location"] = location_entity
        else:
            step_context.active_dialog.state["values"]["location"] = user_input  # Fallback to raw input
    
        return await step_context.next(None)

    async def confirmation_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Confirm the detected location with the user before finalising."""
        detected_location = step_context.active_dialog.state["values"].get("location", "")
        confirmation_text = f"Just to confirm, you want to go to: {detected_location}?"
        translated_confirmation = self.translate_text(confirmation_text, self.user_state.language)
        await step_context.context.send_activity(confirmation_text)
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(translated_confirmation))
        )

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Final step where the completion message is sent."""
        final_text = "Great! Your taxi is on its way."
        translated_final_text = self.translate_text(final_text, self.user_state.language)
        await step_context.context.send_activity(final_text)
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(translated_final_text))
        )
