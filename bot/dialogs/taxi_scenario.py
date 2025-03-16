from botbuilder.core import MessageFactory, TurnContext
from botbuilder.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
    TextPrompt,
    PromptOptions,
)
from botbuilder.schema import Activity
from bot.state.user_state import UserState
from .base_dialog import BaseDialog

class TaxiScenarioDialog(BaseDialog):
    """Dialog for practising taxi-related conversations."""
    
    def __init__(self, user_state: UserState):
        """Initialise the taxi scenario dialog."""
        dialog_id = "TaxiScenarioDialog"
        super().__init__(dialog_id, user_state)
        self.user_state = user_state
        self.language = self.user_state.get_language()
        
        # Add conversation state
        self.destination = None
        self.pickup_location = None
        self.price = None
        self.score = 0

        # Initialise dialogues
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        waterfall_dialog = WaterfallDialog(
            f"{dialog_id}.waterfall",
            [
                self.intro_step,
                self.get_pickup_step,
                self.confirm_pickup_step,
                self.get_destination_step,
                self.confirm_destination_step,
                self.price_negotiation_step,
                self.confirm_price_step,
                self.eta_step,
                self.final_confirmation_step,
                self.feedback_step
            ]
        )
        self.add_dialog(waterfall_dialog)
        self.initial_dialog_id = f"{dialog_id}.waterfall"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Initialise dialog state and display welcome message."""
        response = "Welcome to the Taxi Scenario! Let's practise ordering a taxi."
        translated_response = self.translate_text(response, self.language)

        await step_context.context.send_activity(response)
        await step_context.context.send_activity(translated_response)
        return await step_context.next(None)
    
    async def get_pickup_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Ask for pickup location"""

        # Show typing effect
        await step_context.context.send_activity(Activity(type="typing"))


        prompt = await self.chatbot_respond(
            step_context.context, "pickup", "As a taxi dispatcher, ask for the pickup location in a friendly way."
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def confirm_pickup_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Confirm pickup location"""
        self.pickup_location = step_context.result

        await step_context.context.send_activity(Activity(type="typing"))


        prompt = await self.chatbot_respond(
            step_context.context,
            f"confirm pickup at {self.pickup_location}", 
            "Confirm the pickup location and ask for the destination."
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def get_destination_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Process destination and ask for confirmation"""
        self.destination = step_context.result

        await step_context.context.send_activity(Activity(type="typing"))


        prompt = await self.chatbot_respond(
            step_context.context,
            f"going to {self.destination}", 
            "Confirm the destination and mention an estimated price range."
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def confirm_destination_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Handle destination confirmation"""
        response = step_context.result.lower()

        await step_context.context.send_activity(Activity(type="typing"))


        if "yes" in response or "okay" in response:
            prompt = await self.chatbot_respond(
                step_context.context,
                "price negotiation",
                "Suggest a price of roughly 20-30 euro for the journey and ask if it's acceptable."
            )
        else:
            prompt = await self.chatbot_respond(
                step_context.context,
                "request new destination",
                "Politely ask for a new destination."
            )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def price_negotiation_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Handle price negotiation"""
        response = step_context.result.lower()
        self.price = "25"  # Example price

        await step_context.context.send_activity(Activity(type="typing"))


        prompt = await self.chatbot_respond(
            step_context.context,
            f"negotiate price {self.price}",
            "Respond to the price negotiation and ask for final confirmation."
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def confirm_price_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Final price confirmation"""

        await step_context.context.send_activity(Activity(type="typing"))


        prompt = await self.chatbot_respond(
            step_context.context,
            "confirm booking",
            "Confirm the booking and provide an estimated arrival time for the taxi."
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def eta_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Provide ETA information"""

        await step_context.context.send_activity(Activity(type="typing"))


        prompt = await self.chatbot_respond(
            step_context.context,
            "eta confirmation",
            "Thank the user and ask if they need any additional information."
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def final_confirmation_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Wrap up the conversation"""
        self.score = self.calculate_score(step_context.result)
        self.user_state.update_score(self.score)

        await step_context.context.send_activity(Activity(type="typing"))

        feedback = self.generate_feedback()
        await step_context.context.send_activity(feedback)
        return await step_context.next(None)

    async def feedback_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Provide feedback and score"""
        message = f"Scenario completed! Your score: {self.score}/100"
        translated_message = self.translate_text(message, self.language)

        await step_context.context.send_activity(Activity(type="typing"))

        await step_context.context.send_activity(message)
        await step_context.context.send_activity(translated_message)
        return await step_context.end_dialog()

    def calculate_score(self, final_response: str) -> int:
        """Calculate user's performance score"""
        score = 70  # Base score
        if self.pickup_location and self.destination:
            score += 10
        if self.price:
            score += 10
        if "thank" in final_response.lower():
            score += 10
        return min(score, 100)

    def generate_feedback(self) -> str:
        """Generate personalised feedback based on user performance"""
        feedback = "Here's your feedback:\n"
        if self.score >= 90:
            feedback += "Excellent job! Your conversation was very natural and complete."
        elif self.score >= 70:
            feedback += "Good work! You handled the basic conversation well."
        else:
            feedback += "Keep practicing! Try to include more details in your responses."
        return feedback
