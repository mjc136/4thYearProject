from botbuilder.dialogs import ComponentDialog, DialogSet, DialogTurnStatus
from botbuilder.core import TurnContext
from typing import Optional, Dict, Any
import uuid
import requests
import json
from urllib.parse import urlencode
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv

class BaseDialog(ComponentDialog):
    def __init__(self, dialog_id: str, user_state=None, config=None):
        super(BaseDialog, self).__init__(dialog_id)
        self.user_state = user_state
        self.config = config

    async def run(self, turn_context: TurnContext, accessor):
        """Runs the dialog by creating a DialogSet and continuing or starting the dialog."""
        dialog_set = DialogSet(accessor)
        dialog_set.add(self)

        dialog_context = await dialog_set.create_context(turn_context)
        results = await dialog_context.continue_dialog()
        if results.status == DialogTurnStatus.Empty:
            await dialog_context.begin_dialog(self.id)

    def get_user_language(self) -> str:
        """Retrieve the user's selected language from user state."""
        if self.user_state and hasattr(self.user_state, 'get_language'):
            return self.user_state.get_language()
        return 'en'

    def translate_text(self, text: str, to_language: Optional[str] = None) -> str:
        """
        Translate text using Azure Translator.
        
        Args:
            text: Text to translate
            to_language: Target language code (ISO 639-1)
            
        Returns:
            str: Translated text
            
        Raises:
            ValueError: If translation fails or config is missing
        """
        if not self.config:
            raise ValueError("Configuration not provided to dialog")

        if not text:
            raise ValueError("No text provided for translation")

        target_language = to_language or self.get_user_language()

        # Get translator settings from config
        key = self.config.TRANSLATOR_KEY
        endpoint = self.config.TRANSLATOR_ENDPOINT
        location = self.config.TRANSLATOR_LOCATION

        if not all([key, endpoint, location]):
            raise ValueError("Missing required translator configuration")

        # Construct URL with proper parameter encoding
        base_url = f"{endpoint}/translate"
        params = {
            'api-version': '3.0',
            'to': target_language
        }
        url = f"{base_url}?{urlencode(params)}"

        # Prepare headers
        headers = {
            'Ocp-Apim-Subscription-Key': key,
            'Ocp-Apim-Subscription-Region': location,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }

        # Make request
        try:
            response = requests.post(
                url,
                headers=headers,
                json=[{'text': text}]
            )
            response.raise_for_status()
            
            translations = response.json()
            if not translations or not translations[0].get('translations'):
                raise ValueError("No translation returned from API")
                
            return translations[0]['translations'][0]['text']
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Translation request failed: {str(e)}")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to process translation response: {str(e)}")

    async def analyze_text_in_bot(turn_context):
        user_input = turn_context.activity.text
        
        try:
            # Azure credentials
            key = os.getenv("TEXT_ANALYTICS_KEY")
            endpoint = os.getenv("TEXT_ANALYTICS_ENDPOINT")
            client = TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(key))
            
            # Analyze entities
            response = client.recognize_entities([user_input])
            entities = [f"{entity.text} ({entity.category})" for entity in response[0].entities]
            
            if entities:
                await turn_context.send_activity(f"Identified entities: {', '.join(entities)}")
            else:
                await turn_context.send_activity("No entities were detected.")
                
        except Exception as e:
            await turn_context.send_activity(f"Error analyzing text: {str(e)}")