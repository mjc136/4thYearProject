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
@patch("bot.dialogs.base_dialog.OpenAI")

async def test_conversation_flow(mock_openai, monkeypatch):
    # Mock OpenAI response to prevent connection errors
    mock_openai.return_value.choices = [MagicMock(message=MagicMock(content="Mock AI Response"))]

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
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise requests.exceptions.HTTPError(f"HTTP {self.status_code} Error")

        def mock_translate_request(url, headers, json):
            return MockResponse([{"translations": [{"text": "Bienvenido al escenario de Taxi!"}]}], 200)

        mock_requests_post.side_effect = mock_translate_request

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

        # Define test conversation steps
        test_steps = [
            "es",  # User selects language
            "Beginner",  # User selects proficiency level
        ]

        # Simulate user responses
        for step in test_steps:
            turn_context.activity.text = step
            turn_context.activity.get_property = MagicMock(return_value=step)
            await dialog_context.continue_dialog()

        # Ensure conversation exits properly
        max_turns = 10
        while dialog_context.active_dialog is not None and max_turns > 0:
            await dialog_context.continue_dialog()
            max_turns -= 1

        assert dialog_context.active_dialog is None, "Dialog did not complete as expected"

        # Verify final language selection
        assert user_state.language == "es", f"Expected 'es', but got {user_state.language}"

        # Verify final proficiency selection
        assert user_state.proficiency_level == "beginner", f"Expected 'beginner', but got {user_state.proficiency_level}"
