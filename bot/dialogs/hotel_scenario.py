from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult, PromptOptions
from botbuilder.dialogs.prompts import TextPrompt
from botbuilder.core import MessageFactory
from .base_dialog import BaseDialog
from bot.state.user_state import UserState

class HotelScenarioDialog(BaseDialog):
    def __init__(self, user_state: UserState):
        dialog_id = "HotelScenarioDialog"
        super(HotelScenarioDialog, self).__init__(dialog_id, user_state)
        self.user_state = user_state

        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(WaterfallDialog(f"{dialog_id}.waterfall", [
            self.intro_step,             # Introduction to the hotel booking scenario
            self.ask_room_booking_step,  # Asking for room reservation
            self.ask_checkin_date_step,  # Asking for check-in date
            self.ask_checkout_date_step, # Asking for check-out date
            self.ask_room_type_step,     # Asking for room type preference
            self.ask_amenities_step,     # Asking about hotel amenities
            self.final_step              # Completing the scenario
        ]))

        self.initial_dialog_id = f"{dialog_id}.waterfall"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        text = "Welcome to the Hotel Booking Scenario! Let's practice making a hotel reservation."
        translated_text = self.translate_text(text, self.user_state.language)

        await step_context.context.send_activity(text)
        await step_context.context.send_activity(translated_text)
        return await step_context.next(None)

    async def ask_room_booking_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        return await self.prompt_and_validate(step_context, "I would like to book a room")

    async def ask_checkin_date_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        return await self.prompt_and_validate(step_context, "I would like to check in on [date]")

    async def ask_checkout_date_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        return await self.prompt_and_validate(step_context, "I would like to check out on [date]")

    async def ask_room_type_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        return await self.prompt_and_validate(step_context, "I would like a single/double room")

    async def ask_amenities_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        return await self.prompt_and_validate(step_context, "Do you have free Wi-Fi and breakfast included?")

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Complete the hotel booking scenario."""
        text = "You've completed the hotel booking scenario!"
        translated_text = self.translate_text(text, self.user_state.language)

        await step_context.context.send_activity(text)
        await step_context.context.send_activity(translated_text)
        return await step_context.end_dialog()

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
