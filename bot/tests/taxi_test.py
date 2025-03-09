import pytest
from unittest.mock import MagicMock, AsyncMock
import requests
from botbuilder.core import MemoryStorage, ConversationState, TurnContext
from botbuilder.dialogs import DialogSet, DialogTurnStatus
from botbuilder.dialogs.prompts import TextPrompt
from dialogs.taxi_scenario import TaxiScenarioDialog
from state.user_state import UserState

@pytest.mark.asyncio
async def test_taxi_scenario_flow(monkeypatch):
    # Mock environment variables
    monkeypatch.setenv("AZURE_APP_CONFIG_CONNECTION_STRING", "mock_connection_string")
    monkeypatch.setenv("TRANSLATOR_KEY", "mock_translator_key")
    monkeypatch.setenv("TRANSLATOR_ENDPOINT", "https://mock_translator_endpoint")
    monkeypatch.setenv("TRANSLATOR_LOCATION", "mock_location")
    monkeypatch.setenv("TEXT_ANALYTICS_KEY", "mock_text_analytics_key")
    monkeypatch.setenv("TEXT_ANALYTICS_ENDPOINT", "https://mock_text_analytics_endpoint")

    # Mock the translation request
    def mock_translate_request(url, headers, json):
        return MagicMock(
            status_code=200,
            json=lambda: [{"translations": [{"text": "Bienvenido al escenario de Taxi!"}]}]  # Mock translated text
        )

    monkeypatch.setattr(requests, "post", mock_translate_request)

    # Setup memory and conversation state
    memory = MemoryStorage()
    conversation_state = ConversationState(memory)
    dialog_state = conversation_state.create_property("DialogState")

    # Create UserState instance for testing
    user_state = UserState(user_id="test_user")

    # Create the DialogSet and add dialogs
    dialogs = DialogSet(dialog_state)
    dialogs.add(TextPrompt("text_prompt"))
    dialogs.add(TaxiScenarioDialog(user_state))  # Pass UserState to TaxiScenarioDialog

    # Mock TurnContext
    turn_context = MagicMock(spec=TurnContext)
    turn_context.activity = MagicMock()
    turn_context.activity.type = "message"
    turn_context.activity.locale = "en-us"
    turn_context.turn_state = {"DialogState": dialog_state}  # Ensure consistent dialog state

    # Create DialogContext
    dialog_context = await dialogs.create_context(turn_context)

    # Step 1: Bot sends welcome message and prompts for taxi order
    await dialog_context.begin_dialog("TaxiScenarioDialog")
    assert dialog_context.active_dialog is not None

    # Step 2: User orders a taxi
    turn_context.activity.text = "I would like to order a taxi"
    turn_context.activity.get_property = MagicMock(return_value="I would like to order a taxi")
    await dialog_context.continue_dialog()

    # Step 3: User asks to go to train station
    turn_context.activity.text = "Take me to the train station, please"
    turn_context.activity.get_property = MagicMock(return_value="Take me to the train station, please")
    await dialog_context.continue_dialog()

    # Step 4: User asks for price
    turn_context.activity.text = "How much does the ride cost?"
    turn_context.activity.get_property = MagicMock(return_value="How much does the ride cost?")
    await dialog_context.continue_dialog()

    # Step 5: Scenario completion
    assert dialog_context.active_dialog is None

    # Step 6 Verify final score retrieval
    final_score = user_state.get_final_score()
    assert isinstance(final_score, int), "Final score should be an integer"
    assert final_score >= 0, "Final score should be non-negative"
