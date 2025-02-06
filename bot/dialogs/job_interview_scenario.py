from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult
from .base_dialog import BaseDialog
from bot.state.user_state import UserState

class JobInterviewScenarioDialog(BaseDialog):
    def __init__(self, user_state):
        dialog_id = "JobInterviewScenarioDialog"
        super(JobInterviewScenarioDialog, self).__init__(dialog_id, user_state)
        self.user_state = user_state

        self.add_dialog(WaterfallDialog(f"{dialog_id}.waterfall", [
            self.intro_step,
        ]))

        self.initial_dialog_id = f"{dialog_id}.waterfall"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        print("Debug: Starting intro_step in JobInterviewScenarioDialog")
        text = "Welcome to the Job Interview Scenario! We'll practice phrases used in a job interview."
        translated_text = self.translate_text(text, self.user_state.language)
        
        await step_context.context.send_activity(text)
        await step_context.context.send_activity(translated_text)
        return await step_context.next(None)
    
    
    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        text = "You've completed the job interview scenario!"
        translated_text = self.translate_text(text, self.user_state.language)
        
        await step_context.context.send_activity(text)
        await step_context.context.send_activity(translated_text)
        return await step_context.end_dialog()