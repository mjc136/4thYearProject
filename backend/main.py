import threading
import os
from backend.flask_app.flask_app import app as flask_app
from backend.bot.bot_app import app as bot_app
from aiohttp import web

def run_flask():
    flask_app.run(host="0.0.0.0", port=5000, debug=False)

def run_bot():
    port = int(os.getenv("PORT", 3978))
    web.run_app(bot_app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    run_bot()
