from botbuilder.dialogs import (
    WaterfallDialog, WaterfallStepContext, DialogTurnResult, 
    PromptOptions, TextPrompt, DialogTurnStatus
)
from botbuilder.core import MessageFactory
from botbuilder.schema import ActivityTypes, Activity
import asyncio
from .base_dialog import BaseDialog
from backend.bot.state.user_state import UserState

class RestaurantScenarioDialog(BaseDialog):
    def __init__(self, user_state: UserState):
        super().__init__("RestaurantScenarioDialog", user_state)
        self.user_state = user_state
        self.language = self.user_state.get_language()

        # User's order information
        self.food_order = None
        self.drink_order = None
        self.dessert_order = None
        self.payment_method = None
        self.score = 0
        
        # Scoring flags
        self.greeted_server = False
        self.ordered_food = False
        self.ordered_drinks = False
        self.asked_for_bill = False
        self.paid_bill = False
        self.messages = []
        
        # persona
        self.waiter_persona = (
            "You are a polite and professional restaurant waiter. Stay in character throughout the conversation. "
            "Greet the customer, explain menu options, and take food and drink orders. "
            "Avoid complex language and keep your sentences clear. Do not make up exotic meals or prices. "
            "Mention that the total bill is 25 euros. This is a simulation for language learners, so keep it realistic but simple."
        )
        
        # Add prompts
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        
        self.add_dialog(
            WaterfallDialog(
                "RestaurantScenarioDialog.waterfall",
                [
                    self.waiter_greeting,
                    self.take_food_order,
                    self.take_drink_order,
                    self.offer_dessert,
                    self.handle_bill_request,
                    self.process_payment,
                    self.show_feedback,
                    self.end_scenario
                ]
            )
        )
        self.initial_dialog_id = "RestaurantScenarioDialog.waterfall"

    async def waiter_greeting(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # Send step indicator as a separate, more prominent message
        await step_context.context.send_activity(MessageFactory.text("Step One of Five: Meeting your server"))
        
        prompt = await self.chatbot_respond(
            step_context.context,
            "start",
            f"{self.waiter_persona} Greet the customer warmly and ask if they are ready to order."
        )
        
        guidance = "Respond to the waiter with a greeting and ask about the menu or specials."
        example = self.translate_text(
            "Example: Hello! Could you tell me what today's specials are?", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def take_food_order(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Step Two of Five: Ordering food"))
        user_input = step_context.result
        
        # Check spelling and grammar of user input
        feedback = await self.check_spelling_grammar(user_input)
        await step_context.context.send_activity(MessageFactory.text(feedback))
        
        # Track that user greeted the server
        step_context.values["greeted_server"] = True
        
        # Provide a simple menu response
        menu_response = await self.chatbot_respond(
            step_context.context,
            user_input,
            f"{self.waiter_persona} Mention that today's specials are pasta and grilled chicken. Also mention the restaurant has burgers, salads, and fish. Ask what they would like to order for their main course."
        )
        
        await step_context.context.send_activity(MessageFactory.text(menu_response))
        guidance = "Tell the waiter what food you would like to order."
        example = self.translate_text(
            "Example: I'd like to order the pasta, please.", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text("What would you like to order?"))
        )

    async def take_drink_order(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Step Three of Five: Ordering drinks"))
        user_input = step_context.result
        
        # Check spelling and grammar of user input
        feedback = await self.check_spelling_grammar(user_input)
        await step_context.context.send_activity(MessageFactory.text(feedback))
        
        # Store food order
        step_context.values["ordered_food"] = True
        
        prompt = await self.chatbot_respond(
            step_context.context,
            user_input,
            f"{self.waiter_persona} The customer ordered {user_input}. Confirm their food order and ask what they would like to drink. Mention water, soda, juice, and wine are available."
        )
        
        guidance = "Tell the waiter what you would like to drink."
        example = self.translate_text(
            "Example: I'd like a glass of orange juice, please.", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def offer_dessert(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Step Four of Five: Considering dessert"))
        
        # Check spelling and grammar of user input
        user_input = step_context.result
        feedback = await self.check_spelling_grammar(user_input)
        await step_context.context.send_activity(MessageFactory.text(feedback))
        
        # Store drink order
        self.ordered_drinks = True
        step_context.values["ordered_drinks"] = True
        
        # Time passes... food is eaten
        await step_context.context.send_activity(MessageFactory.text("*Time passes as you enjoy your meal...*"))
        prompt = await self.chatbot_respond(
            step_context.context,
            "meal finished",
            f"{self.waiter_persona} The customer has finished their meal. Ask if they would like to see the dessert menu. Mention ice cream, cake, and fruit salad options."
        )
        
        guidance = "Tell the waiter if you want dessert or if you'd like the bill."
        example = self.translate_text(
            "Example: No dessert for me, thank you. Could I have the bill please?", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def handle_bill_request(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Step Five of Five: Paying the bill"))
        user_input = step_context.result

        # Check spelling and grammar of user input
        feedback = await self.check_spelling_grammar(user_input)
        await step_context.context.send_activity(MessageFactory.text(feedback))

        sentiment = self.analyse_sentiment(user_input)
        
        ai_intent = await self.chatbot_respond(
            step_context.context,
            user_input,
            f"{self.waiter_persona} The customer has finished their meal and was offered dessert. They either want dessert or the bill. Determine if they want dessert or the bill. Reply ONLY with 'dessert' or 'bill'.",
            temperature=0.1  # Lower temperature for intent detection
        )

        if sentiment == "positive" or ai_intent.strip().lower() == "dessert":
            self.dessert_order = user_input
            
            # Acknowledge dessert and time skip
            dessert_response = await self.chatbot_respond(
                step_context.context,
                user_input,
                f"{self.waiter_persona} Acknowledge the dessert order briefly. Then fast forward to after they've eaten it."
            )
            await step_context.context.send_activity(MessageFactory.text(dessert_response))
            await step_context.context.send_activity(MessageFactory.text("*Time passes as you enjoy your dessert...*"))

        # Always present the bill
        self.asked_for_bill = True
        step_context.values["asked_for_bill"] = True

        bill_message = await self.chatbot_respond(
            step_context.context,
            user_input,
            f"{self.waiter_persona} Present the final bill. Say: 'Here is your bill. The total is 25 euros. How would you like to pay?'"
        )
        await step_context.context.send_activity(MessageFactory.text(bill_message))

        # Payment guidance
        guidance = "Tell the waiter how you want to pay (cash or card)."
        example = self.translate_text("Example: I'll pay by credit card, please.", self.language)

        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))

        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("How would you like to pay?"))
        )

    async def process_payment(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        user_input = step_context.result
        
        # Check spelling and grammar of user input
        feedback = await self.check_spelling_grammar(user_input)
        await step_context.context.send_activity(MessageFactory.text(feedback))
        
        # Store payment method
        self.payment_method = user_input
        self.paid_bill = True
        step_context.values["paid_bill"] = True
        
        # Final response from waiter
        farewell = await self.chatbot_respond(
            step_context.context,
            user_input,
            f"{self.waiter_persona} The customer wants to pay by {user_input}. Process the payment and thank them for dining at your restaurant. Wish them a good day."
        )
        
        await step_context.context.send_activity(MessageFactory.text(farewell))
        # Calculate score
        self.score = self.calculate_score(step_context)
        self.user_state.update_xp(self.score)
        
        await step_context.context.send_activity(MessageFactory.text("Your restaurant conversation is now complete. Let's see how you did!"))
        return await step_context.next(None)

    async def show_feedback(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Displays performance feedback and score to the user."""
        await step_context.context.send_activity(MessageFactory.text("Scenario Feedback:"))
        
        # Display score
        score_message = f"Your final score: {self.score}/100"
        await step_context.context.send_activity(MessageFactory.text(score_message))
        
        # Display feedback based on score
        feedback = self.generate_feedback()
        await step_context.context.send_activity(MessageFactory.text(feedback))
        
        # Update streak
        self.update_user_streak()
        
        # Send completion event for tracking
        completion_activity = Activity(
            type=ActivityTypes.event,
            name="scenario_complete",
            value={"scenario": "restaurant", "score": self.score}
        )
        await step_context.context.send_activity(completion_activity)
        
        return await step_context.next(None)
    
    async def end_scenario(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Completes the restaurant scenario dialog."""
        thank_you = "Thank you for completing the Restaurant scenario!"
        await step_context.context.send_activity(MessageFactory.text(thank_you))
        await step_context.context.send_activity(MessageFactory.text(self.translate_text(thank_you, self.language)))
        
        return await step_context.end_dialog(result=True)

    def generate_feedback(self) -> str:
        """Generates feedback text based on the user's score."""
        if self.score >= 90:
            return "Excellent job! You ordered your meal clearly and politely."
        elif self.score >= 70:
            return "Good work! You successfully communicated your order."
        else:
            return "Keep practicing! Try to be more specific with your order next time."
    
    def calculate_score(self, step_context: WaterfallStepContext = None) -> int:
        """Calculate score based on interaction quality and task completion."""
        score = 0
        
        # Use step_context values if provided, otherwise fall back to instance variables
        if step_context:
            greeted_server = step_context.values.get("greeted_server", False) or self.greeted_server
            ordered_food = step_context.values.get("ordered_food", False) or self.ordered_food
            ordered_drinks = step_context.values.get("ordered_drinks", False) or self.ordered_drinks
            asked_for_bill = step_context.values.get("asked_for_bill", False) or self.asked_for_bill
            paid_bill = step_context.values.get("paid_bill", False) or self.paid_bill
        else:
            # Fall back to instance variables if no step_context is provided
            greeted_server = self.greeted_server
            ordered_food = self.ordered_food
            ordered_drinks = self.ordered_drinks
            asked_for_bill = self.asked_for_bill
            paid_bill = self.paid_bill
        
        # Basic completion points
        if greeted_server:
            score += 20
                
        if ordered_food:
            score += 20
                
        if ordered_drinks:
            score += 20
            
        if asked_for_bill or paid_bill:
            score += 20
        
        # Base participation score
        score += 20
        
        return min(score, 100)
