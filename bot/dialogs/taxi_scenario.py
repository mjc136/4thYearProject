from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult
from botbuilder.core import MessageFactory
from .base_dialog import BaseDialog
from state.user_state import UserState

class TaxiScenarioDialog(BaseDialog):
    def __init__(self, user_state: UserState, config=None):
        dialog_id = "TaxiScenarioDialog"
        super(TaxiScenarioDialog, self).__init__(dialog_id, user_state, config)
        self.user_state = user_state
        self.config = config

        self.add_dialog(WaterfallDialog(f"{dialog_id}.waterfall", [
            self.intro_step,
            self.scenario_setup,
            self.test_translation,
            self.final_step
        ]))

        self.initial_dialog_id = f"{dialog_id}.waterfall"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        print("Debug: Starting intro_step in TaxiScenarioDialog")
        welcome_text = "Welcome to the Taxi Scenario! We'll practice phrases used when taking a taxi."
        translated_text = self.translate_text(welcome_text, self.user_state.language)
        
        await step_context.context.send_activity(welcome_text)
        await step_context.context.send_activity(translated_text)
        return await step_context.next(None)

    async def scenario_setup(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        setup_text = "Imagine you need to take a taxi to the train station."
        translated_text = self.translate_text(setup_text, self.user_state.language)
        
        await step_context.context.send_activity(setup_text)
        await step_context.context.send_activity(translated_text)
        return await step_context.next(None)

    async def test_translation(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        print("Debug: Starting test_translation in TaxiScenarioDialog")
        text_to_translate = "Could you take me to the train station, please?"
        translated_text = self.translate_text(text_to_translate, self.user_state.language)
        
        await step_context.context.send_activity(f"{text_to_translate}")
        await step_context.context.send_activity(f"{translated_text}")
        return await step_context.next(None)

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        completion_text = "You've completed the taxi scenario!"
        translated_text = self.translate_text(completion_text, self.user_state.language)
        
        await step_context.context.send_activity(completion_text)
        await step_context.context.send_activity(translated_text)
        return await step_context.end_dialog()