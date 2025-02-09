from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult, PromptOptions
from botbuilder.dialogs.prompts import TextPrompt
from botbuilder.core import MessageFactory
from .base_dialog import BaseDialog
from bot.state.user_state import UserState

class TaxiScenarioDialog(BaseDialog):
    def __init__(self, user_state: UserState):
        dialog_id = "TaxiScenarioDialog"
        super(TaxiScenarioDialog, self).__init__(dialog_id, user_state)
        self.user_state = user_state

        # Define and add dialogs
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(WaterfallDialog(f"{dialog_id}.waterfall", [
            self.intro_step,  # Introduction step
            self.order_taxi_step,  # Step for ordering a taxi
            self.train_station_step,  # Step for asking to go to train station
            self.ask_for_price_step,  # Step for asking taxi fare
            self.final_step  # Completion step
        ]))

        self.initial_dialog_id = f"{dialog_id}.waterfall"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Welcome the user and start the scenario."""
        welcome_text = "Welcome to the Taxi Scenario! Let's practice ordering a taxi."
        translated_text = self.translate_text(welcome_text, self.user_state.language)  # Translate message

        # Send both original and translated messages
        await step_context.context.send_activity(welcome_text)
        await step_context.context.send_activity(translated_text)
        return await step_context.next(None)  # Move to next step

    async def order_taxi_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Step: Translate 'I would like to order a taxi' and validate."""
        return await self.prompt_and_validate(step_context, "I would like to order a taxi")

    async def train_station_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Step: Translate 'Take me to the train station, please' and validate."""
        return await self.prompt_and_validate(step_context, "Take me to the train station, please")

    async def ask_for_price_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Step: Translate 'How much does the ride cost?' and validate."""
        return await self.prompt_and_validate(step_context, "How much does the ride cost?")

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Complete the scenario."""
        text = "You've completed the taxi scenario!"  # Final message
        translated_text = self.translate_text(text, self.user_state.language)  # Translate the final message

        # Send final message in both languages
        await step_context.context.send_activity(text)
        await step_context.context.send_activity(translated_text)
        return await step_context.end_dialog()  # End the dialog

    async def prompt_and_validate(self, step_context: WaterfallStepContext, text_to_translate: str) -> DialogTurnResult:
        """Helper function to handle translation and validation in one step."""
        if step_context.result:  # If there was a previous response, validate it
            user_translation = step_context.result  # Get user translation
            correct_translation = step_context.values["correct_translation"]  # Get correct translation
            feedback = self.evaluate_response(user_translation, correct_translation)  # Evaluate response
            await step_context.context.send_activity(feedback)  # Provide feedback

        # Set the correct translation for this step
        correct_translation = self.translate_text(text_to_translate, self.user_state.language)  # Correct translation
        step_context.values["correct_translation"] = correct_translation  # Save for validation

        # Ask user for the translation of the phrase
        await step_context.context.send_activity(f"How would you say: '{text_to_translate}'")
        return await step_context.prompt(
            TextPrompt.__name__,  # Prompt for user input
            PromptOptions(prompt=MessageFactory.text("Type your translation:"))  # Prompt text
        )
