from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, PromptOptions
from botbuilder.dialogs.prompts import TextPrompt
from .base_dialog import BaseDialog  

class HotelScenarioDialog(WaterfallDialog):
    def __init__(self):
        super().__init__("hotel_dialog")

        # Add steps to the dialog
        self.add_step(self.ask_room_type)
        self.add_step(self.confirm_booking)

    async def ask_room_type(self, step_context: WaterfallStepContext):
        """
        Step 1: Ask the user for the type of room they'd like.
        """
        return await step_context.prompt(
            "text_prompt",
            PromptOptions(prompt="What type of room would you like? (Single or Double)")
        )

    async def confirm_booking(self, step_context: WaterfallStepContext):
        """
        Step 2: Confirm the room booking.
        """
        room_type = step_context.result
        await step_context.context.send_activity(f"Your {room_type} room has been booked.")
        return await step_context.end_dialog()
