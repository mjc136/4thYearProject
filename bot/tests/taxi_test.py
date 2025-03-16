import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import requests
from botbuilder.core import MemoryStorage, ConversationState, TurnContext
from botbuilder.dialogs import DialogSet
from botbuilder.dialogs.prompts import TextPrompt
from bot.dialogs.taxi_scenario import TaxiScenarioDialog
from bot.state.user_state import UserState

@pytest.mark.asyncio
@patch("bot.dialogs.base_dialog.AzureAppConfigurationClient.from_connection_string")
async def test_taxi_scenario_flow(mock_config_client, monkeypatch):
    
    # Mock Azure App Configuration Client
    mock_config_client.return_value.get_configuration_setting = MagicMock(side_effect=lambda key: MagicMock(value="mock_value"))

    # Mock environment variables
    monkeypatch.setenv("AZURE_APP_CONFIG_CONNECTION_STRING", "mock_connection_string")
    monkeypatch.setenv("TRANSLATOR_KEY", "mock_translator_key")
    monkeypatch.setenv("TRANSLATOR_ENDPOINT", "https://mock_translator_endpoint")
    monkeypatch.setenv("TRANSLATOR_LOCATION", "mock_location")
    monkeypatch.setenv("TEXT_ANALYTICS_KEY", "mock_text_analytics_key")
    monkeypatch.setenv("TEXT_ANALYTICS_ENDPOINT", "https://mock_text_analytics_endpoint")

    # Mock translation request (Spanish response)
    def mock_translate_request(url, headers, json):
        return MagicMock(
            status_code=200,
            json=lambda: [{"translations": [{"text": "Bienvenido al escenario de Taxi!"}]}]
        )

    monkeypatch.setattr(requests, "post", mock_translate_request)

    # Setup memory and conversation state
    memory = MemoryStorage()
    conversation_state = ConversationState(memory)
    dialog_state = conversation_state.create_property("DialogState")

    # Create UserState instance for testing (Spanish language)
    user_state = UserState(user_id="test_user", language="es")

    # Create the DialogSet and add dialogs
    dialogs = DialogSet(dialog_state)
    dialogs.add(TextPrompt("text_prompt"))
    dialogs.add(TaxiScenarioDialog(user_state))

    # Mock TurnContext
    turn_context = MagicMock(spec=TurnContext)
    turn_context.activity = MagicMock()
    turn_context.activity.type = "message"
    turn_context.activity.locale = "es"
    turn_context.turn_state = {"DialogState": dialog_state}

    # Create DialogContext
    dialog_context = await dialogs.create_context(turn_context)

    # Step 1: Bot sends welcome message
    await dialog_context.begin_dialog("TaxiScenarioDialog")
    assert dialog_context.active_dialog is not None

    # Step 2: User provides pickup location
    turn_context.activity.text = "Estoy en el centro comercial"
    turn_context.activity.get_property = MagicMock(return_value="Estoy en el centro comercial")
    await dialog_context.continue_dialog()

    # Step 3: User confirms pickup location and provides destination
    turn_context.activity.text = "Sí, quiero ir a la estación de tren"
    turn_context.activity.get_property = MagicMock(return_value="Sí, quiero ir a la estación de tren")
    await dialog_context.continue_dialog()

    # Step 4: User responds to price suggestion
    turn_context.activity.text = "¿Cuánto costará?"
    turn_context.activity.get_property = MagicMock(return_value="¿Cuánto costará?")
    await dialog_context.continue_dialog()

    # Step 5: User accepts price
    turn_context.activity.text = "Sí, está bien"
    turn_context.activity.get_property = MagicMock(return_value="Sí, está bien")
    await dialog_context.continue_dialog()

    # Step 6: User acknowledges ETA
    turn_context.activity.text = "Gracias, me funciona"
    turn_context.activity.get_property = MagicMock(return_value="Gracias, me funciona")
    await dialog_context.continue_dialog()

    # Step 7: Ensure all dialog steps are completed
    while dialog_context.active_dialog is not None:
        await dialog_context.continue_dialog()

    # Verify scenario completion
    assert dialog_context.active_dialog is None, "Dialog did not complete as expected"

    # Verify final score retrieval
    final_score = user_state.get_final_score()
    assert isinstance(final_score, int), "Final score should be an integer"
    assert final_score >= 0, "Final score should be non-negative"
