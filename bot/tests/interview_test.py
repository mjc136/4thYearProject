import pytest
from unittest.mock import MagicMock, patch
import requests
from botbuilder.core import MemoryStorage, ConversationState, TurnContext
from botbuilder.dialogs import DialogSet
from botbuilder.dialogs.prompts import TextPrompt
from bot.dialogs.job_interview_scenario import JobInterviewScenarioDialog  # Ensure correct import
from bot.state.user_state import UserState

@pytest.mark.asyncio
@patch("bot.dialogs.base_dialog.AzureAppConfigurationClient.from_connection_string")
@patch("bot.dialogs.base_dialog.OpenAI")  # Mock OpenAI
async def test_job_interview_scenario_flow(mock_openai, mock_config_client, monkeypatch):
    """
    Test flow for the JobInterviewScenarioDialog.
    """

    # Mock OpenAI API response
    mock_openai_instance = MagicMock()
    mock_openai_instance.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="Resposta simulada da IA"))
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

    # Mock translation request (Portuguese response)
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
        return MockResponse([{"translations": [{"text": "Bem-vindo ao cenário de entrevista de emprego!"}]}], 200)

    monkeypatch.setattr(requests, "post", mock_translate_request)

    # Setup memory and conversation state
    memory = MemoryStorage()
    conversation_state = ConversationState(memory)
    dialog_state = conversation_state.create_property("DialogState")

    # Create UserState instance for testing (Portuguese language)
    user_state = UserState(user_id="test_user", language="pt")

    # Create the DialogSet and add dialogs
    dialogs = DialogSet(dialog_state)
    dialogs.add(TextPrompt("text_prompt"))
    dialogs.add(JobInterviewScenarioDialog(user_state))

    # Mock TurnContext
    turn_context = MagicMock(spec=TurnContext)
    turn_context.activity = MagicMock()
    turn_context.activity.type = "message"
    turn_context.activity.locale = "pt"
    turn_context.turn_state = {"DialogState": dialog_state}

    # Create DialogContext
    dialog_context = await dialogs.create_context(turn_context)

    # Step 1: Bot sends welcome message
    await dialog_context.begin_dialog("JobInterviewScenarioDialog")
    assert dialog_context.active_dialog is not None, "O diálogo não foi iniciado corretamente"

    # Define test conversation steps in Portuguese
    test_steps = [
        "Olá, meu nome é João e estou interessado nesta posição.",  # Introduction
        "Tenho cinco anos de experiência em atendimento ao cliente.",  # Experience
        "Tenho boas habilidades de comunicação e sou muito paciente.",  # Skills
        "Quero trabalhar no atendimento ao cliente porque gosto de ajudar as pessoas.",  # Motivation
        "Meu maior ponto forte é a empatia. Minha maior fraqueza é a impaciência em algumas situações.",  # Strengths & Weaknesses
        "Minha expectativa salarial é de 2.500 euros por mês.",  # Salary Expectations
        "Quais são as oportunidades de crescimento nesta empresa?",  # Candidate's Question
        "Muito obrigado pelo seu tempo e pela oportunidade!"  # Closing remarks
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

    assert dialog_context.active_dialog is None, "O diálogo não foi concluído conforme esperado"

    # Verify final score retrieval
    final_score = user_state.get_final_score()
    assert isinstance(final_score, int), "A pontuação final deve ser um número inteiro"
    assert final_score >= 0, "A pontuação final deve ser não negativa"
