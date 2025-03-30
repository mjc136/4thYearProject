from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///lingolizard.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Load secret key from Azure App Configuration or fallback to .env or random
connection_string = os.getenv("AZURE_APP_CONFIG_CONNECTION_STRING")
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))

if connection_string:
    try:
        from azure.appconfiguration import AzureAppConfigurationClient
        client = AzureAppConfigurationClient.from_connection_string(connection_string)
        app.secret_key = client.get_configuration_setting(key="FLASK_SECRET").value
    except Exception as e:
        print(f"Warning: Could not load secret key from Azure App Config: {e}")

# Init shared extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

with app.app_context():
    db.create_all()