from botbuilder.core import MessageFactory, TurnContext
from botbuilder.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
    TextPrompt,
    PromptOptions,
)
from botbuilder.schema import Activity
from backend.bot.state.user_state import UserState
from .base_dialog import BaseDialog

class TaxiScenarioDialog(BaseDialog):
    """Dialog for practising taxi-related conversations."""

    def __init__(self, user_state: UserState):
        super().__init__("TaxiScenarioDialog", user_state)
        self.user_state = user_state
        self.language = self.user_state.get_language()

        self.greeted = False
        self.change_destination = False
        self.location_confirmed = False

        self.destination = None
        self.pickup_location = None
        self.price = None
        self.score = 0

        self.fallback = self.translate_text("I didn't catch that. Could you repeat it?", self.language)

        self.add_dialog(TextPrompt(TextPrompt.__name__))
        waterfall_dialog = WaterfallDialog(
            "TaxiScenarioDialog.waterfall",
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
        self.initial_dialog_id = "TaxiScenarioDialog.waterfall"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if not self.greeted:
            response = "Welcome to the Taxi Practice!\nIn this scenario, you are a passenger speaking to a taxi driver."
            translated = self.translate_text(response, self.language)
            await step_context.context.send_activity(response)
            await step_context.context.send_activity(translated)
            await step_context.context.send_activity("Step 1 of 6: Greeting the driver")
        return await step_context.next(None)

    async def greet_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if not self.greeted:
            await step_context.context.send_activity(Activity(type="typing"))
            prompt = await self.chatbot_respond(
                step_context.context,
                "Greet",
                "You are a friendly taxi driver. Only Greet the passenger with 'Hello! How are you?'"
            )
            example = self.translate_text("Example: Hello! I am Good, how are you?", self.language)
            self.greeted = True
            await step_context.context.send_activity(example)
            return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))
        return await step_context.next(None)

    async def get_destination_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(Activity(type="typing"))
        await step_context.context.send_activity("Step 2 of 6: Saying where you want to go")

        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask: 'Where do you want to go?' Keep it short and simple."
        )
        example = self.translate_text("Example: I want to go to the city centre.", self.language)
        await step_context.context.send_activity(example)
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def confirm_destination_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        response = step_context.result
        ai_intent = await self.chatbot_respond(
            step_context.context,
            response,
            "Check if the user gave a place. If yes, say the place. If not, reply 'invalid'."
        )
        if ai_intent == "invalid":
            await step_context.context.send_activity(self.fallback)
            return await step_context.reprompt_dialog()
        self.destination = ai_intent
        prompt = await self.chatbot_respond(
            step_context.context,
            response,
            f"Confirm the destination: {ai_intent}. Ask: Is that correct?"
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def verify_destination(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        response = step_context.result
        ai_intent = await self.chatbot_respond(
            step_context.context,
            response,
            "Did the user confirm the destination? Reply 'confirm' or 'change'."
        )
        if ai_intent == "change":
            self.change_destination = True
            return await step_context.replace_dialog(self.id)
        self.location_confirmed = True
        return await step_context.next(None)

    async def give_price_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity("Step 3 of 6: Hearing the price")
        await step_context.context.send_activity(Activity(type="typing"))
        prompt = await self.chatbot_respond(
            step_context.context,
            "price?",
            "Say: The trip costs twenty euros. Is that okay?"
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def price_negotiation_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        response = step_context.result
        ai_intent = await self.chatbot_respond(
            step_context.context,
            response,
            "Did the user accept the price? Reply 'accept' or 'negotiate'."
        )
        if ai_intent == "accept":
            return await step_context.next(None)
        prompt = await self.chatbot_respond(
            step_context.context,
            response,
            "Ask: What price would you like to pay? Accept if it's between fifteen and twenty."
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def confirm_price_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity("Step 4 of 6: Confirming price and pickup")
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Say: Great. The taxi will arrive in ten minutes."
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def eta_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity("Step 5 of 6: Asking final questions")
        prompt = await self.chatbot_respond(
            step_context.context,
            "eta confirmation",
            "Say: Do you have any other questions?"
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def final_confirmation_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity("Step 6 of 6: Feedback")
        self.score = self.calculate_score(step_context.result)
        self.user_state.update_score(self.score)
        await step_context.context.send_activity(Activity(type="typing"))
        feedback = self.generate_feedback()
        await step_context.context.send_activity(feedback)
        return await step_context.next(None)

    async def feedback_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        message = f"You finished the scenario! Your score: {self.score}/100"
        translated_message = self.translate_text(message, self.language)
        await step_context.context.send_activity(Activity(type="typing"))
        await step_context.context.send_activity(message)
        await step_context.context.send_activity(translated_message)
        return await step_context.end_dialog()

    def calculate_score(self, final_response: str) -> int:
        score = 70
        if self.pickup_location and self.destination:
            score += 10
        if self.price:
            score += 10
        if "thank" in final_response:
            score += 10
        return min(score, 100)

    def generate_feedback(self) -> str:
        if self.score >= 90:
            return "Excellent job! You spoke clearly and confidently."
        elif self.score >= 70:
            return "Good work! Try to use more full sentences next time."
        else:
            return "Keep practising! Speak slowly and try short answers."
