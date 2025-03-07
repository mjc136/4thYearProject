from botbuilder.dialogs import ComponentDialog, DialogSet, DialogTurnStatus
from botbuilder.core import TurnContext
from typing import Optional, Tuple, Dict
import uuid
import requests
from urllib.parse import urlencode
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import os
import logging
from dotenv import load_dotenv
import language_tool_python
from azure.appconfiguration import AzureAppConfigurationClient
from azure.core.credentials import AzureKeyCredential

class BaseDialog(ComponentDialog):
    """
    Base class for bot dialogues. This class handles:
    - Configuration loading from environment variables.
    - Initialisation of Azure services for translation and text analytics.
    - Running and managing bot dialogues.
    """
    
    def __init__(self, dialog_id: str, user_state=None):
        super(BaseDialog, self).__init__(dialog_id)
        self.user_state = user_state
        self.logger = logging.getLogger(__name__)
        self._initialise_configuration()
        self._initialise_clients()
        self.score = 0  # Initialise the score

    def _initialise_configuration(self):
        """Load required environment variables for API keys and endpoints from Azure App Configuration."""
        
        # Load environment variables from .env if present
        if os.path.exists('bot/.env'):
            load_dotenv()  # Load local .env if it exists
        else:
            self.logger.info("No .env file found, using environment variables")
        
        connection_string = os.getenv("AZURE_APP_CONFIG_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("Azure App Configuration connection string is not set.")

        # Connect to Azure App Configuration
        app_config_client = AzureAppConfigurationClient.from_connection_string(connection_string)

        required_vars = [
            "TRANSLATOR_KEY",
            "TRANSLATOR_ENDPOINT",
            "TRANSLATOR_LOCATION",
            "TEXT_ANALYTICS_KEY",
            "TEXT_ANALYTICS_ENDPOINT"
        ]

        # Fetch each variable from Azure App Configuration
        for var_name in required_vars:
            try:
                setting = app_config_client.get_configuration_setting(key=var_name)
                value = setting.value
                setattr(self, var_name, value)  # Set the variable as an attribute of the object
                self.logger.info(f"Loaded {var_name} from Azure App Configuration.")
            except Exception as e:
                raise ValueError(f"Failed to fetch {var_name} from Azure App Configuration: {e}")

    def _initialise_clients(self):
        """Initialise Azure service clients for text analytics."""
        try:
            self.text_analytics_client = TextAnalyticsClient(
                endpoint=self.TEXT_ANALYTICS_ENDPOINT,
                credential=AzureKeyCredential(self.TEXT_ANALYTICS_KEY)
            )
            self.logger.info("Successfully initialised Azure clients")
        except Exception as e:
            raise RuntimeError(f"Failed to initialise Azure clients: {e}")
        
    def _initialise_language_tool(self, language: str):
        """Initialise the LanguageTool instance."""
        supported_languages = {
            "es": "es",
            "fr": "fr",
            "pt": "pt"
        }
        if language.lower() not in supported_languages:
            raise ValueError(f"Unsupported language: {language}")
        
        language_code = supported_languages[language.lower()]
        try:
            self.tool = language_tool_python.LanguageTool(language_code)
            self.logger.info("LanguageTool initialised successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialise LanguageTool: {e}")
            raise

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
        
    def analyse_sentiment(self, text: str) -> Dict[str, float]:
        """Analyse sentiment of the given text using Azure Text Analytics."""
        if not text.strip():
            return {"sentiment": "neutral", "positive": 0.5, "negative": 0.5, "neutral": 1.0}

        response = self.text_analytics_client.analyze_sentiment(documents=[{"id": "1", "text": text}])[0]

        return {
            "sentiment": response.sentiment,
            "positive": response.confidence_scores.positive,
            "negative": response.confidence_scores.negative,
            "neutral": response.confidence_scores.neutral
        }

    def detect_language(self, text: str) -> str:
        """Detect the language of the given text using Azure Text Analytics."""
        if not text.strip():
            return "No text provided for language detection."
        response = self.text_analytics_client.detect_language(documents=[{"id": "1", "text": text}])[0]
        return response.primary_language.iso6391_name

    def extract_entities(self, text: str) -> Dict[str, str]:
        """Extract named entities from the given text using Azure Text Analytics."""
        if not text.strip():
            return {}

        response = self.text_analytics_client.recognize_entities(documents=[{"id": "1", "text": text}])[0]
        entities = {entity.text: entity.category for entity in response.entities}

        return entities if entities else {}


    def process_text_analysis(self, text: str) -> Dict[str, any]:
        """
        Perform multiple text processing operations in a single method call.
        This includes:
        - Sentiment analysis
        - Language detection
        - Named entity recognition
        
        Returns a dictionary containing results for all operations.
        """
        if not text.strip():
            return {
                "sentiment": "neutral",
                "positive": 0.5,
                "negative": 0.5,
                "neutral": 1.0,
                "language": "",
                "entities": {}
            }
        
        
        # Perform sentiment analysis to determine emotional tone
        sentiment_result = self.analyse_sentiment(text)
        
        # Detect the language of the input text
        detected_language = self.detect_language(text)
        
        # Extract named entities from the text
        entities = self.extract_entities(text)
        
        return {
            "sentiment": sentiment_result["sentiment"],
            "positive": sentiment_result["positive"],
            "negative": sentiment_result["negative"],
            "neutral": sentiment_result["neutral"],
            "language": detected_language,
            "entities": entities
        }

    async def run(self, turn_context: TurnContext, accessor):
        """
        Runs the dialogue with the given context and state accessor.
        Handles the conversation flow using the DialogSet and DialogContext classes.
        """
        dialog_set = DialogSet(accessor)
        dialog_set.add(self)
        dialog_context = await dialog_set.create_context(turn_context)
        results = await dialog_context.continue_dialog()
        if results.status == DialogTurnStatus.Empty:
            await dialog_context.begin_dialog(self.id)
