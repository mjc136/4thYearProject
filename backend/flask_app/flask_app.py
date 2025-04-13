import os
import threading
import logging
from flask import Flask, redirect
from aiohttp import web
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Set up Flask app
from backend.common.extensions import db, bcrypt
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
db_path = os.path.join(BASE_DIR, "lingolizard.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))

# Init Flask extensions
db.init_app(app)
bcrypt.init_app(app)

# Register Flask routes
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp)
app.register_blueprint(health_bp)

@app.route("/")
def index():
    return redirect("/login")

# Logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Setup aiohttp Bot Framework
from botbuilder.core import (
    BotFrameworkAdapter, BotFrameworkAdapterSettings,
    TurnContext, MemoryStorage, ConversationState, UserState as BotUserState
)
from botbuilder.schema import Activity
from backend.bot.dialogs.main_dialog import MainDialog
from backend.bot.state.user_state import UserState

APP_ID = os.getenv("MicrosoftAppId")
APP_PASSWORD = os.getenv("MicrosoftAppPassword")

SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)

memory = MemoryStorage()
conversation_state = ConversationState(memory)
user_state_property = BotUserState(memory)

async def on_error(context: TurnContext, error: Exception):
    LOGGER.error(f"Unhandled bot error: {error}")
    await context.send_activity("Sorry, something went wrong.")
ADAPTER.on_turn_error = on_error

# aiohttp handlers
aio_app = web.Application()

async def messages(req):
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    user_id = req.headers.get("X-User-ID", "unknown")

    bot_response = {"text": "", "attachments": []}

    with app.app_context():
        user_state = UserState(user_id)
        dialog = MainDialog(user_state)

    async def turn_logic(turn_context: TurnContext):
        async def capture_send_activity(msg):
            bot_response["text"] = msg.text if isinstance(msg, Activity) else str(msg)
        turn_context.send_activity = capture_send_activity
        await dialog.run(turn_context, conversation_state.create_property("DialogState"))
        await conversation_state.save_changes(turn_context)
        await user_state_property.save_changes(turn_context)

    await ADAPTER.process_activity(activity, auth_header, turn_logic)
    return web.json_response({"bot_reply": bot_response["text"]})

aio_app.router.add_post("/api/messages", messages)

# Run Flask + Bot
if __name__ == "__main__":
    port = int(os.getenv("PORT", 3978))
    flask_port = int(os.getenv("FLASK_PORT", 5000))

    def run_flask():
        app.run(host="0.0.0.0", port=flask_port)

    def run_bot():
        LOGGER.info(f"Starting bot on port {port}")
        web.run_app(aio_app, host="0.0.0.0", port=port)

    threading.Thread(target=run_flask).start()
    run_bot()
