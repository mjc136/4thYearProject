import sys
import os
import logging
from aiohttp import web
from dotenv import load_dotenv
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
    MemoryStorage,
    ConversationState,
    UserState as BotUserState,
)
from botbuilder.schema import Activity
from bot.dialogs.main_dialog import MainDialog
from bot.state.user_state import UserState
from common import app as flask_app

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Load Azure config if available
load_dotenv()
APP_ID = os.getenv("MicrosoftAppId")
APP_PASSWORD = os.getenv("MicrosoftAppPassword")

SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)

async def on_error(context: TurnContext, error: Exception):
    LOGGER.error(f"Unhandled error: {str(error)}", exc_info=True)
    await context.send_activity("Sorry, something went wrong.")

ADAPTER.on_turn_error = on_error

memory = MemoryStorage()
conversation_state = ConversationState(memory)
user_state_property = BotUserState(memory)

async def health_check(req):
    return web.Response(text="Healthy")

async def messages(req):
    try:
        body = await req.json()
        activity = Activity().deserialize(body)
        auth_header = req.headers.get("Authorization", "")
        user_id = req.headers.get("X-User-ID")

        if not user_id:
            return web.Response(status=401, text="Missing X-User-ID header")

        with flask_app.app_context():
            user_state = UserState(user_id)
            dialog = MainDialog(user_state)

        async def turn_logic(turn_context: TurnContext):
            await dialog.run(turn_context, conversation_state.create_property("DialogState"))
            await conversation_state.save_changes(turn_context)
            await user_state_property.save_changes(turn_context)

        await ADAPTER.process_activity(activity, auth_header, turn_logic)
        return web.json_response({"status": "ok"})

    except Exception as e:
        LOGGER.error(f"Message error: {e}", exc_info=True)
        return web.Response(status=500, text="Internal Server Error")

APP = web.Application()
APP.router.add_get("/health", health_check)
APP.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3978))
    LOGGER.info(f"Starting bot on port {port}")
    web.run_app(APP, host="0.0.0.0", port=port)