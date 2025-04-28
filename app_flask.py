import sys
import os

# Add the project root directory to Python path to fix import issues
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

import logging
import traceback

# Force output to be unbuffered for real-time visibility
sys.stdout = sys.stderr

print("=== STARTING FLASK APPLICATION ===")

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

def run_flask():
    print("Setting up Flask app...")
    try:
        # Import flask app here to avoid circular imports
        from backend.flask_app.flask_app import app as flask_app
        
        port = int(os.getenv("PORT", "5000"))
        print(f"Starting Flask on port {port}...")
        
        # Start the Flask app
        flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask error: {str(e)}")
        traceback.print_exc()

# Run the app
if __name__ == "__main__":
    try:
        print("Starting Flask application...")
        run_flask()
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
        traceback.print_exc()
        sys.exit(1)