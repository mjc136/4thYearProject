import pytest
from unittest.mock import MagicMock, patch
import requests
from botbuilder.core import MemoryStorage, ConversationState, TurnContext
from botbuilder.dialogs import DialogSet
from botbuilder.dialogs.prompts import TextPrompt
from bot.dialogs.hotel_scenario import HotelScenarioDialog  # Ensure correct import
from bot.state.user_state import UserState

@pytest.mark.asyncio
@patch("bot.dialogs.base_dialog.AzureAppConfigurationClient.from_connection_string")
@patch("bot.dialogs.base_dialog.OpenAI")  # Mock OpenAI
async def test_hotel_scenario_flow(mock_openai, mock_config_client, monkeypatch):
    """
    Test flow for the HotelScenarioDialog.
    """

    # Mock OpenAI API response
    mock_openai_instance = MagicMock()
    mock_openai_instance.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="Réponse IA simulée"))
    ]
    mock_openai.return_value = mock_openai_instance

    # Mock Azure App Configuration Client
    mock_config_client.return_value.get_configuration_setting = MagicMock(
        side_effect=lambda key: MagicMock(value="mock_value")
    )

    # Mock environment variables
    monkeypatch.setenv("AZURE_APP_CONFIG_CONNECTION_STRING", "mock_connection_string")
    monkeypatch.setenv("TRANSLATOR_KEY", "mock_translator_key")
    monkeypatch.setenv("TRANSLATOR_ENDPOINT", "https://mock_translator_endpoint")
    monkeypatch.setenv("TRANSLATOR_LOCATION", "mock_location")
    monkeypatch.setenv("TEXT_ANALYTICS_KEY", "mock_text_analytics_key")
    monkeypatch.setenv("TEXT_ANALYTICS_ENDPOINT", "https://mock_text_analytics_endpoint")
    monkeypatch.setenv("AI_API_KEY", "mock_ai_key")
    monkeypatch.setenv("AI_ENDPOINT", "https://mock_ai_endpoint")

    # Mock translation request (French response)
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data
        
        def raise_for_status(self):
            """Simulate requests behavior: raise an error for non-200 responses"""
            if self.status_code >= 400:
                raise requests.exceptions.HTTPError(f"HTTP {self.status_code} Error")

    def mock_translate_request(url, headers, json):
        return MockResponse([{"translations": [{"text": "Bienvenue dans le scénario de réservation d'hôtel!"}]}], 200)

    monkeypatch.setattr(requests, "post", mock_translate_request)

    # Setup memory and conversation state
    memory = MemoryStorage()
    conversation_state = ConversationState(memory)
    dialog_state = conversation_state.create_property("DialogState")

    # Create UserState instance for testing (French language)
    user_state = UserState(user_id="test_user", language="fr")

    # Create the DialogSet and add dialogs
    dialogs = DialogSet(dialog_state)
    dialogs.add(TextPrompt("text_prompt"))
    dialogs.add(HotelScenarioDialog(user_state))

    # Mock TurnContext
    turn_context = MagicMock(spec=TurnContext)
    turn_context.activity = MagicMock()
    turn_context.activity.type = "message"
    turn_context.activity.locale = "fr"
    turn_context.turn_state = {"DialogState": dialog_state}

    # Create DialogContext
    dialog_context = await dialogs.create_context(turn_context)

    # Step 1: Bot sends welcome message
    await dialog_context.begin_dialog("HotelScenarioDialog")
    assert dialog_context.active_dialog is not None, "Le dialogue n'a pas démarré correctement"

    # Define test conversation steps in French
    test_steps = [
        "Bonjour, je voudrais réserver une chambre s'il vous plaît",  # Booking request
        "J'ai besoin d'une chambre du 15 mars au 17 mars",  # Provide dates
        "Je voudrais une chambre double",  # Select room type
        "Nous serons deux personnes",  # Provide guest count
        "Nous aimerions une chambre avec vue si possible",  # Special requests
        "Oui, tout cela me convient",  # Confirm booking details
        "Je vais payer avec une carte de crédit",  # Payment method
        "Merci pour votre aide"  # Thank the receptionist
    ]

    # Simulate user responses in a loop
    for step in test_steps:
        turn_context.activity.text = step
        turn_context.activity.get_property = MagicMock(return_value=step)
        await dialog_context.continue_dialog()

    # Ensure all dialog steps are completed
    max_turns = 10  # Prevent infinite loop
    while dialog_context.active_dialog is not None and max_turns > 0:
        await dialog_context.continue_dialog()
        max_turns -= 1

    assert dialog_context.active_dialog is None, "Le dialogue ne s'est pas terminé comme prévu"

    # Verify final score retrieval
    final_score = user_state.get_final_score()
    assert isinstance(final_score, int), "Le score final doit être un entier"
    assert final_score >= 0, "Le score final doit être non négatif"
