import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import requests
from botbuilder.core import MemoryStorage, ConversationState, TurnContext
from botbuilder.dialogs import DialogSet
from botbuilder.dialogs.prompts import TextPrompt
from dialogs.hotel_scenario import HotelScenarioDialog
from state.user_state import UserState
from azure.appconfiguration import AzureAppConfigurationClient

@pytest.mark.asyncio
async def test_hotel_scenario_flow(monkeypatch):
    # 🛠️ Set up mocked environment variables
    monkeypatch.setenv("AZURE_APP_CONFIG_CONNECTION_STRING", "Endpoint=https://mock-config.azconfig.io;Id=mockId;Secret=mockSecret")
    monkeypatch.setenv("TRANSLATOR_KEY", "mock_translator_key")
    monkeypatch.setenv("TRANSLATOR_ENDPOINT", "https://mock_translator_endpoint")
    monkeypatch.setenv("TRANSLATOR_LOCATION", "mock_location")
    monkeypatch.setenv("TEXT_ANALYTICS_KEY", "mock_text_analytics_key")
    monkeypatch.setenv("TEXT_ANALYTICS_ENDPOINT", "https://mock_text_analytics_endpoint")

    # 🛠️ Mock Azure App Configuration and Translation API
    with patch.object(AzureAppConfigurationClient, "from_connection_string") as mock_config_client, \
         patch.object(requests, "post") as mock_requests_post:

        mock_config_instance = MagicMock()

        # Mock `get_configuration_setting()` to return fake values
        def mock_get_config(key):
            fake_config = {
                "TRANSLATOR_KEY": MagicMock(value="mock_translator_key"),
                "TRANSLATOR_ENDPOINT": MagicMock(value="https://mock_translator_endpoint"),
                "TRANSLATOR_LOCATION": MagicMock(value="mock_location"),
                "TEXT_ANALYTICS_KEY": MagicMock(value="mock_text_analytics_key"),
                "TEXT_ANALYTICS_ENDPOINT": MagicMock(value="https://mock_text_analytics_endpoint"),
            }
            return fake_config.get(key, MagicMock(value=""))

        mock_config_instance.get_configuration_setting.side_effect = mock_get_config
        mock_config_client.return_value = mock_config_instance

        # ✅ Mock translation API request
        def mock_translate_request(url, headers, json):
            return MagicMock(
                status_code=200,
                json=lambda: [{"translations": [{"text": "Bienvenido al escenario de Reservación de Hotel!"}]}]
            )

        mock_requests_post.side_effect = mock_translate_request

        # ✅ Set up memory and conversation state
        memory = MemoryStorage()
        conversation_state = ConversationState(memory)
        dialog_state = conversation_state.create_property("DialogState")

        # ✅ Create UserState instance for testing
        user_state = UserState(user_id="test_user")

        # ✅ Create the DialogSet and add dialogs
        dialogs = DialogSet(dialog_state)
        dialogs.add(TextPrompt("text_prompt"))
        dialogs.add(HotelScenarioDialog(user_state))  # Pass UserState to HotelScenarioDialog

        # ✅ Mock TurnContext
        turn_context = AsyncMock(spec=TurnContext)
        turn_context.activity = MagicMock()
        turn_context.activity.type = "message"
        turn_context.activity.locale = "en-us"
        turn_context.turn_state = {"DialogState": dialog_state}  # Ensure consistent dialog state

        # ✅ Create DialogContext
        dialog_context = await dialogs.create_context(turn_context)

        # Step 1: Bot sends welcome message and prompts for hotel booking
        await dialog_context.begin_dialog("HotelScenarioDialog")
        assert dialog_context.active_dialog is not None

        # Step 2: User books a room
        turn_context.activity.text = "I would like to book a room"
        await dialog_context.continue_dialog()

        # Step 3: User provides check-in date
        turn_context.activity.text = "I would like to check in on [date]"
        await dialog_context.continue_dialog()

        # Step 4: User provides check-out date
        turn_context.activity.text = "I would like to check out on [date]"
        await dialog_context.continue_dialog()

        # Step 5: User selects room type
        turn_context.activity.text = "I would like a single/double room"
        await dialog_context.continue_dialog()

        # Step 6: User asks about amenities
        turn_context.activity.text = "Do you have free Wi-Fi and breakfast included?"
        await dialog_context.continue_dialog()

        # Step 7: Scenario completion
        assert dialog_context.active_dialog is None, "Expected the dialog to complete, but it's still active"

        # Step 8: Verify final score retrieval
        final_score = user_state.get_final_score()
        assert isinstance(final_score, int), "Final score should be an integer"
        assert final_score >= 0, "Final score should be non-negative"
