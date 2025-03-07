from unittest.mock import MagicMock, patch
import pytest
from botbuilder.core import MemoryStorage, ConversationState, TurnContext
from botbuilder.dialogs import DialogSet
from botbuilder.dialogs.prompts import TextPrompt
from bot.dialogs.main_dialog import MainDialog
from bot.state.user_state import UserState
from azure.appconfiguration import AzureAppConfigurationClient
import requests

@pytest.mark.asyncio
async def test_conversation_flow(monkeypatch):
    # Set a correctly formatted mock connection string
    monkeypatch.setenv("AZURE_APP_CONFIG_CONNECTION_STRING", "Endpoint=https://mock-config.azconfig.io;Id=mockId;Secret=mockSecret")
    monkeypatch.setenv("TRANSLATOR_KEY", "mock_translator_key")
    monkeypatch.setenv("TRANSLATOR_ENDPOINT", "https://mock_translator_endpoint")
    monkeypatch.setenv("TRANSLATOR_LOCATION", "mock_location")
    monkeypatch.setenv("TEXT_ANALYTICS_KEY", "mock_text_analytics_key")
    monkeypatch.setenv("TEXT_ANALYTICS_ENDPOINT", "https://mock_text_analytics_endpoint")

    # Mock Azure App Configuration client
    with patch.object(AzureAppConfigurationClient, "from_connection_string") as mock_client, \
         patch.object(requests, "post") as mock_requests_post:

        mock_instance = MagicMock()

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

        mock_instance.get_configuration_setting.side_effect = mock_get_config
        mock_client.return_value = mock_instance

        # Mock translation API request
        def mock_translate_request(url, headers, json):
            return MagicMock(
                status_code=200,
                json=lambda: [{"translations": [{"text": "Bienvenido al escenario de Taxi!"}]}]  # Mock translated text
            )

        mock_requests_post.side_effect = mock_translate_request

        # Import application code after setting environment variables
        from bot.dialogs.main_dialog import MainDialog
        from bot.state.user_state import UserState
        from botbuilder.core import MemoryStorage, ConversationState, TurnContext
        from botbuilder.dialogs import DialogSet
        from botbuilder.dialogs.prompts import TextPrompt

        # Setup memory and conversation state
        memory = MemoryStorage()
        conversation_state = ConversationState(memory)
        dialog_state = conversation_state.create_property("DialogState")

        # Create UserState instance for testing
        user_state = UserState(user_id="test_user")

        # Create the DialogSet and add dialogs
        dialogs = DialogSet(dialog_state)
        dialogs.add(TextPrompt("text_prompt"))
        dialogs.add(MainDialog(user_state))  # Pass UserState to MainDialog

        # Mock TurnContext
        turn_context = MagicMock(spec=TurnContext)
        turn_context.activity = MagicMock()
        turn_context.activity.type = "message"
        turn_context.activity.locale = "en-us"
        turn_context.turn_state = {"DialogState": dialog_state}  # Ensure consistent dialog state

        # Create DialogContext
        dialog_context = await dialogs.create_context(turn_context)

        # Step 1: Bot sends welcome message and prompts for language
        await dialog_context.begin_dialog("MainDialog")
        assert dialog_context.active_dialog is not None

        # Step 2: User selects language
        turn_context.activity.text = "Es"  # User inputs "Es"
        turn_context.activity.get_property = MagicMock(return_value="Es")  # Ensure user input is read
        await dialog_context.continue_dialog()
        assert user_state.language == "Es", f"Expected 'Es', but got {user_state.language}"

        # Step 3: User selects proficiency level
        turn_context.activity.text = "Beginner"  # User inputs "Beginner"
        turn_context.activity.get_property = MagicMock(return_value="Beginner")
        await dialog_context.continue_dialog()
        assert user_state.proficiency_level == "Beginner", f"Expected 'Beginner', but got {user_state.proficiency_level}"
