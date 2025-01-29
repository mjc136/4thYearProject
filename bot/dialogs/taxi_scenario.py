from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult, PromptOptions
from botbuilder.dialogs.prompts import TextPrompt
from botbuilder.core import MessageFactory
from .base_dialog import BaseDialog
from state.user_state import UserState
from difflib import SequenceMatcher

class TaxiScenarioDialog(BaseDialog):
    def __init__(self, user_state: UserState, config=None):
        dialog_id = "TaxiScenarioDialog"
        super(TaxiScenarioDialog, self).__init__(dialog_id, user_state, config)
        self.user_state = user_state
        self.config = config

        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(WaterfallDialog(f"{dialog_id}.waterfall", [
            self.intro_step,
            self.present_scenario,
            self.validate_translation,
            self.final_step
        ]))

        self.initial_dialog_id = f"{dialog_id}.waterfall"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Welcome the user and start the scenario."""
        welcome_text = "Welcome to the Taxi Scenario! Let's practice ordering a taxi."
        translated_text = self.translate_text(welcome_text, self.user_state.language)
        
        await step_context.context.send_activity(welcome_text)
        await step_context.context.send_activity(translated_text)
        return await step_context.next(None)

    async def present_scenario(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Present the translation task."""
        text_to_translate = "Take me to the train station, please"
        correct_translation = self.translate_text(text_to_translate, self.user_state.language)
        
        # Store for validation
        step_context.values["correct_translation"] = correct_translation
        
        await step_context.context.send_activity(f"How would you say: '{text_to_translate}'")
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Type your translation:"))
        )

    async def validate_translation(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Check the user's translation."""
        user_translation = step_context.result
        correct_translation = step_context.values["correct_translation"]
        
        # Compare translations
        similarity = SequenceMatcher(None, user_translation.lower(), correct_translation.lower()).ratio()
        
        if similarity > 0.8:
            await step_context.context.send_activity("Excellent! That's correct! ⭐")
        elif similarity > 0.5:
            await step_context.context.send_activity(f"Good try! The correct phrase is: {correct_translation}")
        else:
            await step_context.context.send_activity(f"Keep practicing! The correct phrase is: {correct_translation}")
        
        return await step_context.next(None)

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Complete the scenario."""
        text = "You've completed the taxi scenario!"
        translated_text = self.translate_text(text, self.user_state.language)
        
        await step_context.context.send_activity(text)
        await step_context.context.send_activity(translated_text)
        return await step_context.end_dialog()