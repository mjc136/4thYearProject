from botbuilder.dialogs import (
    ComponentDialog, DialogContext, DialogTurnResult,
    DialogTurnStatus, WaterfallDialog, WaterfallStepContext, TextPrompt, PromptOptions
)
from botbuilder.core import TurnContext, MessageFactory
from botbuilder.schema import ActivityTypes, Activity
import logging
import os
from .base_dialog import BaseDialog
from backend.bot.state.user_state import UserState


class TaxiScenarioDialog(BaseDialog):
    """Dialog for practising taxi-related conversations."""

    def __init__(self, user_state: UserState):
        super().__init__("TaxiScenarioDialog", user_state)
        self.user_state = user_state
        self.language = self.user_state.get_language()
        self.messages = []

        # Scenario state
        self.greeted = False
        self.destination = None
        self.price = None
        self.base_price = 20  # Base price for the taxi ride
        self.score = 0

        # Scoring flags
        self.greet_success = False
        self.asked_for_destination = False
        self.user_gave_destination = False
        self.destination_confirmed = False
        self.destination_changed = False
        self.price_offered = False
        self.user_accepted_price = False
        self.user_negotiated = False
        self.valid_negotiated_price = False

        self.taxi_persona = (
            f"You are playing the role of a taxi driver. "
            f"You ONLY offer taxi service - never suggest buses, trains, or other transportation alternatives. "
            f"You only accept payment in euros. "
            f"Always stay in character as a taxi driver throughout the conversation. "
            f"Don't mention anything about the meter. "
            f"If a user says 'hotel', just accept it as a location. Same for other general location names. "
            f"Don't write any 'Notes:' in your response. "
            f"The user is a non-native speaker of {self.language} and is learning the language, so do not use complex words. "
            f"This is a simulation for a taxi ride. do not ask for specific details about the taxi ride like street names."
        )

        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(
            WaterfallDialog(
                "TaxiScenarioDialog.waterfall",
                [
                    self.display_scenario_introduction,  # Renamed from intro_step
                    self.handle_initial_greeting,        # Renamed from greet_step
                    self.request_destination,            # Renamed from get_destination_step
                    self.confirm_destination_with_user,  # Renamed from confirm_destination_step
                    self.validate_destination_response,  # Renamed from verify_destination
                    self.provide_price_quote,            # Renamed from give_price_step
                    self.handle_price_negotiation,       # Renamed from price_negotiation_step
                    self.validate_negotiated_price,      # Renamed from verify_price_step
                    self.finalise_trip_details,          # Renamed from confirm_price_step
                    self.prepare_scenario_feedback,      # Renamed from final_confirmation_step
                    self.display_user_score,             # Renamed from feedback_step
                    self.end_taxi_scenario               # Renamed from completion_step
                ]
            )
        )
        self.initial_dialog_id = "TaxiScenarioDialog.waterfall"

    def get_fallback(self):
        """Returns a fallback message when user input is not understood."""
        return self.translate_text("I didn't catch that. Could you repeat it?", self.language)
    
    def add_to_memory(self, user_message: str, bot_response: str):
        """Add a user message and bot response to memory for context tracking."""
        self.messages.append({"user": user_message, "bot": bot_response})
        if len(self.messages) > 10:  # Limit memory to the last 10 exchanges
            self.messages.pop(0)

    def get_memory(self) -> str:
        """Retrieve the conversation memory as a formatted string for context awareness."""
        return "\n".join([f"User: {msg['user']}\nBot: {msg['bot']}" for msg in self.messages])

    async def display_scenario_introduction(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Introduces the taxi scenario and explains the context to the user."""
        if not self.greeted:
            intro = "Welcome to the Taxi Practice!\nIn this scenario, you are a passenger speaking to a taxi driver."
            await step_context.context.send_activity(MessageFactory.text(intro))
            await step_context.context.send_activity(MessageFactory.text(self.translate_text(intro, self.language)))
            await step_context.context.send_activity(MessageFactory.text("Step 1 of 5: Greeting the driver"))
        return await step_context.next(None)

    async def handle_initial_greeting(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Handles the greeting phase where the taxi driver greets the user."""
        if not self.greeted:
            await step_context.context.send_activity(Activity(type="typing"))
            prompt = await self.chatbot_respond(
                step_context.context,
                "start",
                f"Greet the user and ask how they are doing. That is all."
            )
            example = self.translate_text("Example: Hello! I am good, how are you?", self.language)
            self.greeted = True
            self.greet_success = True
            await step_context.context.send_activity(MessageFactory.text(example))
            return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))
        return await step_context.next(None)

    async def request_destination(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompts the user to provide their desired destination."""
        await step_context.context.send_activity(MessageFactory.text("Step 2 of 5: Saying where you want to go"))
        await step_context.context.send_activity(Activity(type="typing"))
        self.asked_for_destination = True
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            f"{self.taxi_persona} Ask the passenger where they would like to go. Don't mention the price. You have already greeted them."
        )
        example = self.translate_text("Example: I want to go to the city centre.", self.language)
        await step_context.context.send_activity(MessageFactory.text(example))
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def confirm_destination_with_user(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Extracts and confirms the destination provided by the user."""
        response = step_context.result
        
        locations = self.entity_extraction(response, "Location")
        if locations:
            self.destination = locations[0]
            self.user_gave_destination = True
            self.destination_confirmed = True
            self.destination_changed = False
            prompt = await self.chatbot_respond(
                step_context.context,
                response,
                f"{self.taxi_persona} Confirm the destination is '{self.destination}'. Ask ONLY: 'Is that correct?'. Absolutely DO NOT mention the price or cost yet."
            )
            return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))
        else:
            await step_context.context.send_activity(MessageFactory.text(self.get_fallback()))
            self.destination_changed = True
            prompt = await self.chatbot_respond(
                step_context.context,
                response,
                f"{self.taxi_persona} The user did not give a valid destination. Ask them again: 'Where would you like to go?'"
            )
            return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def validate_destination_response(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Validates if the user confirmed the destination or needs to change it."""
        ai_intent = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            f"{self.taxi_persona} The user said '{step_context.result}'. Did they clearly confirm the destination? Reply ONLY 'yes' or 'no'."
        )
        sentiment = self.analyse_sentiment(step_context.result)
        if sentiment == "positive" or ("yes" in ai_intent.lower()):
            self.destination_confirmed = True
            self.destination_changed = False
            self.user_gave_destination = True
            return await step_context.next(None)
        else:
            self.destination_changed = True
            prompt = await self.chatbot_respond(
                step_context.context,
                step_context.result,
                f"{self.taxi_persona} The user is not happy with the destination. Ask them again: 'Where would you like to go?'"
            )
            return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def provide_price_quote(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Provides the base price quote for the taxi journey to the destination."""
        if self.price:
            return await step_context.next(None)
            
        confirmed_destination = self.destination 
        
        await step_context.context.send_activity(MessageFactory.text("Step 3 of 5: Hearing the price"))
        self.price_offered = True
        
        prompt = await self.chatbot_respond(
            step_context.context,
            f"Destination confirmed: {confirmed_destination}",
            f"{self.taxi_persona} The destination is confirmed as '{confirmed_destination}'. Now, state the price. Say ONLY: 'The trip costs twenty euros. Is that okay?'"
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def handle_price_negotiation(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Handles the user's response to the price quote - acceptance or negotiation."""
        if self.price:
            return await step_context.next(None)

        response = step_context.result
        sentiment = self.analyse_sentiment(response)
            
        ai_intent = await self.chatbot_respond(
            step_context.context,
            response,
            f"{self.taxi_persona}The user was just told the price is {self.base_price} euros and asked 'Is that okay?'. Did the user clearly accept the price? Reply ONLY 'accept' or 'negotiate'."
        )

        if sentiment == "positive" or ("accept" in ai_intent.lower()):
            self.price = self.base_price
            self.user_accepted_price = True
            return await step_context.next(None) 

        self.user_negotiated = True
        prompt = await self.chatbot_respond(
            step_context.context,
            "Destination confirmed: {confirmed_destination}",
            f"{self.taxi_persona} The user wants to negotiate the price 20 euros to their destination '{self.destination}'.DON'T ASK: for their destination again Ask: 'What price would you like to pay?"
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def validate_negotiated_price(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Validates the user's suggested price from the negotiation."""
        if self.user_accepted_price:
            return await step_context.next(None)
            
        response = step_context.result

        price = self.entity_extraction(response, "Quantity",)
        
        if not price:
            await step_context.context.send_activity(MessageFactory.text(self.get_fallback()))
            prompt = await self.chatbot_respond(
                step_context.context,
                response,
                f"{self.taxi_persona} The user did not give a valid price. Ask them again: 'What price would you like to pay?'"
            )
            return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))
        else:
            self.price_offered = True
            self.valid_negotiated_price = True
        
        if int(price) > 15 and int(price) < 20:
            self.price = int(price)
            self.user_accepted_price = True
            self.valid_negotiated_price = True
            return await step_context.next(None)
        elif int(price) > 20:
            self.price = int(price)
            self.user_accepted_price = True
            self.valid_negotiated_price = True
            await step_context.context.send_activity(MessageFactory.text(self.translate_text("That's a bit too much. I can only accept 20 euros."), self.language))
            return await step_context.next(None)
        elif int(price) < 15:
            self.price = int(price)
            self.user_accepted_price = True
            self.valid_negotiated_price = True
            await step_context.context.send_activity(MessageFactory.text(self.translate_text("That's a bit too low. I can only accept up to 15 euros at the lowest."), self.language))
            return await step_context.next(None)
        else:
            await step_context.context.send_activity(MessageFactory.text(self.get_fallback()))
            prompt = await self.chatbot_respond(
                step_context.context,
                response,
                f"{self.taxi_persona} The user did not give a valid price. Ask them again: 'What price would you like to pay?'"
            )
            return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def finalise_trip_details(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Finalises the trip details after price agreement and confirms journey start."""
        await step_context.context.send_activity("Step 4 of 5: Confirming price")
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            f"{self.taxi_persona} User has confirmed destination and fare. Say: Great. We'll start driving right away. Please get in. I will take you to {self.destination}. "
        )
        return await step_context.context.send_activity(MessageFactory.text(prompt))

    async def prepare_scenario_feedback(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prepares feedback for the user based on their interaction during the scenario."""
        await step_context.context.send_activity("Step 5 of 5: Feedback")
        self.score = self.calculate_score()
        self.user_state.update_xp(self.score)
        await step_context.context.send_activity(Activity(type="typing"))
        await step_context.context.send_activity(self.generate_feedback())
        return await step_context.next(None)

    async def display_user_score(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Displays the user's score and completes the scenario."""
        message = f"You finished the scenario! Your score: {self.score}/100"
        translated = self.translate_text(message, self.language)
        await step_context.context.send_activity(Activity(type="typing"))
        await step_context.context.send_activity(message)
        await step_context.context.send_activity(translated)

        completion_activity = Activity(
            type=ActivityTypes.event,
            name="scenario_complete",
            value={"scenario": "taxi", "score": self.score}
        )
        await step_context.context.send_activity(completion_activity)
        return await step_context.next(None)

    async def end_taxi_scenario(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Concludes the taxi scenario with farewell messages."""
        await step_context.context.send_activity("Thank you for using the taxi scenario!")
        await step_context.context.send_activity(self.translate_text("Thank you for using the taxi scenario!", self.language))
        await step_context.context.send_activity("Goodbye!")
        await step_context.context.send_activity(self.translate_text("Goodbye!", self.language))
        return await step_context.end_dialog()

    def calculate_score(self) -> int:
        """Calculates the user's score based on their performance in the scenario."""
        score = 45  # Base score for completing the scenario
        
        print(f"[DEBUG] greet_success: {self.greet_success}")
        print(f"[DEBUG] user_gave_destination: {self.user_gave_destination}")
        print(f"[DEBUG] destination_confirmed: {self.destination_confirmed}")
        print(f"[DEBUG] price_offered: {self.price_offered}")
        print(f"[DEBUG] user_accepted_price: {self.user_accepted_price}")
        print(f"[DEBUG] valid_negotiated_price: {self.valid_negotiated_price}")
        
        if self.greet_success:
            score += 10
        if self.user_gave_destination:
            score += 15
        if self.destination_confirmed:
            score += 10
        if self.price_offered:
            score += 10
        if self.user_accepted_price or self.valid_negotiated_price:
            score += 10
            
        return min(score, 100)

    def generate_feedback(self) -> str:
        """Generates feedback text based on the user's score."""
        if self.score >= 90:
            return "Excellent job! You spoke clearly and confidently."
        elif self.score >= 70:
            return "Good work! Try to use more full sentences next time."
        else:
            return "Keep practising!"
