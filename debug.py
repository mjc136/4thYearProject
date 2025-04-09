import os
import sys
import traceback

def check_db():
    """Test database connection"""
    try:
        print("Checking database...")
        from common.extensions import db
        from models import User
        from common import app as flask_app
        
        with flask_app.app_context():
            user_count = User.query.count()
            print(f"Database connection successful. Found {user_count} users.")
        return True
    except Exception as e:
        print(f"Database error: {str(e)}")
        traceback.print_exc()
        return False

def check_bot_config():
    """Test bot configuration loading"""
    try:
        print("Checking bot configuration...")
        from dotenv import load_dotenv
        load_dotenv()
        
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
            print(f"Missing environment variables: {', '.join(missing)}")
            return False
        else:
            print("All required environment variables are set.")
            return True
    except Exception as e:
        print(f"Configuration error: {str(e)}")
        traceback.print_exc()
        return False

def check_azure_config():
    """Test Azure App Configuration connection"""
    try:
        print("Checking Azure App Configuration...")
        from bot.bot_app import load_azure_app_config
        
        success = load_azure_app_config()
        if success:
            print("Azure App Configuration loaded successfully.")
        else:
            print("Failed to load from Azure App Configuration.")
        return success
    except Exception as e:
        print(f"Azure App Configuration error: {str(e)}")
        traceback.print_exc()
        return False

def check_bot_imports():
    """Test if all bot imports work correctly"""
    try:
        print("Testing bot imports...")
        # Try importing all necessary bot modules
        from bot.bot_app import app as bot_app
        from bot.dialogs.main_dialog import MainDialog
        from bot.state.user_state import UserState
        
        print("Bot imports successful.")
        return True
    except Exception as e:
        print(f"Bot import error: {str(e)}")
        traceback.print_exc()
        return False

def check_flask_imports():
    """Test if all Flask imports work correctly"""
    try:
        print("Testing Flask imports...")
        from flask_app.flask_app import app as flask_app
        from models import User
        
        print("Flask imports successful.")
        return True
    except Exception as e:
        print(f"Flask import error: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== RUNNING SYSTEM DIAGNOSTICS ===")
    
    # Run tests
    db_ok = check_db()
    flask_imports_ok = check_flask_imports()
    bot_config_ok = check_bot_config()
    bot_imports_ok = check_bot_imports()
    azure_ok = check_azure_config()
    
    # Report results
    print("\n=== DIAGNOSTIC RESULTS ===")
    print(f"Database: {'✓ OK' if db_ok else '✗ FAIL'}")
    print(f"Flask Imports: {'✓ OK' if flask_imports_ok else '✗ FAIL'}")
    print(f"Bot Config: {'✓ OK' if bot_config_ok else '✗ FAIL'}")
    print(f"Bot Imports: {'✓ OK' if bot_imports_ok else '✗ FAIL'}")
    print(f"Azure Config: {'✓ OK' if azure_ok else '✗ FAIL'}")
    
    if all([db_ok, flask_imports_ok, bot_config_ok, bot_imports_ok]):
        print("\nAll core components appear to be functioning properly.")
        print("You can try running the application with 'python backend/main.py'")
    else:
        print("\nSome components are not functioning correctly. Please fix the issues above.")
