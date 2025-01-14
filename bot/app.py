from aiohttp import web
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
    MemoryStorage,
    ConversationState,
)
from botbuilder.dialogs import DialogSet
from botbuilder.dialogs.prompts import TextPrompt
from botbuilder.schema import Activity, ActivityTypes
from dialogs.taxi_scenario import TaxiScenarioDialog
from dialogs.hotel_scenario import HotelScenarioDialog
from dialogs.main_dialog import MainDialog
from nlu.recogniser import recognise_intent_and_entities

# Adapter settings
SETTINGS = BotFrameworkAdapterSettings(app_id="", app_password="")
ADAPTER = BotFrameworkAdapter(SETTINGS)

# State and dialog setup
memory = MemoryStorage()
conversation_state = ConversationState(memory)
dialog_state = conversation_state.create_property("DialogState")
dialogs = DialogSet(dialog_state)

# Add dialogs
dialogs = DialogSet(dialog_state)
dialogs.add(TextPrompt("text_prompt"))
dialogs.add(MainDialog())
dialogs.add(TaxiScenarioDialog())
dialogs.add(HotelScenarioDialog())

# Bot message handler
async def messages(req: web.Request) -> web.Response:
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    async def turn_logic(turn_context: TurnContext):
        # Create a dialog context
        dialog_context = await dialogs.create_context(turn_context)

        if activity.type == ActivityTypes.conversation_update:
            if activity.members_added:
                for member in activity.members_added:
                    if member.id != activity.recipient.id:
                        await turn_context.send_activity("Welcome to the bot!")
                        await dialog_context.begin_dialog("main_dialog")
        else:
            # Check for active dialog
            if dialog_context.active_dialog:
                # Continue the active dialog
                await dialog_context.continue_dialog()
            else:
                # Start the MainDialog when no active dialog exists
                await dialog_context.begin_dialog("main_dialog")

            await conversation_state.save_changes(turn_context)

            # Recognize intent and entities only if no active dialog
            if not dialog_context.active_dialog:
                user_message = turn_context.activity.text
                intent, entities = recognise_intent_and_entities(user_message)

                if intent == "beginner":
                    await turn_context.send_activity("You selected beginner proficiency.")
                elif intent == "intermediate":
                    await turn_context.send_activity("You selected intermediate proficiency.")
                elif intent == "advanced":
                    await turn_context.send_activity("You selected advanced proficiency.")
                else:
                    await turn_context.send_activity("Sorry, I didn't understand that.")

                # Save state changes
                await conversation_state.save_changes(turn_context)

    await ADAPTER.process_activity(activity, auth_header, turn_logic)
    return web.Response()

# Create and run the web app
APP = web.Application()
APP.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    web.run_app(APP, port=3978)
