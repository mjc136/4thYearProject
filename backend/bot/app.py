import sys
import os
import logging
from aiohttp import web
from dotenv import load_dotenv
from azure.appconfiguration import AzureAppConfigurationClient
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
    MemoryStorage,
    ConversationState,
    UserState as BotUserState,
)
from botbuilder.schema import Activity
from backend.bot.dialogs.main_dialog import MainDialog
from backend.bot.state.user_state import UserState

# ------------------------------------------------------------------------------
# Logging Setup
# ------------------------------------------------------------------------------
logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
LOGGER = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Load .env + Azure Config
# ------------------------------------------------------------------------------
load_dotenv()
connection_string = os.getenv("AZURE_APP_CONFIG_CONNECTION_STRING")

if connection_string:
    try:
        app_config_client = AzureAppConfigurationClient.from_connection_string(connection_string)
        APP_ID = app_config_client.get_configuration_setting(key="MicrosoftAppId").value
        APP_PASSWORD = app_config_client.get_configuration_setting(key="MicrosoftAppPassword").value
        LOGGER.info("Fetched App ID and App Password from Azure App Configuration.")
    except Exception as e:
        LOGGER.warning(f"Could not fetch from Azure App Configuration: {e}")
else:
    APP_ID, APP_PASSWORD = None, None

# ------------------------------------------------------------------------------
# Bot Framework Adapter & States
# ------------------------------------------------------------------------------
#SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
SETTINGS = BotFrameworkAdapterSettings(None,None)
ADAPTER = BotFrameworkAdapter(SETTINGS)

async def on_error(context: TurnContext, error: Exception):
    LOGGER.error(f"Unhandled error: {str(error)}", exc_info=True)
    await context.send_activity("Sorry, something went wrong.")

ADAPTER.on_turn_error = on_error

memory = MemoryStorage()
conversation_state = ConversationState(memory)
user_state_property = BotUserState(memory)
user_state = UserState("default_user")
main_dialog = MainDialog(user_state)

# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------
async def health_check(req: web.Request) -> web.Response:
    return web.Response(text="Healthy")

async def messages(req: web.Request) -> web.Response:
    LOGGER.info("Processing /api/messages")

    try:
        body = await req.json()
        activity = Activity().deserialize(body)
        auth_header = req.headers.get("Authorization", "")

        bot_response = {"text": "", "attachments": []}

        async def turn_logic(turn_context: TurnContext):
            turn_context.turn_state["conversation_state"] = conversation_state
            turn_context.turn_state["user_state_property"] = user_state_property

            async def capture_send_activity(msg):
                if isinstance(msg, str):
                    bot_response["text"] = msg
                elif isinstance(msg, Activity):
                    bot_response["text"] = msg.text or ""
                    if msg.attachments:
                        bot_response["attachments"] = [
                            {
                                "contentType": att.content_type,
                                "content": att.content
                            }
                            for att in msg.attachments
                        ]
                else:
                    bot_response["text"] = str(msg)

                LOGGER.info(f"Bot response: {bot_response}")

            turn_context.send_activity = capture_send_activity

            await main_dialog.run(turn_context, conversation_state.create_property("DialogState"))
            await conversation_state.save_changes(turn_context)
            await user_state_property.save_changes(turn_context)

        await ADAPTER.process_activity(activity, auth_header, turn_logic)

        return web.json_response({
            "bot_reply": bot_response["text"],
            "attachments": bot_response["attachments"]
        })

    except Exception as e:
        LOGGER.error(f"Error processing message: {str(e)}", exc_info=True)
        return web.Response(status=500, text="Internal Server Error")

# ------------------------------------------------------------------------------
# Server Init
# ------------------------------------------------------------------------------
APP = web.Application()
APP.router.add_get("/health", health_check)
APP.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    try:
        PORT = int(os.getenv("PORT", 3978))
        LOGGER.info(f"Starting bot on port {PORT}")
        web.run_app(APP, host="0.0.0.0", port=PORT)
    except Exception as e:
        LOGGER.error(f"Bot startup error: {str(e)}", exc_info=True)
        sys.exit(1)
