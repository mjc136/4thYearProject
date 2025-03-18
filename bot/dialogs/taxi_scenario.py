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
        
        # conversation markers
        self.greeted = False
        self.change_destination = False
        self.location_confirmed = False
        
        # Add conversation state
        self.destination = None
        self.pickup_location = None
        self.price = None
        self.score = 0
        
        # fallback
        self.fallback = self.translate_text("I didn't catch that. Could you repeat it?", self.language)

        # Initialise dialogues
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        waterfall_dialog = WaterfallDialog(
            f"{dialog_id}.waterfall",
            [
                self.intro_step,
                self.greet_step,
                self.get_destination_step,
                self.confirm_destination_step,
                self.verify_destination,
                self.give_price_step,
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
        if not self.greeted:
            response = "Welcome to the Taxi Scenario! Imagine you just got into a taxi and need to communicate with the driver."
            translated_response = self.translate_text(response, self.language)

            await step_context.context.send_activity(response)
            await step_context.context.send_activity(translated_response)
        return await step_context.next(None)
    
    async def greet_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Greet the user and ask for their pickup location."""
        if not self.greeted:
            await step_context.context.send_activity(Activity(type="typing"))

            prompt = await self.chatbot_respond(
                step_context.context,
                "Greet",
                "You are the taxi driver. Greet the passenger with nothing but a simple hello and ask how are they."
            )
            self.greeted = True
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=MessageFactory.text(prompt))
            )
        return await step_context.next(None)

    async def get_destination_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Process destination and ask for confirmation"""
        await step_context.context.send_activity(Activity(type="typing"))
        if not self.change_destination:
            response = step_context.result

            prompt = await self.chatbot_respond(
                step_context.context,
                response, 
                """only ask your taxi passenger for their destination. You can reply if asked how are you but that is it."""
            )
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=MessageFactory.text(prompt))
            )
        
        prompt = await self.chatbot_respond(
                step_context.context,
                "change", 
                "The user has changed their mind ask your taxi passenger again for their destination."
            )
        return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=MessageFactory.text(prompt))
            )
        
    async def confirm_destination_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Handle destination confirmation"""
        response = step_context.result
        
        # Extract entities from response
        ai_intent = await self.chatbot_respond(
            step_context.context,
            response,
            """Did the user answer 'what location they want to go to'? if they answered with a 
            valid location reply the location otherwise reply 'invalid'."""
        )
        if ai_intent != "invalid":
            self.destination = ai_intent
        else:
            await step_context.context.send_activity(self.fallback)
            return await step_context.replace_dialog(self.id)

        await step_context.context.send_activity(Activity(type="typing"))
        
        if self.destination:
            prompt = await self.chatbot_respond(
                step_context.context,
                response,
                """Ask the user to confirm the destination nothing else.
                As this is just a simulation don't ask for specific names of locations."""
            )
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=MessageFactory.text(prompt))
            )
        else:
            prompt = await self.chatbot_respond(
                step_context.context,
                response,
                "say something like 'I didn't catch the destination. Could you repeat it?'."
            )
            return await step_context.replace_dialog(self.id)
        
    async def verify_destination(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Verifies if user confirmed location."""
        response = step_context.result
        
        ai_intent = await self.chatbot_respond(
            step_context.context,
            response,
            """Does the user confirm the destination, or do they want to change it?
            if they want to change it reply 'change' otherwise reply 'confirm'."""
        )

        if self.analyse_sentiment(response) == "negative" or ai_intent == "change":
            self.change_destination = True
            return await step_context.replace_dialog(self.id)

        # If sentiment is not negative, continue to the next step
        self.location_confirmed = True
        return await step_context.next(None)
    
    async def give_price_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Provide the user with a price estimate."""
        await step_context.context.send_activity(Activity(type="typing"))

        prompt = await self.chatbot_respond(
            step_context.context,
            "price?",
            "Provide the user with a price estimate for the journey. suggest 20 euro. Ask them if it's acceptable."
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )
            
    async def price_negotiation_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Handle price negotiation efficiently."""
        response = step_context.result
        
        ai_intent = await self.chatbot_respond(
            step_context.context,
            response,
            "if the user seems happy with the price reply 'accept' otherwise  reply 'negotiate'."
        )
        
        if ai_intent == "accept":
            return await step_context.next(None)

        # negotiate
        prompt = await self.chatbot_respond(
            step_context.context,
            response,
            """ask for a price if none is offered as a counter and ifonw is and it is between 15 and 20 accept it
            otherwise ask for a price between 15 and 20""",
        )

        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )


# continue from here onwards

    async def confirm_price_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Final price confirmation"""
        response = step_context.result

        await step_context.context.send_activity(Activity(type="typing"))


        prompt = await self.chatbot_respond(
            step_context.context,
            response,
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
        if "thank" in final_response:
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
