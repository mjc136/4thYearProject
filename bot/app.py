from aiohttp import web
from aiohttp.web import middleware
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
    MemoryStorage,
    ConversationState,
    UserState as BotUserState,
)
from botbuilder.schema import Activity
from dialogs.main_dialog import MainDialog
from state.user_state import UserState
from config import Config
import os
import logging
import sys

# Configure logging
logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
LOGGER = logging.getLogger(__name__)

# Initialize config with Azure settings
config = Config()
config.validate()

# Azure Bot Service settings
APP_ID = os.getenv("MicrosoftAppId", "")
APP_PASSWORD = os.getenv("MicrosoftAppPassword", "")
PORT = int(os.getenv("PORT", 3978))

# Adapter settings
SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)

# Error Handler
async def on_error(context: TurnContext, error: Exception):
    LOGGER.error(f"Error: {str(error)}")
    await context.send_activity("Sorry, something went wrong.")

ADAPTER.on_turn_error = on_error

# State setup
memory = MemoryStorage()
conversation_state = ConversationState(memory)
user_state_property = BotUserState(memory)
user_state = UserState("default_user")
main_dialog = MainDialog(user_state, config)

# Health check endpoint
async def health_check(req: web.Request) -> web.Response:
    return web.Response(text="Healthy")

# Bot message handler
async def messages(req: web.Request) -> web.Response:
    if req.headers.get("Content-Type") != "application/json":
        return web.Response(status=415)
    
    try:
        body = await req.json()
        activity = Activity().deserialize(body)
        auth_header = req.headers.get("Authorization", "")

        async def turn_logic(turn_context: TurnContext):
            await main_dialog.run(turn_context, conversation_state.create_property("DialogState"))
            await conversation_state.save_changes(turn_context)
            await user_state_property.save_changes(turn_context)

        await ADAPTER.process_activity(activity, auth_header, turn_logic)
        return web.Response(status=200)
    except Exception as e:
        LOGGER.error(f"Error processing message: {str(e)}")
        return web.Response(status=500)

# Create and configure web app
APP = web.Application()
APP.router.add_get("/health", health_check)
APP.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    try:
        LOGGER.info(f"Starting bot on port {PORT}")
        web.run_app(APP, host='0.0.0.0', port=PORT)
    except Exception as e:
        LOGGER.error(f"Error starting bot: {str(e)}")
        sys.exit(1)
