import os
from flask import Flask
from dotenv import load_dotenv
from common.extensions import db, bcrypt

# Load .env variables
load_dotenv()

# Define template directory (for Flask to find login.html, etc.)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATE_DIR = os.path.join(BASE_DIR, "flask_app", "templates")

# Initialise the Flask app
app = Flask(__name__, template_folder=TEMPLATE_DIR)

# Base configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///lingolizard.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Secret key (from Azure or fallback)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))

connection_string = os.getenv("AZURE_APP_CONFIG_CONNECTION_STRING")
if connection_string:
    try:
        from azure.appconfiguration import AzureAppConfigurationClient
        client = AzureAppConfigurationClient.from_connection_string(connection_string)
        app.secret_key = client.get_configuration_setting(key="FLASK_SECRET").value
    except Exception as e:
        print(f"[WARNING] Could not load secret key from Azure: {e}")

# Initialise extensions with app
db.init_app(app)
bcrypt.init_app(app)

# Auto-create tables if they don’t exist
with app.app_context():
    db.create_all()
