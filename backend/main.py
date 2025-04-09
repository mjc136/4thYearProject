import threading
import os
import sys
import logging
import signal
import time
import requests
from flask_app.flask_app import app as flask_app
from bot.bot_app import app as bot_app, load_azure_app_config
from aiohttp import web
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.getLevelName(os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Flag to track if we're shutting down
is_shutting_down = False
flask_thread = None
bot_running = False
flask_running = False

def load_config_from_azure():
    """Load configuration from Azure App Configuration."""
    logger.info("Loading configuration from Azure App Configuration...")
    success = load_azure_app_config()
    if success:
        logger.info("Successfully loaded configuration from Azure App Configuration")
    else:
        logger.warning("Failed to load configuration from Azure App Configuration. Using local environment variables.")
    
    # Check key environment variables after loading from Azure
    check_environment_variables()

def check_environment_variables():
    """Check for required environment variables and warn if any are missing."""
    required_vars = [
        "AI_API_KEY", "AI_ENDPOINT", 
        "TRANSLATOR_KEY", "TRANSLATOR_ENDPOINT", "TRANSLATOR_LOCATION", 
        "TEXT_ANALYTICS_KEY", "TEXT_ANALYTICS_ENDPOINT"
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.warning(f"WARNING: The following environment variables are missing: {', '.join(missing)}")
        logger.warning("This may cause errors in the application.")
    else:
        logger.info("All required environment variables are set.")
    
    return missing

def run_flask():
    global flask_running
    try:
        port = int(os.getenv("FLASK_PORT", "5000"))
        logger.info(f"Starting Flask application on port {port}")
        flask_running = True
        flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    except Exception as e:
        flask_running = False
        logger.error(f"Error in Flask application: {str(e)}")
        if not is_shutting_down:
            os._exit(1)  # Force exit if Flask fails to start (unless we're shutting down)

def run_bot():
    global bot_running
    try:
        port = int(os.getenv("PORT", 3978))
        logger.info(f"Starting Bot application on port {port}")
        
        # Add additional routes if needed
        bot_running = True
        web.run_app(bot_app, host="0.0.0.0", port=port, print=logger.info)
    except Exception as e:
        bot_running = False
        logger.error(f"Error in Bot application: {str(e)}")
        if not is_shutting_down:
            os._exit(1)  # Force exit if bot fails to start (unless we're shutting down)

def check_services():
    """Check if the services are operational after startup."""
    time.sleep(5)  # Give services time to start
    
    services_ok = True
    
    # Check Flask app
    try:
        if not flask_running:
            logger.error("Flask application failed to start")
            services_ok = False
        else:
            logger.info("Flask application is running")
    except Exception as e:
        logger.error(f"Error checking Flask service: {str(e)}")
        services_ok = False
    
    # Check Bot app
    try:
        if not bot_running:
            logger.error("Bot application failed to start")
            services_ok = False
        else:
            try:
                response = requests.get(f"http://localhost:{os.getenv('PORT', '3978')}/health", timeout=5)
                if response.status_code == 200:
                    logger.info("Bot application is running and healthy")
                    # Log the details from the health check
                    try:
                        health_data = response.json()
                        logger.info(f"Health check details: {health_data}")
                    except:
                        pass
                else:
                    logger.warning(f"Bot application health check returned status {response.status_code}")
                    services_ok = False
            except requests.exceptions.RequestException as req_err:
                logger.warning(f"Bot health endpoint not available: {req_err}")
                # Don't mark services as failed - the endpoint might just not exist yet
                logger.info("Bot application is running but health check failed")
    except Exception as e:
        logger.error(f"Error checking Bot service: {str(e)}")
        services_ok = False
    
    return services_ok

def graceful_shutdown(sig, frame):
    global is_shutting_down
    logger.info("Received shutdown signal, shutting down gracefully...")
    is_shutting_down = True
    
    # Give the services a moment to complete any pending requests
    time.sleep(1)
    
    # Exit the process
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    
    try:
        logger.info("Starting LingoLizard application")
        
        # First load configuration from Azure App Configuration
        load_config_from_azure()
        
        # Start the Flask application in a thread
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True  # Make thread exit when main thread exits
        flask_thread.start()
        
        # Wait a moment to ensure Flask is starting up
        time.sleep(2)
        
        # Run the service health check in a separate thread
        health_check_thread = threading.Thread(target=check_services)
        health_check_thread.daemon = True
        health_check_thread.start()
        
        # Run the bot application in the main thread
        run_bot()
    except Exception as e:
        logger.critical(f"Fatal error in main process: {str(e)}")
        sys.exit(1)
