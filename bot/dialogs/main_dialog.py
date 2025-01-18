from botbuilder.core import MessageFactory, TurnContext, CardFactory
from botbuilder.dialogs import (
    ComponentDialog,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
    TextPrompt,
    PromptOptions,
    DialogSet,
    DialogTurnStatus,
)
from botbuilder.schema import HeroCard, CardImage, CardAction, ActionTypes
from state.user_state import UserState

class MainDialog(ComponentDialog):
    def __init__(self, user_state: UserState):
        super(MainDialog, self).__init__("MainDialog")
        self.user_state = user_state

        # Define the waterfall dialog steps
        self.add_dialog(WaterfallDialog("main_dialog", [
            self.intro_step,
            self.language_step,
            self.proficiency_step,
            self.final_step
        ]))
        self.add_dialog(TextPrompt(TextPrompt.__name__))

    async def run(self, turn_context, accessor):
        """
        Runs the dialog.
        """
        dialog_set = DialogSet(accessor)
        dialog_set.add(self)

        dialog_context = await dialog_set.create_context(turn_context)

        # Continue an active dialog or start a new one
        results = await dialog_context.continue_dialog()
        if results.status == DialogTurnStatus.Empty:
            await dialog_context.begin_dialog(self.id)

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """
        Sends a welcome message and proceeds to the next step.
        """
        await step_context.context.send_activity("Welcome to LingoLizard! Let's start improving your language skills.")
        return await step_context.next(None)

    async def language_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """
        Sends the language selection HeroCard and processes user input.
        """
        if step_context.result:
            # Save the language to UserState
            language = step_context.result.strip().capitalize()
            self.user_state.set_language(language)
            return await step_context.next(None)

        # Send the HeroCard for language selection
        card = HeroCard(
            title="Select a Language",
            text="Please select the language you would like to practise:",
            images=[CardImage(url="https://example.com/language-selection-image.png")],
            buttons=[
                CardAction(type=ActionTypes.im_back, title="Spanish", value="Spanish"),
                CardAction(type=ActionTypes.im_back, title="French", value="French"),
                CardAction(type=ActionTypes.im_back, title="Portuguese", value="Portuguese"),
            ],
        )
        await step_context.context.send_activity(MessageFactory.attachment(CardFactory.hero_card(card)))
        return DialogTurnResult(DialogTurnStatus.Waiting)


    async def proficiency_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """
        Prompts the user for their proficiency level.
        """
        prompt_message = MessageFactory.text("What is your proficiency level? (Beginner, Intermediate, Advanced)")
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=prompt_message))

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """
        Saves the proficiency level and concludes the dialog.
        """
        proficiency_level = step_context.result.strip().capitalize()
        try:
            # Validate and save the proficiency level
            self.user_state.set_proficiency_level(proficiency_level)
        except ValueError as e:
            await step_context.context.send_activity(str(e))
            return await step_context.replace_dialog(self.id)

        # Send a confirmation message
        await step_context.context.send_activity(
            MessageFactory.text(
                f"Language set to {self.user_state.language} and proficiency level set to {self.user_state.proficiency_level}."
            )
        )
        return await step_context.end_dialog()
