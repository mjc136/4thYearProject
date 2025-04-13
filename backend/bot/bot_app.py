import sys
import os
import logging
from aiohttp import web
from dotenv import load_dotenv
import re
import json
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
    MemoryStorage,
    ConversationState,
    UserState as BotUserState,
    AnonymousReceiveMiddleware
)
from botbuilder.schema import Activity, ResourceResponse
from backend.bot.dialogs.main_dialog import MainDialog
from backend.bot.state.user_state import UserState
from backend.common import app as flask_app
from azure.core.exceptions import DeserializationError
from azure.appconfiguration import AzureAppConfigurationClient
import time
import threading

# Configure logging
logging.basicConfig(
    level=logging.getLevelName(os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
LOGGER = logging.getLogger(__name__)

# Load environment variables from .env file first
load_dotenv()

# Function to load environment variables from Azure App Configuration
def load_azure_app_config():
    """Load environment variables from Azure App Configuration."""
    connection_string = os.getenv("AZURE_APP_CONFIG_CONNECTION_STRING")
    
    if not connection_string:
        LOGGER.warning("Azure App Configuration connection string not found. Using local environment variables only.")
        return False
    
    # Set up a timeout for Azure App Configuration loading
    def fetch_config():
        nonlocal config_loaded
        try:
            # Connect to Azure App Configuration
            LOGGER.info("Connecting to Azure App Configuration...")
            client = AzureAppConfigurationClient.from_connection_string(connection_string)
            
            # Define the list of configuration keys we need to load
            config_keys = [
                "AI_API_KEY",
                "AI_ENDPOINT",
                "TRANSLATOR_KEY",
                "TRANSLATOR_ENDPOINT", 
                "TRANSLATOR_LOCATION",
                "TEXT_ANALYTICS_KEY",
                "TEXT_ANALYTICS_ENDPOINT",
                "MicrosoftAppId",
                "MicrosoftAppPassword"
            ]
            
            # Only try to load if not already in environment
            for key in config_keys:
                if os.getenv(key):
                    LOGGER.info(f"Skipping {key} - already set in environment")
                    continue
                    
                try:
                    setting = client.get_configuration_setting(key=key)
                    os.environ[key] = setting.value
                    LOGGER.info(f"Loaded {key} from Azure App Configuration.")
                except Exception as e:
                    LOGGER.warning(f"Failed to load {key} from Azure App Configuration: {str(e)}")
            
            config_loaded = True
        except Exception as e:
            LOGGER.error(f"Error connecting to Azure App Configuration: {str(e)}")
            config_loaded = False
    
    # Run config loading with a timeout
    config_loaded = False
    config_thread = threading.Thread(target=fetch_config)
    config_thread.daemon = True
    config_thread.start()
    
    # Wait up to 5 seconds for config to load
    config_thread.join(timeout=5.0)
    
    if config_thread.is_alive():
        LOGGER.warning("Azure App Configuration loading timed out after 5 seconds. Using environment variables.")
        return False
    
    return config_loaded

# Load variables from Azure App Configuration before initializing other services
load_azure_app_config()

# Now get environment variables (prioritizing ones loaded from Azure App Config)
APP_ID = os.getenv("MicrosoftAppId", "")
APP_PASSWORD = os.getenv("MicrosoftAppPassword", "")

# For local development without authentication
BYPASS_AUTH = os.getenv("BYPASS_AUTH", "true").lower() == "true"
LOGGER.info(f"Authentication bypass is {'enabled' if BYPASS_AUTH else 'disabled'}")

SETTINGS = BotFrameworkAdapterSettings(
    app_id=APP_ID,
    app_password=APP_PASSWORD,
    auth_configuration=None if BYPASS_AUTH else None  # We'll handle auth manually
)

# Custom adapter to handle direct responses without going through Bot Framework
class DirectResponseAdapter(BotFrameworkAdapter):
    async def send_activities(self, context: TurnContext, activities):
        """Custom implementation to bypass Bot Framework connector for local conversations."""
        if (context.activity and context.activity.service_url and 
            (context.activity.service_url.startswith('http://localhost') or
             context.activity.service_url == 'http://localhost')):
            
            LOGGER.info("Using direct response adapter")
            responses = []
            for activity in activities:
                # Create a resource response locally
                response = ResourceResponse(id=activity.id or "direct-response")
                responses.append(response)
                
                # Store the activity in the turn state so we can access it in our handler
                if not hasattr(context, "sent_activities"):
                    context.sent_activities = []
                context.sent_activities.append(activity)
                
            return responses
        # Fall back to standard behavior for non-local conversations
        return await super().send_activities(context, activities)
    
    async def process_activity(self, req_body, auth_header, logic):
        """Override to bypass authentication for local development."""
        try:
            return await super().process_activity(req_body, auth_header, logic)
        except Exception as e:
            error_message = str(e)
            if ("Authorization" in error_message or "authentication" in error_message.lower()) and BYPASS_AUTH:
                LOGGER.info("Bypassing authentication error for local development")
                # Convert the body to an Activity
                activity = Activity().deserialize(req_body) if isinstance(req_body, dict) else req_body
                
                # Create context and call the bot logic directly
                context = TurnContext(self, activity)
                
                try:
                    await logic(context)
                    return
                except Exception as logic_error:
                    LOGGER.error(f"Logic error after auth bypass: {str(logic_error)}", exc_info=True)
                    raise logic_error
            else:
                # Re-raise for other exceptions
                LOGGER.error(f"Error in process_activity: {error_message}")
                raise

# Create the custom adapter
ADAPTER = DirectResponseAdapter(SETTINGS)

# Error handler for unhandled exceptions
async def on_error(context: TurnContext, error: Exception):
    LOGGER.error(f"Unhandled error: {str(error)}", exc_info=True)
    
    error_message = "I apologize, but something went wrong. Let's try again."
    
    if isinstance(error, DeserializationError):
        LOGGER.error(f"Deserialization error: {str(error)}")
        error_message = "I'm having trouble processing that. Let's start over."
    elif "Authorization" in str(error):
        LOGGER.error("Authorization error in request")
        error_message = "There was an authentication issue. Let's try again."
    
    # Send a message to the user without going through the Bot Framework
    if hasattr(context, "responded") and context.responded:
        LOGGER.info("Context already has a response, not sending error message")
    else:
        try:
            # Try to send directly without using Bot Framework connector
            await context.send_activity(error_message)
        except Exception as send_error:
            LOGGER.error(f"Failed to send error message: {str(send_error)}")
    
    # Log additional details for debugging
    if context and context.activity:
        if context.activity.from_property:
            LOGGER.error(f"Error occurred for user: {context.activity.from_property.id}")
        if context.activity.conversation:
            LOGGER.error(f"Error occurred in conversation: {context.activity.conversation.id}")
    
ADAPTER.on_turn_error = on_error

# Initialize storage
memory = MemoryStorage()
conversation_state = ConversationState(memory)
user_state_property = BotUserState(memory)

async def health_check(req):
    """Health check endpoint to verify the bot is running."""
    try:
        # Check if critical services are available
        env_vars = ["AI_API_KEY", "AI_ENDPOINT", "TRANSLATOR_KEY", "TRANSLATOR_ENDPOINT"]
        missing = [var for var in env_vars if not os.getenv(var)]
        
        if missing:
            LOGGER.warning(f"Missing environment variables: {', '.join(missing)}")
            return web.json_response({
                "status": "degraded",
                "details": f"Missing configuration: {', '.join(missing)}"
            }, status=200)
        
        return web.json_response({"status": "healthy", "configSource": "Azure App Configuration"}, status=200)
    except Exception as e:
        LOGGER.error(f"Health check failed: {str(e)}")
        return web.json_response({"status": "unhealthy", "error": str(e)}, status=500)

# Extract HTML content for debug purposes
def extract_html_error(html_content):
    """Extract error information from HTML content."""
    error_info = {}
    
    # Try to find title
    title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
    if title_match:
        error_info['title'] = title_match.group(1)
    
    # Try to find h1 or h2
    heading_match = re.search(r'<h1>(.*?)</h1>|<h2>(.*?)</h2>', html_content, re.IGNORECASE)
    if heading_match:
        for group in heading_match.groups():
            if group:
                error_info['heading'] = group
                break
    
    return error_info

async def messages(req):
    """Process incoming messages from users."""
    try:
        body = await req.json()
        user_id = req.headers.get("X-User-ID")

        if not user_id:
            LOGGER.warning("Missing user ID in request")
            return web.json_response(
                {"error": "Missing X-User-ID header", "reply": "Authentication error. Please refresh the page."}, 
                status=401
            )

        # Get the server origin
        origin = f"http://localhost:{os.getenv('PORT', '3978')}"
        
        # Set required activity fields
        body.setdefault('type', 'message')
        body.setdefault('channelId', 'directline')
        body.setdefault('from', {'id': user_id})
        body.setdefault('recipient', {'id': 'bot'})
        body.setdefault('conversation', {'id': f'conversation-{user_id}'})
        body.setdefault('serviceUrl', origin)

        activity = Activity().deserialize(body)
        # For local development, we don't need an auth header
        auth_header = req.headers.get("Authorization", "") if not BYPASS_AUTH else ""

        bot_response = {"text": "", "attachments": []}

        with flask_app.app_context():
            try:
                user_state = UserState(user_id)
                
                # Force reset of active dialog if the message is "__start__" or similar
                if body.get('text', '').lower() == "__start__" or body.get('text', '').lower() == "start":
                    user_state.set_active_dialog(None)
                    user_state.set_new_conversation(True)
                    LOGGER.info(f"Starting new conversation for user {user_id}")
                
                dialog = MainDialog(user_state)
                LOGGER.info(f"Processing message for user {user_id}: '{activity.text}'")
            except Exception as e:
                LOGGER.error(f"Failed to initialize dialog: {str(e)}", exc_info=True)
                return web.json_response(
                    {"error": "Failed to initialize dialog", "reply": "System error. Please try again later."}, 
                    status=500
                )

        async def turn_logic(turn_context: TurnContext):
            # Store the original send_activity method
            original_send_activity = turn_context.send_activity
            
            # Keep track of all responses
            all_responses = []
            
            # Create a wrapper for send_activity to capture the response
            async def capture_send_activity(msg):
                try:
                    if isinstance(msg, str):
                        # Plain text message
                        all_responses.append({"type": "message", "text": msg})
                        bot_response["text"] = msg
                    elif isinstance(msg, Activity):
                        # Handle typing indicator
                        if msg.type == "typing":
                            all_responses.append({"type": "typing"})
                        # Normal text activity
                        elif msg.text:
                            all_responses.append({"type": "message", "text": msg.text})
                            bot_response["text"] = msg.text
                        # Handle attachments if present
                        if msg.attachments:
                            bot_response["attachments"] = [
                                {
                                    "contentType": att.content_type,
                                    "content": att.content
                                }
                                for att in msg.attachments
                            ]
                    else:
                        # Unknown message type, convert to string
                        all_responses.append({"type": "message", "text": str(msg)})
                        bot_response["text"] = str(msg)

                    LOGGER.info(f"Bot response to {user_id}: {str(msg)[:100]}...")
                    
                    # Try to send the message (might fail with deserialization errors)
                    return await original_send_activity(msg)
                except DeserializationError as de:
                    # If we get a deserialization error, just log it and continue
                    LOGGER.error(f"Deserialization error during send_activity: {str(de)}")
                    # We already captured the message in bot_response, so no need to raise
                    return None
                except Exception as e:
                    LOGGER.error(f"Error in send_activity: {str(e)}")
                    if "Authorization" in str(e) and BYPASS_AUTH:
                        LOGGER.info("Bypassing authorization error in send_activity")
                        # We already captured the message in bot_response, so we're good
                        return None
                    # We already captured the message in bot_response, so no need to raise
                    return None

            # Replace the send_activity method with our wrapper
            turn_context.send_activity = capture_send_activity

            try:
                # Run the dialog
                try:
                    dialog_result = await dialog.run(turn_context, conversation_state.create_property("DialogState"))
                    # Handle case where dialog_result is None
                    if dialog_result is None:
                        LOGGER.warning(f"Dialog returned None result for user {user_id}")
                        if not bot_response["text"]:
                            bot_response["text"] = "I'm still processing. Let me think about that."
                except AttributeError as ae:
                    LOGGER.error(f"AttributeError in dialog execution: {str(ae)}", exc_info=True)
                    if "NoneType" in str(ae) and "status" in str(ae):
                        # This is the specific error we're handling
                        LOGGER.info("Handling None dialog result error")
                        bot_response["text"] = "I'm ready to continue our conversation."
                    else:
                        raise ae
                
                await conversation_state.save_changes(turn_context)
                await user_state_property.save_changes(turn_context)
                
            except DeserializationError as de:
                # If we get HTML instead of JSON, this happens
                LOGGER.error(f"Deserialization error: {str(de)}")
                if "text/html" in str(de):
                    LOGGER.error("Received HTML response instead of JSON - this is likely due to a Bot Framework service URL issue")
                
                # Don't rethrow, we'll use the captured bot_response
            except Exception as e:
                LOGGER.error(f"Dialog execution error: {str(e)}", exc_info=True)
                bot_response["text"] = "I apologize, but I encountered an error. Let's try again."

            # After dialog execution, combine all responses
            if all_responses:
                # Join all text messages, preserving order
                combined_text = ""
                for resp in all_responses:
                    if resp["type"] == "message" and resp["text"]:
                        if combined_text:
                            combined_text += "\n\n"
                        combined_text += resp["text"]
                
                # Only update if we have content
                if combined_text:
                    bot_response["text"] = combined_text

        try:
            await ADAPTER.process_activity(activity, auth_header, turn_logic)
        except Exception as process_error:
            LOGGER.error(f"Error processing activity: {str(process_error)}")
            # If this is an auth error and we're bypassing auth, we can handle it specially
            if "Authorization" in str(process_error) and BYPASS_AUTH:
                LOGGER.info("Handling authorization error in process_activity")
                bot_response["text"] = "I'm here to help. What would you like to talk about?"
            # Continue execution - we'll use the captured bot_response if available

        # Provide a fallback response if no text was captured
        if not bot_response["text"]:
            LOGGER.warning(f"No response text captured for user {user_id}")
            bot_response["text"] = "I'm processing your request..."

        return web.json_response({
            "reply": bot_response["text"],
            "attachments": bot_response["attachments"]
        })

    except json.JSONDecodeError:
        LOGGER.error("Invalid JSON in request body")
        return web.json_response({
            "error": "Invalid JSON",
            "reply": "Sorry, I couldn't understand that request. Please try again."
        }, status=400)
    except Exception as e:
        LOGGER.error(f"Message processing error: {str(e)}", exc_info=True)
        return web.json_response({
            "error": "Internal server error",
            "reply": "Sorry, the service is experiencing technical difficulties. Please try again later."
        }, status=500)

# Create and configure the web app
app = web.Application()
app.router.add_get("/health", health_check)
app.router.add_post("/api/messages", messages)

# Only run the server if directly executed
if __name__ == "__main__":
    port = int(os.getenv("PORT", 3978))
    LOGGER.info(f"Starting bot on port {port}")
    
    # Reload config in case environment has changed
    config_loaded = load_azure_app_config()
    LOGGER.info(f"Config loaded from Azure App Configuration: {config_loaded}")
    
    web.run_app(app, host="0.0.0.0", port=port)
