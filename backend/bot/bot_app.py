import sys
import os
import logging
from aiohttp import web
from dotenv import load_dotenv
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
    MemoryStorage,
    ConversationState,
    UserState as BotUserState,
)
from botbuilder.schema import Activity
from bot.dialogs.main_dialog import MainDialog
from bot.state.user_state import UserState
from common import app as flask_app

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Load Azure config if available
load_dotenv()
APP_ID = os.getenv("MicrosoftAppId")
APP_PASSWORD = os.getenv("MicrosoftAppPassword")

SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)

async def on_error(context: TurnContext, error: Exception):
    LOGGER.error(f"Unhandled error: {str(error)}", exc_info=True)
    await context.send_activity("Sorry, something went wrong.")

ADAPTER.on_turn_error = on_error

memory = MemoryStorage()
conversation_state = ConversationState(memory)
user_state_property = BotUserState(memory)

async def health_check(req):
    return web.Response(text="Healthy")

async def messages(req):
    try:
        body = await req.json()
        user_id = req.headers.get("X-User-ID")

        if not user_id:
            return web.Response(status=401, text="Missing X-User-ID header")

        # # Ensure required activity properties
        # if 'type' not in body:
        #     body['type'] = 'message'
        # if 'channelId' not in body:
        #     body['channelId'] = 'web'
        # if 'from' not in body:
        #     body['from'] = {'id': user_id}
        # if 'recipient' not in body:
        #     body['recipient'] = {'id': 'bot'}
        # if 'conversation' not in body:
        #     body['conversation'] = {'id': f'web-{user_id}'}
        # if 'serviceUrl' not in body:
        #     body['serviceUrl'] = 'http://localhost'

        activity = Activity().deserialize(body)
        auth_header = req.headers.get("Authorization", "")

        bot_response = {"text": "", "attachments": []}

        with flask_app.app_context():
            user_state = UserState(user_id)
            dialog = MainDialog(user_state)

        async def turn_logic(turn_context: TurnContext):
            from botbuilder.schema import Activity

            async def capture_send_activity(msg):
                if isinstance(msg, str):
                    bot_response["text"] = msg
                elif isinstance(msg, Activity):
                    bot_response["text"] = msg.text or ""
                    if msg.attachments:
                        bot_response["attachments"] = [
                            {
                                "contentType": att.content_type,
                                "content": att.content
                            }
                            for att in msg.attachments
                        ]
                else:
                    bot_response["text"] = str(msg)

                LOGGER.info(f"Bot said: {bot_response['text']}")

            turn_context.send_activity = capture_send_activity

            await dialog.run(turn_context, conversation_state.create_property("DialogState"))
            await conversation_state.save_changes(turn_context)
            await user_state_property.save_changes(turn_context)

        await ADAPTER.process_activity(activity, auth_header, turn_logic)

        return web.json_response({
            "bot_reply": bot_response["text"],
            "attachments": bot_response["attachments"]
        })

    except Exception as e:
        LOGGER.error(f"Message error: {e}", exc_info=True)
        return web.Response(status=500, text="Internal Server Error")

APP = web.Application()
APP.router.add_get("/health", health_check)
APP.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3978))
    LOGGER.info(f"Starting bot on port {port}")
    web.run_app(APP, host="0.0.0.0", port=port)
