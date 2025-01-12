from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogSet, PromptOptions
from botbuilder.dialogs.prompts import TextPrompt
from botbuilder.core import TurnContext
from botbuilder.schema import InputHints
from botbuilder.dialogs.prompts import PromptOptions
from botbuilder.core import MessageFactory

class TaxiScenarioDialog(WaterfallDialog):
    def __init__(self):
        super().__init__("taxi_dialog")

        # Add steps to the dialog
        self.add_step(self.ask_destination)
        self.add_step(self.confirm_fare)

    async def ask_destination(self, step_context: WaterfallStepContext):
        """
        Step 1: Ask the user where they would like to go.
        """
        # Use MessageFactory to create a proper message object
        prompt_message = MessageFactory.text("Where would you like to go?")
        return await step_context.prompt(
            "text_prompt",
            PromptOptions(prompt=prompt_message)
        )

    async def confirm_fare(self, step_context: WaterfallStepContext):
        """
        Step 2: Confirm the fare based on the user's destination.
        """
        destination = step_context.result
        fare = 30 if destination.lower() == "airport" else 20
        await step_context.context.send_activity(f"The fare to {destination} is {fare} euros.")
        return await step_context.end_dialog()

