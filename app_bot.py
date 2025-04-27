import sys
import os

# Add the project root directory to Python path to fix import issues
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

import logging
import traceback

# Force output to be unbuffered for real-time visibility
sys.stdout = sys.stderr

print("=== STARTING BOT APPLICATION ===")

# Load environment variables first
try:
    from dotenv import load_dotenv
    print("Loading .env file...")
    load_dotenv()
    print(".env file loaded successfully")
except Exception as e:
    print(f"Error loading .env: {str(e)}")
    traceback.print_exc()

# Configure simple logging to stdout
logging.basicConfig(
    level=logging.getLevelName(os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
logger.info("Logging initialized")

def run_bot():
    try:
        print("Setting up Bot app...")
        
        # Import bot app here to avoid circular imports
        print("Importing bot_app...")
        from backend.bot.bot_app import app as bot_app
        import aiohttp.web
        
        bot_port = int(os.getenv("PORT", "3978"))
        
        print(f"Starting Bot on port {bot_port}...")
        
        # Use the correct method to run an aiohttp application
        aiohttp.web.run_app(bot_app, host="0.0.0.0", port=bot_port)
    except Exception as e:
        print(f"Bot error: {str(e)}")
        traceback.print_exc()

# Run the app
if __name__ == "__main__":
    try:
        print("Starting Bot application...")
        run_bot()
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
        traceback.print_exc()
        sys.exit(1)