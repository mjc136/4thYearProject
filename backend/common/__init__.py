import os
from flask import Flask, redirect
from dotenv import load_dotenv
from common.extensions import db, bcrypt
from models import User


# Load .env variables
load_dotenv()

# Define template directory (for Flask to find login.html, etc.)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATE_DIR = os.path.join(BASE_DIR, "flask_app", "templates")

# Initialise the Flask app
app = Flask(__name__, template_folder=TEMPLATE_DIR)

# Base configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(basedir, '..', 'lingolizard.db')}"
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

from flask_migrate import Migrate
from models import User

migrate = Migrate(app, db)

# Auto-create tables and default users
with app.app_context():
    db.create_all()

    if not User.query.filter_by(username="admin").first():
        admin_user = User(
            username="admin",
            password=bcrypt.generate_password_hash("adminpass").decode("utf-8"),
            language="english",
            proficiency="beginner",
            xp=0,
            level=1,
            admin=True
        )
        db.session.add(admin_user)

    if not User.query.filter_by(username="testuser").first():
        regular_user = User(
            username="testuser",
            password=bcrypt.generate_password_hash("testpass").decode("utf-8"),
            language="spanish",
            proficiency="beginner",
            xp=0,
            level=1,
            admin=False
        )
        db.session.add(regular_user)

    db.session.commit()
    print("[INFO] Database ready and default users added.")

    db_path = os.path.join(basedir, '..', 'lingolizard.db')
    print("[DEBUG] DB path:", os.path.abspath(db_path))
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"


# Default redirect from `/` → `/login`
@app.route("/")
def index():
    return redirect("/login")
