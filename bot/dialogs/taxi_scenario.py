from botbuilder.core import MessageFactory
from botbuilder.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
    TextPrompt,
    PromptOptions,
)
from bot.state.user_state import UserState
from .base_dialog import BaseDialog

class TaxiScenarioDialog(BaseDialog):
    """Dialog for practicing taxi-related conversations."""
    
    def __init__(self, user_state: UserState):
        """initialise the taxi scenario dialog."""
        dialog_id = "TaxiScenarioDialog"
        super(TaxiScenarioDialog, self).__init__(dialog_id, user_state)
        self.user_state = user_state
        
        # initialise dialogs
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        waterfall_dialog = WaterfallDialog(
            f"{dialog_id}.waterfall",
            [
                self.intro_step,
                self.test_step,
                self.spell_check_step,
                self.final_step
            ]
        )
        self.add_dialog(waterfall_dialog)
        self.initial_dialog_id = f"{dialog_id}.waterfall"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """initialise dialog state and display welcome message."""
        # initialise state if needed
        step_context.active_dialog.state = getattr(step_context.active_dialog, "state", {})
        step_context.active_dialog.state["values"] = step_context.active_dialog.state.get("values", {})
        step_context.active_dialog.state["stepIndex"] = step_context.active_dialog.state.get("stepIndex", 0)
        step_context.active_dialog.state["instanceId"] = step_context.active_dialog.state.get(
            "instanceId", "taxi_scenario_instance"
        )

        # initialise LanguageTool
        self._initialise_language_tool(self.user_state.language)

        # Welcome message
        welcome_text = "Welcome to the Taxi Scenario! Let's practice ordering a taxi."
        translated_text = self.translate_text(welcome_text, self.user_state.language)

        await step_context.context.send_activity(welcome_text)
        await step_context.context.send_activity(translated_text)
        return await step_context.next(None)

    async def test_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Step where user provides their destination."""
        
        text = "Where would you like to go?"
        translated_text = self.translate_text(text, self.user_state.language)
        
        await step_context.context.send_activity(text)
        await step_context.context.send_activity(translated_text)

        # Prompt user for destination
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Type your destination:"))
        )

    async def spell_check_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Step where user input is checked for spelling and grammar errors."""
        user_input = step_context.result
        corrected_text, corrections = self.check_grammar_and_spelling(user_input)

        if corrections:
            correction_message = "**Spelling Mistakes Found:**\n" + "\n".join(corrections)
            await step_context.context.send_activity(correction_message)
        
        step_context.active_dialog.state["values"]["corrected_destination"] = corrected_text
        return await step_context.next(corrected_text)

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Final step where the completion message is sent."""
        text = "You've completed the taxi scenario!"  # Final message
        translated_text = self.translate_text(text, self.user_state.language)  # Translate the final message

        # Send final message in both languages
        await step_context.context.send_activity(text)
        await step_context.context.send_activity(translated_text)
        await step_context.context.send_activity(f"Your final score is: {self.user_state.get_final_score()}")  # Display final score
        return await step_context.end_dialog()  # End the dialog
