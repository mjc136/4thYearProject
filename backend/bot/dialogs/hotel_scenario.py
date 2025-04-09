from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult, PromptOptions
from botbuilder.dialogs.prompts import TextPrompt
from botbuilder.core import MessageFactory
from botbuilder.schema import Activity
from .base_dialog import BaseDialog
from bot.state.user_state import UserState
import re

class HotelScenarioDialog(BaseDialog):
    def __init__(self, user_state: UserState):
        dialog_id = "HotelScenarioDialog"
        super().__init__(dialog_id, user_state)
        self.user_state = user_state
        self.language = self.user_state.get_language()

        self.check_in_date = None
        self.check_out_date = None
        self.room_type = None
        self.num_guests = None
        self.special_requests = None
        self.score = 0

        self.add_dialog(TextPrompt(TextPrompt.__name__))
        waterfall_dialog = WaterfallDialog(
            f"{dialog_id}.waterfall",
            [
                self.intro_step,
                self.greet_receptionist_step,
                self.ask_availability_step,
                self.provide_dates_step,
                self.room_type_step,
                self.guests_count_step,
                self.special_requests_step,
                self.confirm_booking_step,
                self.payment_method_step,
                self.final_confirmation_step,
                self.feedback_step
            ]
        )
        self.add_dialog(waterfall_dialog)
        self.initial_dialog_id = f"{dialog_id}.waterfall"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        message = "Welcome to the Hotel Booking Scenario (Intermediate Level)."
        tip = "Try to answer in full sentences and use polite expressions."
        translated_message = self.translate_text(message, self.language)
        translated_tip = self.translate_text(tip, self.language)
        await step_context.context.send_activity(translated_message)
        await step_context.context.send_activity(translated_tip)
        return await step_context.next(None)

    async def greet_receptionist_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(Activity(type="typing"))
        prompt = await self.chatbot_respond(
            step_context.context, "greeting",
            "You are a hotel receptionist. Politely greet the guest and offer assistance."
        )
        await step_context.context.send_activity(self.translate_text("Example: Good afternoon! How can I assist you today?", self.language))
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def ask_availability_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(Activity(type="typing"))
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask for the guest's check-in and check-out dates."
        )
        await step_context.context.send_activity(self.translate_text("Try to include both dates in one sentence.", self.language))
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def provide_dates_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.check_in_date = step_context.result
        await step_context.context.send_activity(Activity(type="typing"))
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask the guest about their preferred room type. Offer a couple of options."
        )
        await step_context.context.send_activity(self.translate_text("Example: I would like a double room, please.", self.language))
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def room_type_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.room_type = step_context.result
        await step_context.context.send_activity(Activity(type="typing"))
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask how many guests will be staying. Encourage complete sentences."
        )
        await step_context.context.send_activity(self.translate_text("Example: There will be two guests.", self.language))
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def guests_count_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.num_guests = step_context.result
        await step_context.context.send_activity(Activity(type="typing"))
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask if the guest has any special requests or preferences."
        )
        await step_context.context.send_activity(self.translate_text("Tip: You could ask for a quiet room or a room on a higher floor.", self.language))
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def special_requests_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.special_requests = step_context.result
        await step_context.context.send_activity(Activity(type="typing"))
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Summarise the booking details and ask the guest to confirm."
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def confirm_booking_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(Activity(type="typing"))
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask for the guest's preferred payment method."
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def payment_method_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(Activity(type="typing"))
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Thank the guest and confirm the reservation details one last time."
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def final_confirmation_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.score = self.calculate_score(step_context.result)
        self.user_state.update_score(self.score)
        await step_context.context.send_activity(Activity(type="typing"))
        feedback = self.generate_feedback()
        await step_context.context.send_activity(feedback)
        return await step_context.next(None)

    async def feedback_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        message = f"You completed the hotel scenario. Your score: {self.score}/100"
        translated_message = self.translate_text(message, self.language)
        await step_context.context.send_activity(Activity(type="typing"))
        await step_context.context.send_activity(message)
        await step_context.context.send_activity(translated_message)
        return await step_context.end_dialog()

    def calculate_score(self, final_response: str) -> int:
        score = 60
        if self.check_in_date and self.check_out_date:
            score += 10
        if self.room_type:
            score += 10
        if self.num_guests:
            score += 10
        if self.special_requests:
            score += 5
        if self.detect_thank_you(final_response):
            score += 5
        return min(score, 100)

    def detect_thank_you(self, text: str) -> bool:
        translated_thanks = ["thank", "gracias", "merci", "obrigado", "obrigada"]
        return any(re.search(rf"\\b{word}\\b", text.lower()) for word in translated_thanks)

    def generate_feedback(self) -> str:
        feedback = "Here's your feedback:\n"
        if self.score >= 90:
            feedback += "Excellent! You handled the intermediate hotel conversation with confidence."
        elif self.score >= 70:
            feedback += "Good work! Try to speak more fluently and include details."
        else:
            feedback += "You're doing well. Focus on making complete sentences and being polite."
        return feedback
