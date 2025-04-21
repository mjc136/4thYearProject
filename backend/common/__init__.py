import os
import logging
from flask import Flask, redirect, request, jsonify
from dotenv import load_dotenv
from backend.common.extensions import db, bcrypt
from backend.models import User
from flask_migrate import Migrate

# Load .env variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATE_DIR = os.path.join(BASE_DIR, "flask_app", "templates")

# Get database path from environment variable or use default
# Azure environments typically use /home for persistent storage

# Determine environment
is_azure = os.getenv("WEBSITE_SITE_NAME") is not None

# Use /home in Azure, BASE_DIR locally
default_db_path = os.path.join("/home", "lingolizard.db") if is_azure else os.path.join(BASE_DIR, "lingolizard.db")
DB_PATH = os.getenv("DB_PATH", default_db_path)

logger.info(f"Using database path: {DB_PATH}")

# Init app
app = Flask(__name__, template_folder=TEMPLATE_DIR)

# Config
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))

# Azure App Config fallback
connection_string = os.getenv("AZURE_APP_CONFIG_CONNECTION_STRING")
if connection_string:
    try:
        from azure.appconfiguration import AzureAppConfigurationClient
        client = AzureAppConfigurationClient.from_connection_string(connection_string)
        app.secret_key = client.get_configuration_setting(key="FLASK_SECRET").value
        logger.info("Successfully loaded secret key from Azure App Configuration")
    except Exception as e:
        logger.warning(f"Could not load secret key from Azure: {e}")

# Init extensions
db.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db)

# Create tables & default users
with app.app_context():
    try:
        logger.info("Initializing database...")
        db.create_all()
        
        if not User.query.filter_by(username="admin").first():
            logger.info("Adding admin user")
            db.session.add(User(
                username="admin",
                password=bcrypt.generate_password_hash("adminpass").decode("utf-8"),
                language="english",
                proficiency="beginner",
                xp=0,
                level=1,
                admin=True
            ))

        if not User.query.filter_by(username="testuser").first():
            logger.info("Adding test user")
            db.session.add(User(
                username="testuser",
                password=bcrypt.generate_password_hash("testpass").decode("utf-8"),
                language="spanish",
                proficiency="beginner",
                xp=0,
                level=1,
                admin=False
            ))

        db.session.commit()
        logger.info("Database ready and default users added.")
        logger.info(f"DB path: {DB_PATH}")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        # Don't crash the application, but log the error

@app.route("/")
def index():
    return redirect("/login")

# Add a error handler for bad requests
@app.errorhandler(400)
def handle_bad_request(e):
    """Handle bad request errors with a friendly response."""
    logger.error(f"Bad request error: {str(e)}")
    return jsonify({
        "status": "error",
        "message": "Bad Request: The server could not understand the request.",
        "details": str(e)
    }), 400

# Add a DB-checking health endpoint
@app.route("/db-health")
def db_health():
    try:
        # Validate request parameters if any
        if request.args and not all(k in ['format', 'verbose'] for k in request.args):
            return jsonify({
                "status": "error",
                "message": "Invalid query parameters"
            }), 400
            
        # Test DB connection by querying a user
        with app.app_context():
            user_count = User.query.count()
            return {
                "status": "healthy",
                "database": "connected",
                "users": user_count,
                "db_path": DB_PATH
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "db_path": DB_PATH
        }, 500
