import os
import logging
from flask import Flask, redirect
from dotenv import load_dotenv
from flask_migrate import Migrate

# Configure logging first to capture all startup issues
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Load env variables
load_dotenv()

# Set up Flask app
from backend.common.extensions import db, bcrypt, csrf
from backend.flask_app.routes.auth import auth_bp
from backend.flask_app.routes.user import user_bp
from backend.flask_app.routes.admin import admin_bp
from backend.flask_app.routes.api import api_bp
from backend.flask_app.routes.health import health_bp

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "flask_app", "static"),
    static_url_path="/static",
    template_folder=os.path.join(BASE_DIR, "flask_app", "templates")
)

# Config
# Use Azure's persistent storage location for SQLite
# On Azure App Service, use /home directory for persistence
is_azure = os.getenv("WEBSITE_SITE_NAME") is not None
default_db_dir = "/home" if is_azure else BASE_DIR
db_path = os.path.join(default_db_dir, os.getenv("DB_FILENAME", "lingolizard.db"))

# Allow override with DATABASE_URL environment variable for flexibility
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Add session cookie security settings
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("ENVIRONMENT") == "production"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # Session lifetime in seconds (24 hours)

# Secret key configuration - critical for sessions to work
stored_key = os.getenv("SECRET_KEY")
if not stored_key:
    LOGGER.warning("SECRET_KEY not found in environment. Using a temporary key.")
    # Store a consistent key for this app instance, don't regenerate on every request
    app.secret_key = os.urandom(24)
else:
    LOGGER.info("Using SECRET_KEY from environment variables")
    app.secret_key = stored_key

# Log the database location for debugging
LOGGER.info(f"Using database at: {db_path}")
LOGGER.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

# Init Flask extensions
db.init_app(app)
bcrypt.init_app(app)
csrf.init_app(app)
migrate = Migrate(app, db)  # Add migration support

# Initialize database if necessary
with app.app_context():
    try:
        # Import models here to ensure they're registered with SQLAlchemy
        from backend.models import User
        
        LOGGER.info("Checking database tables...")
        # Check for required fields in User model
        if not hasattr(User, 'completed_scenarios'):
            LOGGER.warning("User model doesn't have completed_scenarios attribute! This will cause template errors.")
        
        # Only create tables if they don't exist (safer approach)
        db.create_all()
        LOGGER.info("Database tables verified.")
    except Exception as e:
        LOGGER.error(f"Database initialization error: {e}")
        LOGGER.error("This could cause login issues!")

# Register Flask routes
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp)
app.register_blueprint(health_bp)

@app.route("/")
def index():
    return redirect("/login")

# The Bot-related code has been removed since it's now handled by app_bot.py
# and running in a separate Azure App Service

# Only this single-process run block remains
if __name__ == "__main__":
    flask_port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(host="0.0.0.0", port=flask_port)
