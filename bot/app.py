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
from botbuilder.schema import Activity
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

        # Check for active dialog
        if dialog_context.active_dialog:
            results = await dialog_context.continue_dialog()
            if results.status == "Complete":
                await turn_context.send_activity("Scenario complete!")
        else:
            # Process NLU for intent recognition
            user_message = turn_context.activity.text

            if not user_message:
                await turn_context.send_activity("Sorry, I didn't catch that. Could you please repeat?")
                return

            intent, entities = recognise_intent_and_entities(user_message)

            if intent == "select_taxi_scenario":
                await turn_context.send_activity("Starting Taxi Scenario...")
                await dialog_context.begin_dialog("taxi_dialog")
            elif intent == "select_hotel_scenario":
                await turn_context.send_activity("Starting Hotel Scenario...")
                await dialog_context.begin_dialog("hotel_dialog")
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
