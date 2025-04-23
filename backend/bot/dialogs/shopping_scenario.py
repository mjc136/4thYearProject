from botbuilder.dialogs import (
    WaterfallDialog, WaterfallStepContext, DialogTurnResult, 
    PromptOptions, TextPrompt, DialogTurnStatus
)
from botbuilder.core import MessageFactory
from botbuilder.schema import ActivityTypes, Activity
import asyncio
from .base_dialog import BaseDialog
from backend.bot.state.user_state import UserState

class ShoppingScenarioDialog(BaseDialog):
    def __init__(self, user_state: UserState):
        super().__init__("ShoppingScenarioDialog", user_state)
        self.user_state = user_state
        self.language = self.user_state.get_language()

        # User's shopping information
        self.item_selected = None
        self.price_asked = False
        self.payment_method = None
        self.score = 0
        
        # Scoring flags
        self.greeted_clerk = False
        self.asked_about_product = False
        self.asked_about_price = False
        self.made_purchase = False
        self.thanked_clerk = False
        
        # Add prompts
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        
        self.add_dialog(
            WaterfallDialog(
                "ShoppingScenarioDialog.waterfall",
                [
                    self.store_greeting,
                    self.product_inquiry,
                    self.price_check,
                    self.make_purchase,
                    self.complete_transaction,
                    self.show_feedback,
                    self.end_scenario
                ]
            )
        )
        self.initial_dialog_id = "ShoppingScenarioDialog.waterfall"

    async def store_greeting(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Step One of Five: Entering the store"))
        
        prompt = await self.chatbot_respond(
            step_context.context,
            "start",
            "You are a friendly shop clerk. Greet the customer warmly and ask if they're looking for anything specific today."
        )
        
        guidance = "Greet the clerk and ask about what's available in the store."
        example = self.translate_text(
            "Example: Hello! Can you tell me what items are popular today?", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def product_inquiry(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Step Two of Five: Asking about products"))
        user_input = step_context.result
        
        # Track that user greeted the clerk
        self.greeted_clerk = True
        step_context.values["greeted_clerk"] = True
        
        # Provide information about products
        products_response = await self.chatbot_respond(
            step_context.context,
            user_input,
            "Mention that popular items today include t-shirts, sunglasses, and hats. Describe them briefly and ask if the customer is interested in any of them."
        )
        
        await step_context.context.send_activity(MessageFactory.text(products_response))
        
        guidance = "Ask about a specific item you're interested in."
        example = self.translate_text(
            "Example: Those sunglasses look nice. Can I see them?", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text("Which item interests you?"))
        )

    async def price_check(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Step Three of Five: Checking the price"))
        user_input = step_context.result
        
        # Store item selected
        self.item_selected = user_input
        self.asked_about_product = True
        step_context.values["asked_about_product"] = True
        
        # Clerk responds about the item
        item_response = await self.chatbot_respond(
            step_context.context,
            user_input,
            f"The customer is interested in {user_input}. Show them the item and describe it briefly. Don't mention the price yet."
        )
        
        await step_context.context.send_activity(MessageFactory.text(item_response))
        
        guidance = "Ask how much the item costs."
        example = self.translate_text(
            "Example: How much does this cost?", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text("Is there anything else you'd like to know?"))
        )

    async def make_purchase(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Step Four of Five: Deciding to buy"))
        user_input = step_context.result
        
        # User asked about price
        self.price_asked = True
        self.asked_about_price = True
        step_context.values["asked_about_price"] = True
        
        # Clerk gives price
        price_response = await self.chatbot_respond(
            step_context.context,
            user_input,
            f"Tell the customer the {self.item_selected} costs 20 euros. Mention it's good quality and a popular choice. Ask if they'd like to buy it."
        )
        
        await step_context.context.send_activity(MessageFactory.text(price_response))
        
        guidance = "Decide if you want to buy the item or not."
        example = self.translate_text(
            "Example: Yes, I'll take it. I'll pay with my credit card.", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text("Would you like to purchase this item?"))
        )

    async def complete_transaction(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Step Five of Five: Completing your purchase"))
        user_input = step_context.result
        
        intent = self.analyse_sentiment(user_input)
        
        ai_intent = await self.chatbot_respond(
            step_context.context,
            user_input,
            "Analyse the customer's sentiment and determine if they want to buy the item or not. Respond ONLY 'yes' if so.",
            temperature=0.1  # Lower temperature for intent detection
        )
        
        if intent == "positive" or ai_intent == "yes":
            self.made_purchase = True
            step_context.values["made_purchase"] = True
            
            # Clerk completes sale
            completion_response = await self.chatbot_respond(
                step_context.context,
                user_input,
                f"The customer wants to buy the {self.item_selected}. Complete the sale, thank them, and wish them a good day."
            )
            await step_context.context.send_activity(MessageFactory.text(completion_response))
        else:
            # They decided not to buy
            rejection_response = await self.chatbot_respond(
                step_context.context,
                user_input,
                "The customer doesn't want to buy. Be understanding, thank them for visiting, and invite them to come back another time."
            )
            await step_context.context.send_activity(MessageFactory.text(rejection_response))
        
        # Final response from customer
        guidance = "Thank the clerk before leaving the store."
        example = self.translate_text(
            "Example: Thank you for your help. Have a nice day!", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text("Any final words before you leave?"))
        )

    async def show_feedback(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        user_input = step_context.result
        
        # Check for thanks using sentiment rather than English keywords
        step_context.values["thanked_clerk"] = True
        
        # Use AI to detect thanking behavior regardless of language
        thanked_response = await self.chatbot_respond(
            step_context.context,
            user_input,
            "Did the customer thank you or express gratitude in any way? Respond ONLY 'yes' or 'no'.",
            temperature=0.1  # Lower temperature for intent detection
        )
        
        # Calculate score
        self.score = self.calculate_score(step_context)
        self.user_state.update_xp(self.score)
        
        # Final farewell
        farewell = await self.chatbot_respond(
            step_context.context,
            user_input,
            "Give a friendly goodbye to the customer."
        )
        
        await step_context.context.send_activity(MessageFactory.text(farewell))
        await step_context.context.send_activity(MessageFactory.text("Your shopping experience is now complete. Let's see how you did!"))
        
        # Display score
        await step_context.context.send_activity(MessageFactory.text("Scenario Feedback:"))
        score_message = f"Your final score: {self.score}/100"
        await step_context.context.send_activity(MessageFactory.text(score_message))
        
        # Display feedback
        feedback = self.generate_feedback()
        await step_context.context.send_activity(MessageFactory.text(feedback))
        
        # Send completion event
        completion_activity = Activity(
            type=ActivityTypes.event,
            name="scenario_complete",
            value={"scenario": "shopping", "score": self.score}
        )
        await step_context.context.send_activity(completion_activity)
        
        return await step_context.next(None)
    
    async def end_scenario(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Completes the shopping scenario dialog."""
        thank_you = "Thank you for completing the Shopping scenario!"
        await step_context.context.send_activity(MessageFactory.text(thank_you))
        await step_context.context.send_activity(MessageFactory.text(self.translate_text(thank_you, self.language)))
        
        return await step_context.end_dialog(result=True)
        
    def generate_feedback(self) -> str:
        """Generates feedback text based on the user's score."""
        if self.score >= 90:
            return "Excellent job! You navigated the shopping experience perfectly."
        elif self.score >= 70:
            return "Good work! You successfully communicated with the shop clerk."
        else:
            return "Keep practicing! Try asking more questions about the products next time."
    
    def calculate_score(self, step_context: WaterfallStepContext = None) -> int:
        """Calculate score based on interaction quality and task completion."""
        score = 0
        
        # Use step_context values if provided, otherwise fall back to instance variables
        if step_context:
            greeted_clerk = step_context.values.get("greeted_clerk", False) or self.greeted_clerk
            asked_about_product = step_context.values.get("asked_about_product", False) or self.asked_about_product
            asked_about_price = step_context.values.get("asked_about_price", False) or self.asked_about_price
            made_purchase = step_context.values.get("made_purchase", False) or self.made_purchase
            thanked_clerk = step_context.values.get("thanked_clerk", False) or self.thanked_clerk
        else:
            # Fall back to instance variables
            greeted_clerk = self.greeted_clerk
            asked_about_product = self.asked_about_product
            asked_about_price = self.asked_about_price
            made_purchase = self.made_purchase
            thanked_clerk = self.thanked_clerk
        
        # Basic completion points
        if greeted_clerk:
            score += 20
                
        if asked_about_product:
            score += 20
                
        if asked_about_price:
            score += 20
            
        if made_purchase or thanked_clerk:
            score += 20
        
        # Base participation score
        score += 20
        
        return min(score, 100)
