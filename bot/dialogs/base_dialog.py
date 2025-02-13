from botbuilder.dialogs import ComponentDialog, DialogSet, DialogTurnStatus
from botbuilder.core import TurnContext
from typing import Optional
import uuid
import requests
import json
from urllib.parse import urlencode
from difflib import SequenceMatcher
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import os
import logging
from dotenv import load_dotenv

class BaseDialog(ComponentDialog):
    """
    Base class for bot dialogs. This class handles:
    - Configuration loading from environment variables.
    - Initialization of Azure services for translation and text analytics.
    - Running and managing bot dialogs.
    """
    def __init__(self, dialog_id: str, user_state=None):
        super(BaseDialog, self).__init__(dialog_id)
        self.user_state = user_state
        self.logger = logging.getLogger(__name__)
        self._initialise_configuration()
        self._initialise_clients()

    def _initialise_configuration(self):
        """Load required environment variables for API keys and endpoints."""
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
            self.logger.info(f"Loaded .env file from {env_path}")

        required_vars = {
            "TRANSLATOR_KEY": None,
            "TRANSLATOR_ENDPOINT": None,
            "TRANSLATOR_LOCATION": None,
            "TEXT_ANALYTICS_KEY": None,
            "TEXT_ANALYTICS_ENDPOINT": None
        }

        for var_name in required_vars:
            value = os.getenv(var_name)
            if not value:
                raise ValueError(f"Missing required environment variable: {var_name}")
            setattr(self, var_name, value)

    def _initialise_clients(self):
        """Initialize Azure service clients for text analytics."""
        try:
            self.text_analytics_client = TextAnalyticsClient(
                endpoint=self.TEXT_ANALYTICS_ENDPOINT,
                credential=AzureKeyCredential(self.TEXT_ANALYTICS_KEY)
            )
            self.logger.info("Successfully initialized Azure clients")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Azure clients: {e}")

    async def run(self, turn_context: TurnContext, accessor):
        """Runs the dialog with the given context and state accessor."""
        dialog_set = DialogSet(accessor)
        dialog_set.add(self)
        dialog_context = await dialog_set.create_context(turn_context)
        results = await dialog_context.continue_dialog()
        if results.status == DialogTurnStatus.Empty:
            await dialog_context.begin_dialog(self.id)

    def get_user_language(self) -> str:
        """Retrieve the user's selected language from user state."""
        return self.user_state.language if hasattr(self.user_state, "language") else "en"

    def translate_text(self, text: str, to_language: Optional[str] = None) -> str:
        """Translate text using Azure Translator service."""
        if not text:
            raise ValueError("No text provided for translation")
        target_language = to_language or self.get_user_language()
        url = f"{self.TRANSLATOR_ENDPOINT}/translate?{urlencode({'api-version': '3.0', 'to': target_language})}"
        headers = {
            'Ocp-Apim-Subscription-Key': self.TRANSLATOR_KEY,
            'Ocp-Apim-Subscription-Region': self.TRANSLATOR_LOCATION,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }
        try:
            response = requests.post(url, headers=headers, json=[{'text': text}])
            response.raise_for_status()
            translations = response.json()
            if not translations or not translations[0].get('translations'):
                return "Translation unavailable."
            return translations[0]['translations'][0]['text']
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Translation request failed: {str(e)}")

    def analyse_sentiment(self, text: str) -> str:
        """Analyze sentiment of the given text using Azure Text Analytics."""
        response = self.text_analytics_client.analyze_sentiment(documents=[{"id": "1", "text": text}])[0]
        return f"Sentiment: {response.sentiment}, Positive: {response.confidence_scores.positive:.2f}, Negative: {response.confidence_scores.negative:.2f}, Neutral: {response.confidence_scores.neutral:.2f}"

    def detect_language(self, text: str) -> str:
        """Detect the language of the given text using Azure Text Analytics."""
        if not text.strip():
            return "No text provided for language detection."
        response = self.text_analytics_client.detect_language(documents=[{"id": "1", "text": text}])[0]
        return response.primary_language.iso6391_name

    def extract_entities(self, text: str) -> str:
        """Extract named entities from the given text using Azure Text Analytics."""
        if not text.strip():
            return "No text provided for entity recognition."
        response = self.text_analytics_client.recognize_entities(documents=[{"id": "1", "text": text}])[0]
        entities = [f"{entity.text} ({entity.category})" for entity in response.entities]
        return "Entities: " + ", ".join(entities) if entities else "No entities found."
    
    def evaluate_response(self, response: str, correct_text: str) -> str:
        """Evaluate the user's response compared to the expected correct text."""
        response_language = self.detect_language(response)
        correct_text_language = self.detect_language(correct_text)
        similarity = SequenceMatcher(None, response.lower().strip(), correct_text.lower().strip()).ratio()
        if similarity > 0.8:
            return "Excellent! That's correct!"
        elif similarity > 0.5:
            return f"Good try! The correct phrase is: {correct_text}"
        else:
            return f"Keep practicing! The correct phrase is: {correct_text}"
