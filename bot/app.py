from aiohttp import web
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
    MemoryStorage,
    ConversationState,
)
from botbuilder.schema import Activity, ActivityTypes
from dialogs.main_dialog import MainDialog
from nlu.recogniser import recognise_intent_and_entities
from state.user_state import UserState

# Adapter settings
SETTINGS = BotFrameworkAdapterSettings(app_id="", app_password="")
ADAPTER = BotFrameworkAdapter(SETTINGS)

# State setup
memory = MemoryStorage()
conversation_state = ConversationState(memory)
dialog_state = conversation_state.create_property("DialogState")
user_state = UserState()
main_dialog = MainDialog(user_state)

# Bot message handler
async def messages(req: web.Request) -> web.Response:
    """
    Handles incoming messages from the bot framework.
    """
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    async def turn_logic(turn_context: TurnContext):
        """
        Processes the logic for each turn of the conversation.
        """
        if activity.type == ActivityTypes.conversation_update:
            # Handle new members joining the conversation
            if activity.members_added:
                for member in activity.members_added:
                    if member.id != activity.recipient.id:
                        await turn_context.send_activity("Welcome to the bot!")
                        await main_dialog.run(turn_context, dialog_state)
        else:
            # Recognise user input with the custom recogniser
            intent, entities = recognise_intent_and_entities(turn_context.activity.text)
            await turn_context.send_activity(f"Recognised intent: {intent}, Entities: {entities}")

            # Run the main dialogue
            await main_dialog.run(turn_context, dialog_state)

        # Save any state changes to memory
        await conversation_state.save_changes(turn_context)

    # Process the incoming activity using the adapter
    await ADAPTER.process_activity(activity, auth_header, turn_logic)
    return web.Response()

# Create and run the web application
APP = web.Application()
APP.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    web.run_app(APP, port=3978)
