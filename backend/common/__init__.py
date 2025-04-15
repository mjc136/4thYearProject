import os
from flask import Flask, redirect
from dotenv import load_dotenv
from backend.common.extensions import db, bcrypt
from backend.models import User
from flask_migrate import Migrate

# Load .env variables
load_dotenv()

# Setup paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATE_DIR = os.path.join(BASE_DIR, "flask_app", "templates")
SQLITE_PATH = os.path.join("/home", "lingolizard.db")

# Init app
app = Flask(__name__, template_folder=TEMPLATE_DIR)

# Config
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{SQLITE_PATH}"
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
    except Exception as e:
        print(f"[WARNING] Could not load secret key from Azure: {e}")

# Init extensions
db.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db)

# Create tables & default users
with app.app_context():
    db.create_all()

    if not User.query.filter_by(username="admin").first():
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
    print("[INFO] Database ready and default users added.")
    print("[DEBUG] DB path:", SQLITE_PATH)

@app.route("/")
def index():
    return redirect("/login")
