from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions
from botbuilder.dialogs import DialogSet, Dialog
from botbuilder.core import MessageFactory

class MainDialog(WaterfallDialog):
    def __init__(self):
        super().__init__("main_dialog")

        self.add_step(self.ask_language)
        self.add_step(self.ask_proficiency)
        self.add_step(self.start_scenario)

    async def ask_language(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Ask the user to choose a language."""
        prompt_message = MessageFactory.text("What language would you like to practice? (fr, es, pt)")
        return await step_context.prompt(
            "text_prompt",
            PromptOptions(prompt=prompt_message),
        )
    
    async def ask_proficiency(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Ask the user to choose a proficiency."""
        prompt_message = MessageFactory.text("What level of proficiency are you? (beginner, intermediate, advanced)")
        return await step_context.prompt(
            "text_prompt",
            PromptOptions(prompt=prompt_message),
        )

    async def start_scenario(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Route to the selected scenario."""
        user_response = step_context.result.lower()
        # Add logic to route to the selected scenario based on user response
        await step_context.context.send_activity(f"You selected {user_response} proficiency.")
        return await step_context.end_dialog()
