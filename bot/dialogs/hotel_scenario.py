from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult, PromptOptions
from botbuilder.dialogs.prompts import TextPrompt
from botbuilder.core import MessageFactory
from .base_dialog import BaseDialog
from bot.state.user_state import UserState

class HotelScenarioDialog(BaseDialog):
    def __init__(self, user_state: UserState):
        dialog_id = "HotelScenarioDialog"
        super().__init__(dialog_id, user_state)
        self.user_state = user_state
        self.language = self.user_state.get_language()
        
        # Add conversation state
        self.check_in_date = None
        self.check_out_date = None
        self.room_type = None
        self.num_guests = None
        self.special_requests = None
        self.score = 0

        # Initialize dialogues
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
        """Initialize dialog state and display welcome message."""
        message = "Welcome to the Hotel Booking Scenario! Let's practice making a hotel reservation."
        translated_message = self.translate_text(message, self.language)
        
        await step_context.context.send_activity(message)
        await step_context.context.send_activity(translated_message)
        return await step_context.next(None)

    async def greet_receptionist_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        prompt = self.chatbot_respond("greeting", "As a hotel receptionist, greet the guest warmly and ask how you can help.")
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def ask_availability_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        prompt = self.chatbot_respond(
            step_context.result,
            "Ask the guest about their intended check-in and check-out dates."
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def provide_dates_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.check_in_date, self.check_out_date = self.extract_dates(step_context.result)
        prompt = self.chatbot_respond(
            step_context.result,
            "Ask the guest about their preferred room type."
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def room_type_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.room_type = step_context.result
        prompt = self.chatbot_respond(
            step_context.result,
            "Ask the guest about the number of guests."
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def guests_count_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.num_guests = step_context.result
        prompt = self.chatbot_respond(
            step_context.result,
            "Ask the guest if they have any special requests."
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def special_requests_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.special_requests = step_context.result
        prompt = self.chatbot_respond(
            step_context.result,
            "Confirm the booking details with the guest."
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def confirm_booking_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        prompt = self.chatbot_respond(
            step_context.result,
            "Ask the guest for their preferred payment method."
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def payment_method_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        prompt = self.chatbot_respond(
            step_context.result,
            "Thank the guest and confirm the booking."
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def final_confirmation_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Wrap up the conversation and calculate score"""
        self.score = self.calculate_score(step_context.result)
        self.user_state.update_score(self.score)
        
        feedback = self.generate_feedback()
        await step_context.context.send_activity(feedback)
        return await step_context.next(None)

    async def feedback_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Provide feedback and score"""
        message = f"Scenario completed! Your score: {self.score}/100"
        translated_message = self.translate_text(message, self.language)
        
        await step_context.context.send_activity(message)
        await step_context.context.send_activity(translated_message)
        return await step_context.end_dialog()

    def calculate_score(self, final_response: str) -> int:
        """Calculate user's performance score"""
        score = 60  # Base score
        if self.check_in_date and self.check_out_date:
            score += 10
        if self.room_type:
            score += 10
        if self.num_guests:
            score += 10
        if self.special_requests:
            score += 5
        if "thank" in final_response.lower():
            score += 5
        return min(score, 100)

    def generate_feedback(self) -> str:
        """Generate personalized feedback based on user performance"""
        feedback = "Here's your feedback:\n"
        if self.score >= 90:
            feedback += "Outstanding! You handled the hotel booking conversation like a native speaker."
        elif self.score >= 70:
            feedback += "Good job! You successfully communicated the essential booking details."
        else:
            feedback += "Keep practicing! Try to include more booking details and polite expressions."
        return feedback
