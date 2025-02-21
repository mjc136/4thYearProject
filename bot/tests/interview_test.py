import pytest
from unittest.mock import MagicMock, AsyncMock
import requests
from botbuilder.core import MemoryStorage, ConversationState, TurnContext
from botbuilder.dialogs import DialogSet, DialogTurnStatus
from botbuilder.dialogs.prompts import TextPrompt
from bot.dialogs.job_interview_scenario import JobInterviewScenarioDialog
from bot.state.user_state import UserState

@pytest.mark.asyncio
async def test_job_interview_scenario_flow(monkeypatch):
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
            json=lambda: [{"translations": [{"text": "Bienvenido al escenario de Entrevista de Trabajo!"}]}]  # Mock translated text
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
    dialogs.add(JobInterviewScenarioDialog(user_state))  # Pass UserState to JobInterviewScenarioDialog

    # Mock TurnContext
    turn_context = MagicMock(spec=TurnContext)
    turn_context.activity = MagicMock()
    turn_context.activity.type = "message"
    turn_context.activity.locale = "en-us"
    turn_context.turn_state = {"DialogState": dialog_state}  # Ensure consistent dialog state

    # Create DialogContext
    dialog_context = await dialogs.create_context(turn_context)

    # Step 1: Bot sends welcome message and prompts for job interview
    await dialog_context.begin_dialog("JobInterviewScenarioDialog")
    assert dialog_context.active_dialog is not None

    # Step 2: User discusses experience
    turn_context.activity.text = "I have four years of experience as a customer service representative"
    turn_context.activity.get_property = MagicMock(return_value="I have four years of experience as a customer service representative")
    await dialog_context.continue_dialog()

    # Step 3: User discusses key skills
    turn_context.activity.text = "I am skilled in active listening and conflict resolution"
    turn_context.activity.get_property = MagicMock(return_value="I am skilled in active listening and conflict resolution")
    await dialog_context.continue_dialog()

    # Step 4: User answers why they want the job
    turn_context.activity.text = "I enjoy helping people and ensuring they have a positive experience"
    turn_context.activity.get_property = MagicMock(return_value="I enjoy helping people and ensuring they have a positive experience")
    await dialog_context.continue_dialog()

    # Step 5: User discusses strengths and weaknesses
    turn_context.activity.text = "My biggest strength is my ability to stay calm and professional in high-pressure situations"
    turn_context.activity.get_property = MagicMock(return_value="My biggest strength is my ability to stay calm and professional in high-pressure situations")
    await dialog_context.continue_dialog()

    # Step 6: User provides salary expectation
    turn_context.activity.text = "I am looking for a salary range of $40,000 - $50,000 per year"
    turn_context.activity.get_property = MagicMock(return_value="I am looking for a salary range of $40,000 - $50,000 per year")
    await dialog_context.continue_dialog()

    # Step 7: Scenario completion
    assert dialog_context.active_dialog is None

    # Step 8: Verify final score retrieval
    final_score = user_state.get_final_score()
    assert isinstance(final_score, int), "Final score should be an integer"
    assert final_score >= 0, "Final score should be non-negative"
