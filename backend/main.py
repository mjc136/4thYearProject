import sys
import os

# Add the project root directory to Python path to fix import issues
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

import threading
import logging
import signal
import time
import traceback

# Force output to be unbuffered for real-time visibility
sys.stdout = sys.stderr

print("=== STARTING APPLICATION - INITIALIZATION ===")

# Load environment variables first
try:
    from dotenv import load_dotenv
    print("Loading .env file...")
    load_dotenv()
    print(".env file loaded successfully")
except Exception as e:
    print(f"Error loading .env: {str(e)}")
    traceback.print_exc()

# Global config cache
APP_CONFIG_CACHE = {}

def load_configuration():
    """Load configuration from either Azure App Config or environment variables"""
    global APP_CONFIG_CACHE
    
    # First attempt to load environment variables from file again to ensure they're available
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
    except Exception as e:
        print(f"Warning: Could not load environment variables from .env file: {str(e)}")
    
    # Check if we should use Azure App Config
    use_azure = os.getenv("USE_AZURE_APP_CONFIG", "false").lower() == "true"
    
    if use_azure:
        try:
            print("Loading configuration from Azure App Configuration...")
            from azure.appconfiguration import AzureAppConfigurationClient
            connection_string = os.getenv("AZURE_APP_CONFIG_CONNECTION_STRING")
            
            if not connection_string:
                print("ERROR: AZURE_APP_CONFIG_CONNECTION_STRING environment variable not set")
                print("Falling back to local environment variables...")
                use_azure = False
            else:
                try:
                    client = AzureAppConfigurationClient.from_connection_string(connection_string)
                    
                    # Fetch all settings at once to minimize API calls
                    settings = client.list_configuration_settings()
                    settings_count = 0
                    for setting in settings:
                        APP_CONFIG_CACHE[setting.key] = setting.value
                        # Also set as environment variable for compatibility
                        os.environ[setting.key] = setting.value
                        settings_count += 1
                        
                    print(f"Successfully loaded {settings_count} settings from Azure App Configuration")
                    
                    if settings_count == 0:
                        print("WARNING: No configuration settings were loaded from Azure App Configuration")
                except Exception as azure_error:
                    print(f"ERROR accessing Azure App Configuration: {str(azure_error)}")
                    print("Falling back to local environment variables...")
                    use_azure = False
        except ImportError:
            print("Azure App Configuration SDK not installed. Falling back to local environment variables...")
            print("To use Azure App Config, install with: pip install azure-appconfiguration")
            use_azure = False
        except Exception as e:
            print(f"ERROR loading Azure App Configuration: {str(e)}")
            print("Falling back to local environment variables...")
            use_azure = False
    
    if not use_azure:
        print("Using local environment variables...")
        # Ensure we have at least the basic configuration in APP_CONFIG_CACHE
        for key, value in os.environ.items():
            APP_CONFIG_CACHE[key] = value
    
    # Always check critical env vars regardless of source
    return check_critical_env_vars()

# Configure simple logging to stdout
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
logger.info("Logging initialized")

# Flag to track shutdown
is_shutting_down = False
flask_running = False
bot_running = False

# Check for minimum required environment variables
def check_critical_env_vars():
    """Check for critical environment variables and set defaults if needed."""
    # Minimum required variables with default values
    critical_vars = {
        "AI_API_KEY": os.getenv("AI_API_KEY", ""),  # No default for API keys
        "AI_ENDPOINT": os.getenv("AI_ENDPOINT", "https://api.deepseek.com"),  # Example default
        "TRANSLATOR_KEY": os.getenv("TRANSLATOR_KEY", ""),
        "TRANSLATOR_ENDPOINT": os.getenv("TRANSLATOR_ENDPOINT", "https://api.cognitive.microsofttranslator.com"),
        "TRANSLATOR_LOCATION": os.getenv("TRANSLATOR_LOCATION", "global"),
        "TEXT_ANALYTICS_KEY": os.getenv("TEXT_ANALYTICS_KEY", ""),
        "TEXT_ANALYTICS_ENDPOINT": os.getenv("TEXT_ANALYTICS_ENDPOINT", ""),
    }
    
    missing = []
    for var, value in critical_vars.items():
        if not value:
            missing.append(var)
        else:
            # Make sure the value is set in os.environ
            os.environ[var] = value
    
    if missing:
        print(f"WARNING: Missing critical environment variables: {', '.join(missing)}")
        print("Application may not function correctly without these variables.")
    else:
        print("All critical environment variables are set.")
    
    return len(missing) == 0

def run_flask():
    global flask_running
    print("Setting up Flask app...")
    try:
        # Import flask app here to avoid circular imports
        from backend.flask_app.flask_app import app as flask_app
        port = int(os.getenv("FLASK_PORT", "5000"))
        print(f"Starting Flask on port {port}...")
        
        # Start the Flask app
        flask_running = True
        flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    except Exception as e:
        flask_running = False
        print(f"Flask error: {str(e)}")
        traceback.print_exc()

def run_bot():
    global bot_running
    try:
        print("Setting up Bot app...")
        
        # Check for environment variables
        check_critical_env_vars()
        
        # Import bot app here to avoid circular imports
        print("Importing bot_app...")
        from backend.bot.bot_app import app as bot_app
        import aiohttp.web
        
        # Use a different port if PORT and FLASK_PORT are the same
        bot_port = int(os.getenv("PORT", "3978"))
        flask_port = int(os.getenv("FLASK_PORT", "5000"))
        
        # If ports conflict, use a different port for the bot
        if bot_port == flask_port:
            bot_port = flask_port + 1
            print(f"Port conflict detected. Using port {bot_port} for bot instead.")
        
        print(f"Starting Bot on port {bot_port}...")
        
        bot_running = True
        # Use the correct method to run an aiohttp application
        aiohttp.web.run_app(bot_app, host="0.0.0.0", port=bot_port)
    except Exception as e:
        bot_running = False
        print(f"Bot error: {str(e)}")
        traceback.print_exc()

def start_app():
    print("Starting application with sequential components...")
    
    # Start Flask in a thread
    print("Starting Flask app thread...")
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Wait a moment and then start bot directly
    print("Waiting for Flask to initialize...")
    time.sleep(2)
    
    # Run bot in main thread so we can see errors
    print("Starting Bot application (main thread)...")
    run_bot()

# Run the app
if __name__ == "__main__":
    try:
        print("Starting LingoLizard application...")
        start_app()
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
