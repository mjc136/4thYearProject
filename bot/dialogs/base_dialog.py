from botbuilder.dialogs import ComponentDialog, DialogSet, DialogTurnStatus
from botbuilder.core import TurnContext

class BaseDialog(ComponentDialog):
    async def run(self, turn_context: TurnContext, accessor):
        """
        Runs the dialog by creating a DialogSet and continuing or starting the dialog.
        """
        dialog_set = DialogSet(accessor)
        dialog_set.add(self)

        dialog_context = await dialog_set.create_context(turn_context)

        # Continue an active dialog or start a new one
        results = await dialog_context.continue_dialog()
        if results.status == DialogTurnStatus.Empty:
            await dialog_context.begin_dialog(self.id)
