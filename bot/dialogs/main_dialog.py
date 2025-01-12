from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions
from botbuilder.dialogs import DialogSet, Dialog

class MainDialog(WaterfallDialog):
    def __init__(self):
        super().__init__("main_dialog")

        self.add_step(self.ask_scenario)
        self.add_step(self.start_scenario)

    async def ask_scenario(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Ask the user to choose a scenario."""
        return await step_context.prompt(
            "text_prompt",
            PromptOptions(
                prompt="What scenario would you like to practise? (e.g., Taxi, Hotel)"
            ),
        )

    async def start_scenario(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Route to the selected scenario."""
        user_response = step_context.result.lower()

        if "taxi" in user_response:
            return await step_context.begin_dialog("taxi_dialog")
        elif "hotel" in user_response:
            return await step_context.begin_dialog("hotel_dialog")
        else:
            await step_context.context.send_activity(
                "Sorry, I didn't recognise that scenario. Please try again."
            )
            return await step_context.replace_dialog("main_dialog")
