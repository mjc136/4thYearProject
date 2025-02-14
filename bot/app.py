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

# Add the current directory to the system path to ensure relative imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging to track events and errors
logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
LOGGER = logging.getLogger(__name__)

# Load environment variables from .env if present
if os.path.exists('bot/.env'):
    load_dotenv()  # Load local .env if it exists
    LOGGER.info("Loaded local .env file")
else:
    LOGGER.info("No .env file found, using environment variables")

# Fetch configuration from Azure App Configuration
connection_string = os.getenv("AZURE_APP_CONFIG_CONNECTION_STRING")
if not connection_string:
    LOGGER.error("Azure App Configuration connection string is not set.")
    sys.exit(1)  # Terminate execution if configuration is missing

# Attempt to retrieve app credentials from Azure App Configuration
try:
    app_config_client = AzureAppConfigurationClient.from_connection_string(connection_string)
    APP_ID = app_config_client.get_configuration_setting(key="MicrosoftAppId").value  # Fetch bot app ID
    APP_PASSWORD = app_config_client.get_configuration_setting(key="MicrosoftAppPassword").value  # Fetch bot app password
    LOGGER.info("Fetched App ID and App Password from Azure App Configuration.")
except Exception as e:
    LOGGER.error(f"Error fetching configuration from Azure App Configuration: {e}")
    sys.exit(1)  # Terminate if fetching credentials fails

# Define the default port the bot will listen on
PORT = int(os.getenv("PORT", 3978))  # Use 3978 as the default if PORT is not set

# Create adapter settings for the bot framework
SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)  # Initialize the bot adapter

# Define the bot's error handler
async def on_error(context: TurnContext, error: Exception):
    """
    Handles any errors that occur during bot execution.
    Logs the error and notifies the user that something went wrong.
    """
    LOGGER.error(f"Unhandled error: {str(error)}", exc_info=True)
    await context.send_activity("Sorry, something went wrong.")

# Assign the error handler to the adapter
ADAPTER.on_turn_error = on_error

# Initialize bot state management
memory = MemoryStorage()  # In-memory storage for bot state
conversation_state = ConversationState(memory)  # Maintain conversation state
user_state_property = BotUserState(memory)  # User state storage
user_state = UserState("default_user")  # Default user state handler
main_dialog = MainDialog(user_state)  # Main dialog for handling user interactions

# Define a health check endpoint
async def health_check(req: web.Request) -> web.Response:
    """
    Responds with a simple text message to indicate the bot is running.
    This can be used by external monitoring tools to check if the bot service is up.
    """
    LOGGER.info("Health check endpoint called.")
    return web.Response(text="Healthy")

# Serve index.html at the root URL
async def serve_index(req: web.Request) -> web.Response:
    """
    Serves the index.html file if it exists.
    This allows users to interact with the bot via a basic web interface.
    If the file is missing, returns a 404 error.
    """
    index_path = "index.html"
    LOGGER.info(f"Serving index.html from: {index_path}")
    if os.path.exists(index_path):
        return web.FileResponse(index_path)
    else:
        LOGGER.error(f"index.html not found at {index_path}")
        return web.Response(status=404, text="index.html not found")

# Handle bot messages
async def messages(req: web.Request) -> web.Response:
    """
    Processes incoming messages from users and routes them to the bot.
    This function extracts user messages, authenticates them, and executes the bot's logic.
    """
    LOGGER.info("Processing /api/messages endpoint.")

    # Log request details for debugging
    LOGGER.info(f"Request Headers: {req.headers}")
    LOGGER.info(f"Request Body: {await req.text()}")

    try:
        body = await req.json()  # Parse the request body as JSON
        LOGGER.info(f"Received request body: {body}")
        activity = Activity().deserialize(body)  # Convert JSON to Activity object
        auth_header = req.headers.get("Authorization", "")  # Get authentication header

        # Define the bot's turn logic
        async def turn_logic(turn_context: TurnContext):
            """Handles user interactions by running the main dialog."""
            LOGGER.info("Running main dialog.")
            await main_dialog.run(turn_context, conversation_state.create_property("DialogState"))
            await conversation_state.save_changes(turn_context)  # Save conversation state
            await user_state_property.save_changes(turn_context)  # Save user state

        # Process the incoming activity
        await ADAPTER.process_activity(activity, auth_header, turn_logic)
        LOGGER.info("Activity processed successfully.")
        return web.Response(status=200)
    except Exception as e:
        LOGGER.error(f"Error processing message: {str(e)}", exc_info=True)
        return web.Response(status=500, text="Internal Server Error")

# Create and configure the web application
APP = web.Application()
APP.router.add_get("/", serve_index)  # Serve the index page
APP.router.add_get("/health", health_check)  # Health check endpoint
APP.router.add_post("/api/messages", messages)  # Bot message processing endpoint

# Start the web application
if __name__ == "__main__":
    try:
        LOGGER.info(f"Starting bot on port {PORT}")
        web.run_app(APP, host='0.0.0.0', port=PORT)  # Start the web server
    except Exception as e:
        LOGGER.error(f"Error starting bot: {str(e)}", exc_info=True)
        sys.exit(1)  # Terminate if bot fails to start
