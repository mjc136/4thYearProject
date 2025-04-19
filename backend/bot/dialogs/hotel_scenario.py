from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult, PromptOptions
from botbuilder.dialogs.prompts import TextPrompt
from botbuilder.core import MessageFactory
from botbuilder.schema import Activity
from .base_dialog import BaseDialog
from backend.bot.state.user_state import UserState
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
        tip = "Try to answer in full sentences and use polite expressions. You'll get feedback as you go!"
        translated_message = self.translate_text(message, self.language)
        translated_tip = self.translate_text(tip, self.language)
        await step_context.context.send_activity(translated_message)
        await step_context.context.send_activity(translated_tip)
        
        # Initialize performance tracking
        self.responses = []
        self.politeness_score = 0
        self.vocabulary_score = 0
        self.completeness_score = 0
        
        return await step_context.next(None)

    async def greet_receptionist_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        
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
        
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask for the guest's check-in and check-out dates."
        )
        await step_context.context.send_activity(self.translate_text("Try to include both dates in one sentence.", self.language))
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def provide_dates_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.check_in_date = step_context.result
        
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask the guest about their preferred room type. Offer a couple of options."
        )
        await step_context.context.send_activity(self.translate_text("Example: I would like a double room, please.", self.language))
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def room_type_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.room_type = step_context.result
        
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask how many guests will be staying. Encourage complete sentences."
        )
        await step_context.context.send_activity(self.translate_text("Example: There will be two guests.", self.language))
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def guests_count_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.num_guests = step_context.result
        
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask if the guest has any special requests or preferences."
        )
        await step_context.context.send_activity(self.translate_text("Tip: You could ask for a quiet room or a room on a higher floor.", self.language))
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def special_requests_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.special_requests = step_context.result
        
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Summarise the booking details and ask the guest to confirm."
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def confirm_booking_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask for the guest's preferred payment method."
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def payment_method_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Thank the guest and confirm the reservation details one last time."
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def final_confirmation_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.score = self.calculate_score(step_context.result)
        self.user_state.update_score(self.score)
        
        feedback = self.generate_feedback()
        await step_context.context.send_activity(feedback)
        return await step_context.next(None)

    async def feedback_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        message = f"You completed the hotel scenario! Your score: {self.score}/100"
        translated_message = self.translate_text(message, self.language)
        
        await step_context.context.send_activity(message)
        
        detailed_feedback = self.generate_detailed_feedback()
        await step_context.context.send_activity(detailed_feedback)
        
        next_steps = "Would you like to try another scenario to practice different skills?"
        translated_next_steps = self.translate_text(next_steps, self.language)
        await step_context.context.send_activity(translated_next_steps)
        
        return await step_context.end_dialog()

    def calculate_score(self, final_response: str) -> int:
        # Save the final response for feedback
        self.responses.append(final_response)
        
        # Base score starts lower to make room for more granular scoring
        score = 40
        
        # Check for complete booking information
        if self.check_in_date and self.check_out_date:
            score += 10
        if self.room_type:
            score += 10
        if self.num_guests:
            score += 10
        if self.special_requests:
            score += 5
            
        # Politeness and vocabulary assessment
        politeness_points = self.assess_politeness(self.responses)
        vocabulary_points = self.assess_vocabulary(self.responses)
        completeness_points = self.assess_completeness(self.responses)
        
        score += politeness_points + vocabulary_points + completeness_points
        
        # Bonus for thank you
        if self.detect_thank_you(final_response):
            score += 5
            
        return min(score, 100)

    def detect_thank_you(self, text: str) -> bool:
        # Fixed regex pattern (removed extra escapes)
        translated_thanks = ["thank", "gracias", "merci", "obrigado", "obrigada", "danke", "grazie"]
        return any(re.search(r"\b{}\b".format(word), text.lower()) for word in translated_thanks)

    def generate_feedback(self) -> str:
        feedback = "Here's your feedback:\n"
        if self.score >= 90:
            feedback += "Excellent! You handled the intermediate hotel conversation with confidence and used appropriate vocabulary."
        elif self.score >= 70:
            feedback += "Good work! Your communication was clear. Try to use more varied expressions next time."
        else:
            feedback += "You're making progress! Focus on forming complete sentences and using polite expressions."
        return feedback
    
    def generate_detailed_feedback(self) -> str:
        feedback = "Here's your personalized feedback:\n\n"
        
        # Strengths section
        feedback += "💪 **Strengths**:\n"
        if self.politeness_score >= 7:
            feedback += "- Excellent use of polite expressions\n"
        if self.vocabulary_score >= 7:
            feedback += "- Good variety of vocabulary\n"
        if self.completeness_score >= 7:
            feedback += "- Strong, complete responses\n"
        if self.detect_thank_you(self.responses[-1]):
            feedback += "- Good use of thank you expressions\n"
            
        # Areas for improvement
        feedback += "\n📝 **Areas to work on**:\n"
        if self.politeness_score < 7:
            feedback += "- Try using more polite expressions like 'please' and 'thank you'\n"
        if self.vocabulary_score < 7:
            feedback += "- Expand your vocabulary for hotel-related terms\n"
        if self.completeness_score < 7:
            feedback += "- Work on providing complete sentences and details\n"
        
        # General score assessment
        feedback += "\n🌟 **Overall Performance**:\n"
        if self.score >= 90:
            feedback += "Outstanding! You're communicating at an advanced level."
        elif self.score >= 80:
            feedback += "Very good! You're solidly at the intermediate level."
        elif self.score >= 70:
            feedback += "Good work! You're progressing well at the intermediate level."
        else:
            feedback += "You're developing your intermediate skills. Keep practicing!"
        
        # Next steps
        feedback += "\n\n💡 **Tip**: In your next conversation, focus on asking follow-up questions."
        
        return feedback
    
    def assess_politeness(self, responses: list) -> int:
        politeness_markers = ["please", "thank you", "thanks", "appreciate", "grateful", 
                             "would you", "could you", "may i", "pardon", "excuse me"]
        score = 0
        for response in responses:
            if any(marker in response.lower() for marker in politeness_markers):
                score += 1
        
        # Normalize to 10 points maximum
        self.politeness_score = min(10, int(score * 10 / len(responses)))
        return self.politeness_score
    
    def assess_vocabulary(self, responses: list) -> int:
        hotel_vocab = ["room", "booking", "reservation", "check-in", "check-out", 
                      "night", "stay", "accommodation", "single", "double", "key", 
                      "floor", "service", "breakfast", "deposit", "payment"]
        score = 0
        unique_words = set()
        
        for response in responses:
            words = re.findall(r'\b\w+\b', response.lower())
            relevant_words = [word for word in words if word in hotel_vocab]
            unique_words.update(relevant_words)
            
        # Score based on unique relevant vocabulary used
        score = len(unique_words)
        
        # Normalize to 10 points maximum
        self.vocabulary_score = min(10, score)
        return self.vocabulary_score
    
    def assess_completeness(self, responses: list) -> int:
        score = 0
        for response in responses:
            words = len(re.findall(r'\b\w+\b', response))
            if words >= 8:  # Good length response
                score += 1
            if ',' in response or '.' in response:  # Uses punctuation
                score += 0.5
                
        # Normalize to 10 points maximum
        self.completeness_score = min(10, int(score * 10 / len(responses)))
        return self.completeness_score
