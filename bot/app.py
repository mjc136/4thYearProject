from aiohttp import web
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
    MemoryStorage,
    ConversationState,
    UserState as BotUserState,
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
user_state_property = BotUserState(memory)
user_state_accessor = user_state_property.create_property("UserState")
user_state = UserState("default_user")
main_dialog = MainDialog(user_state)

# Bot message handler
async def messages(req: web.Request) -> web.Response:
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    async def turn_logic(turn_context: TurnContext):
        # Run the main dialog
        await main_dialog.run(turn_context, conversation_state.create_property("DialogState"))

        # Save any state changes
        await conversation_state.save_changes(turn_context)
        await user_state_property.save_changes(turn_context)

    # Process the incoming activity using the adapter
    await ADAPTER.process_activity(activity, auth_header, turn_logic)
    return web.Response()

# Create and run the web application
APP = web.Application()
APP.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    web.run_app(APP, port=3978)
