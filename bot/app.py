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
from bot.dialogs.main_dialog import MainDialog
from bot.state.user_state import UserState
import os
import logging
import sys
from azure.appconfiguration import AzureAppConfigurationClient
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
LOGGER = logging.getLogger(__name__)

if os.path.exists('bot\.env'):
    load_dotenv()  # Load local .env if it exists
    LOGGER.info("Loaded local .env file")
else:
    LOGGER.info("No .env file found, using environment variables")

# Fetch configuration from Azure App Configuration
connection_string = os.getenv("AZURE_APP_CONFIG_CONNECTION_STRING")
if not connection_string:
    LOGGER.error("Azure App Configuration connection string is not set.")
    sys.exit(1)

try:
    app_config_client = AzureAppConfigurationClient.from_connection_string(connection_string)
    APP_ID = app_config_client.get_configuration_setting(key="MicrosoftAppId").value
    APP_PASSWORD = app_config_client.get_configuration_setting(key="MicrosoftAppPassword").value
    LOGGER.info("Fetched App ID and App Password from Azure App Configuration.")
except Exception as e:
    LOGGER.error(f"Error fetching configuration from Azure App Configuration: {e}")
    sys.exit(1)

# Default port
PORT = int(os.getenv("PORT", 3978))

# Adapter settings
SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)

# Error Handler
async def on_error(context: TurnContext, error: Exception):
    LOGGER.error(f"Unhandled error: {str(error)}", exc_info=True)
    await context.send_activity("Sorry, something went wrong.")

ADAPTER.on_turn_error = on_error

# State setup
memory = MemoryStorage()
conversation_state = ConversationState(memory)
user_state_property = BotUserState(memory)
user_state = UserState("default_user")
main_dialog = MainDialog(user_state)

# Health check endpoint
async def health_check(req: web.Request) -> web.Response:
    LOGGER.info("Health check endpoint called.")
    return web.Response(text="Healthy")

# Bot message handler
async def messages(req: web.Request) -> web.Response:
    LOGGER.info("Processing /api/messages endpoint.")

    # Log request headers and body for debugging
    LOGGER.info(f"Request Headers: {req.headers}")
    LOGGER.info(f"Request Body: {await req.text()}")

    try:
        body = await req.json()
        LOGGER.info(f"Received request body: {body}")
        activity = Activity().deserialize(body)
        auth_header = req.headers.get("Authorization", "")

        async def turn_logic(turn_context: TurnContext):
            LOGGER.info("Running main dialog.")
            await main_dialog.run(turn_context, conversation_state.create_property("DialogState"))
            await conversation_state.save_changes(turn_context)
            await user_state_property.save_changes(turn_context)

        await ADAPTER.process_activity(activity, auth_header, turn_logic)
        LOGGER.info("Activity processed successfully.")
        return web.Response(status=200)
    except Exception as e:
        LOGGER.error(f"Error processing message: {str(e)}", exc_info=True)
        return web.Response(status=500, text="Internal Server Error")
    
# Path to the current directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    
# Serve the index.html file at the root URL
async def serve_index(req: web.Request) -> web.Response:
    return web.FileResponse(os.path.join(CURRENT_DIR, 'index.html'))

# Create and configure web app
APP = web.Application()
APP.router.add_get("/health", health_check)
APP.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    try:
        LOGGER.info(f"Starting bot on port {PORT}")
        web.run_app(APP, host='0.0.0.0', port=PORT)
    except Exception as e:
        LOGGER.error(f"Error starting bot: {str(e)}", exc_info=True)
        sys.exit(1)
