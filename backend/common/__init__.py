import os
import logging
from flask import Flask, redirect, request, jsonify
from dotenv import load_dotenv
from backend.common.extensions import db, bcrypt
from flask_migrate import Migrate

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Determine environment
is_azure = os.getenv("WEBSITE_SITE_NAME") is not None

# Define paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATE_DIR = os.path.join(BASE_DIR, "flask_app", "templates")

# Detect where to store SQLite DB if no DATABASE_URL is provided
if is_azure:
    storage_path = "/tmp/lingolizard_data"
else:
    storage_path = BASE_DIR

default_db_path = os.path.join(storage_path, "lingolizard.db")
DB_PATH = os.getenv("DB_PATH", default_db_path)

# Only create local storage if using SQLite
if "postgresql" not in os.getenv("DATABASE_URL", ""):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

logger.info(f"Using database path: {DB_PATH}")

# Initialise Flask app
app = Flask(__name__, template_folder=TEMPLATE_DIR)

# Flask config
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

# Initialise DB and users
with app.app_context():
    try:
        db.create_all()
        from backend.models import User
        user_count = User.query.count()

        if user_count == 0:
            logger.info("Database exists but has no users. Creating default users...")

            if not User.query.filter_by(username="admin").first():
                db.session.add(User(
                    username="admin",
                    password=bcrypt.generate_password_hash("adminpass").decode("utf-8"),
                    language="english",
                    xp=0,
                    level=1,
                    admin=True
                ))

            if not User.query.filter_by(username="testuser").first():
                db.session.add(User(
                    username="testuser",
                    password=bcrypt.generate_password_hash("testpass").decode("utf-8"),
                    language="spanish",
                    xp=0,
                    level=1,
                    admin=False
                ))

            db.session.commit()
            logger.info(f"Created default users. Now have {User.query.count()} users.")
        else:
            logger.info(f"Database already has {user_count} users. Skipping default user creation.")

    except Exception as e:
        logger.error(f"Database initialization error: {e}", exc_info=True)
        logger.error(f"Current directory: {os.getcwd()}")
        logger.error(f"DB path: {DB_PATH}")
        logger.error(f"Directory writable: {os.access(os.path.dirname(DB_PATH), os.W_OK)}")

# Root route
@app.route("/")
def index():
    return redirect("/login")

# Handle 400 errors gracefully
@app.errorhandler(400)
def handle_bad_request(e):
    logger.error(f"Bad request error: {str(e)}")
    return jsonify({
        "status": "error",
        "message": "Bad Request: The server could not understand the request.",
        "details": str(e)
    }), 400

# DB health check
@app.route("/db-health")
def db_health():
    try:
        if request.args and not all(k in ['format', 'verbose'] for k in request.args):
            return jsonify({
                "status": "error",
                "message": "Invalid query parameters"
            }), 400

        from backend.models import User
        user_count = User.query.count()
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "users": user_count,
            "db_path": DB_PATH
        })
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "db_path": DB_PATH
        }), 500
