from botbuilder.core import MessageFactory, TurnContext
from botbuilder.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
    TextPrompt,
    PromptOptions,
)
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

        # Initialise dialogues
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        waterfall_dialog = WaterfallDialog(
            f"{dialog_id}.waterfall",
            [
                self.intro_step,
                self.greeting_step,
                self.test_step,
                self.final_step
            ]
        )
        self.add_dialog(waterfall_dialog)
        self.initial_dialog_id = f"{dialog_id}.waterfall"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Initialise dialog state and display welcome message."""
        repsonse = "Welcome to the Taxi Scenario! Let's practise ordering a taxi."
        translated_repsonse = self.translate_text(repsonse, self.language)

        await step_context.context.send_activity(repsonse)
        await step_context.context.send_activity(translated_repsonse)
        return await step_context.next(None)
    
    async def greeting_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """AI-generated taxi greeting"""        
        # Generate AI greeting
        repsonse = self.chatbot_respond("hello", "Greet the user as a taxi driver. Ask for the user's desired destination.")
        
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(repsonse))
        )
    
    async def test_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Handles the taxi conversation with AI-powered responses."""
        user_input = step_context.result if step_context.result else None

        if user_input:
            # AI response
            repsonse = self.chatbot_respond(user_input, """If the entered location is a valid location, 
                                            respond asking for confirmation otherwise ask for clarification.""")
            
        
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(repsonse))
        )

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Final step where the completion message is sent."""
        repsonse= "You have completed the taxi scenario."
        translated_repsonse = self.translate_text(repsonse, self.language)

        await step_context.context.send_activity(repsonse)
        await step_context.context.send_activity(translated_repsonse)
        
        return await step_context.end_dialog()
