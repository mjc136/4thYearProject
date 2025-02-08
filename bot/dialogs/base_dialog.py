from botbuilder.dialogs import ComponentDialog, DialogSet, DialogTurnStatus
from botbuilder.core import TurnContext
from typing import Optional
import uuid
import requests
import json
from urllib.parse import urlencode
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.appconfiguration import AzureAppConfigurationClient
import os
import logging
from dotenv import load_dotenv

class BaseDialog(ComponentDialog):
    def __init__(self, dialog_id: str, user_state=None):
        super(BaseDialog, self).__init__(dialog_id)
        self.user_state = user_state

        # Configure logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

        # Load environment variables
        if os.path.exists('bot/.env'):
            load_dotenv()
            self.logger.info("Loaded local .env file")
        else:
            self.logger.info("No .env file found, using environment variables")

        # Fetch configuration from Azure App Configuration
        connection_string = os.getenv("AZURE_APP_CONFIG_CONNECTION_STRING", "")
        if not connection_string:
            raise RuntimeError("Error: AZURE_APP_CONFIG_CONNECTION_STRING is not set.")

        try:
            self.TRANSLATOR_KEY = os.getenv(key="TRANSLATOR_KEY")
            self.TRANSLATOR_ENDPOINT = os.getenv(key="TRANSLATOR_ENDPOINT")
            self.TRANSLATOR_LOCATION = os.getenv(key="TRANSLATOR_LOCATION")
            self.TEXT_ANALYTICS_KEY = os.getenv(key="TEXT_ANALYTICS_KEY")
            self.TEXT_ANALYTICS_ENDPOINT = os.getenv(key="TEXT_ANALYTICS_ENDPOINT")

            if not all([self.TRANSLATOR_KEY, self.TRANSLATOR_ENDPOINT, self.TRANSLATOR_LOCATION,
                        self.TEXT_ANALYTICS_KEY, self.TEXT_ANALYTICS_ENDPOINT]):
                raise RuntimeError("Missing required configuration values from Azure App Configuration")

            self.logger.info("Successfully retrieved keys from Azure App Configuration.")

        except Exception as e:
            raise RuntimeError(f"Error fetching configuration from Azure App Configuration: {e}")

    async def run(self, turn_context: TurnContext, accessor):
        """Runs the dialog."""
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
        """Translate text using Azure Translator."""
        if not text:
            raise ValueError("No text provided for translation")

        target_language = to_language or self.get_user_language()

        key = self.TRANSLATOR_KEY
        endpoint = self.TRANSLATOR_ENDPOINT
        location = self.TRANSLATOR_LOCATION

        if not all([key, endpoint, location]):
            raise ValueError("Missing required translator configuration")

        url = f"{endpoint}/translate?{urlencode({'api-version': '3.0', 'to': target_language})}"
        headers = {
            'Ocp-Apim-Subscription-Key': key,
            'Ocp-Apim-Subscription-Region': location,
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

    def analyse_text(self, text: str) -> str:
        """Analyse text using Azure Text Analytics."""
        # ...existing code...

    def initialise_client(self):
        """Initialise the Text Analytics client."""
        # ...existing code...

    def customise_settings(self):
        """Customise dialog settings."""
        # ...existing code...

    async def analyse_text_in_bot(self, turn_context):
        """Analyse text entities using Azure Text Analytics."""
        user_input = turn_context.activity.text

        try:
            key = self.TEXT_ANALYTICS_KEY
            endpoint = self.TEXT_ANALYTICS_ENDPOINT

            if not all([key, endpoint]):
                raise ValueError("Missing Text Analytics configuration")

            client = TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(key))
            response = client.recognise_entities([user_input])
            entities = [f"{entity.text} ({entity.category})" for entity in response[0].entities]

            if entities:
                await turn_context.send_activity(f"Identified entities: {', '.join(entities)}")
            else:
                await turn_context.send_activity("No entities were detected.")
        except Exception as e:
            await turn_context.send_activity(f"Error analysing text: {str(e)}")