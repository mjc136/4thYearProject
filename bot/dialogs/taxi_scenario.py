from botbuilder.dialogs import ComponentDialog, WaterfallDialog, WaterfallStepContext, DialogTurnResult
from botbuilder.core import MessageFactory
from .base_dialog import BaseDialog

class TaxiScenarioDialog(BaseDialog):
    def __init__(self):
        super(TaxiScenarioDialog, self).__init__("taxi_dialog")

        self.add_dialog(WaterfallDialog("taxi_scenario", [
            self.intro_step,
            self.testTranslation
        ]))

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity("Welcome to the Taxi Scenario!")
        return await step_context.next(None)
    
    async def testTranslation(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity("This is a test translation.")
        return await step_context.next(None)

