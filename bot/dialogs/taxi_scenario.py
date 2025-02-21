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
    # This dialog simulates a real-life taxi ordering conversation.
    # The user practices ordering a taxi, giving a destination, and asking for the fare.
    def __init__(self, user_state: UserState):
        dialog_id = "TaxiScenarioDialog"
        super(TaxiScenarioDialog, self).__init__(dialog_id, user_state)
        self.user_state = user_state

        # Define and add the necessary dialog steps.
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
        # Welcome message for the taxi scenario.
        welcome_text = "Welcome to the Taxi Scenario! Let's practice ordering a taxi."
        translated_text = self.translate_text(welcome_text, self.user_state.language)  # Translate message

        # Send both original and translated messages
        await step_context.context.send_activity(welcome_text)
        await step_context.context.send_activity(translated_text)
        return await step_context.next(None)  # Move to next step

    async def order_taxi_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # Step where the user must translate "I would like to order a taxi."
        return await self.prompt_and_validate(step_context, "I would like to order a taxi")

    async def train_station_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # Step where the user must translate "Take me to the train station, please."
        return await self.prompt_and_validate(step_context, "Take me to the train station, please")

    async def ask_for_price_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # Step where the user must translate "How much does the ride cost?"
        return await self.prompt_and_validate(step_context, "How much does the ride cost?")

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # Final message upon completion of the scenario.
        text = "You've completed the taxi scenario!"  # Final message
        translated_text = self.translate_text(text, self.user_state.language)  # Translate the final message

        # Send final message in both languages
        await step_context.context.send_activity(text)
        await step_context.context.send_activity(translated_text)
        await step_context.context.send_activity(f"Your final score is: {self.user_state.get_final_score()}")  # Display final score
        return await step_context.end_dialog()  # End the dialog

    async def prompt_and_validate(self, step_context: WaterfallStepContext, text_to_translate: str) -> DialogTurnResult:
        # Helper function to handle translation and validation in one step.
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
