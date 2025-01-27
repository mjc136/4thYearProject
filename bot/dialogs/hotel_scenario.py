from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult, PromptOptions
from botbuilder.dialogs.prompts import TextPrompt
from botbuilder.core import MessageFactory
from .base_dialog import BaseDialog
from state.user_state import UserState

class HotelScenarioDialog(BaseDialog):
    def __init__(self, user_state: UserState, config=None):
        dialog_id = "HotelScenarioDialog"
        super(HotelScenarioDialog, self).__init__(dialog_id, user_state, config)
        self.user_state = user_state
        self.config = config

        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(WaterfallDialog(f"{dialog_id}.waterfall", [
            self.intro_step,
            self.final_step
        ]))

        self.initial_dialog_id = f"{dialog_id}.waterfall"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        text = "Welcome to the Hotel Booking Scenario! Let's practice making a hotel reservation."
        translated_text = self.translate_text(text, self.user_state.language)
        
        await step_context.context.send_activity(text)
        await step_context.context.send_activity(translated_text)
        return await step_context.next(None)

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        text = "You've completed the hotel booking scenario!"
        translated_text = self.translate_text(text, self.user_state.language)
        
        await step_context.context.send_activity(text)
        await step_context.context.send_activity(translated_text)
        return await step_context.end_dialog()
