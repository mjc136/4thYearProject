import time
from botbuilder.dialogs import ComponentDialog, DialogSet, DialogTurnStatus, DialogTurnResult
from botbuilder.core import TurnContext
from typing import Optional, Dict
from botbuilder.schema import Activity
import uuid
import requests
from urllib.parse import urlencode
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.appconfiguration import AzureAppConfigurationClient
import os
import logging
from dotenv import load_dotenv
from openai import OpenAI
from backend.bot.state.user_state import UserState

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
        self._initialise_ai()
        self.score = 0  # Initialise the score
        
        # Add conversation history to maintain context
        self.conversation_history = []
        self.max_history_length = 6  # Keep last 6 exchanges for context

    def _initialise_configuration(self):
        """Load required environment variables for API keys and endpoints from Azure App Configuration."""
        
        # Load environment variables from .env file
        load_dotenv()
        
        connection_string = os.getenv("AZURE_APP_CONFIG_CONNECTION_STRING")
        if not connection_string:
            self.logger.warning("Azure App Configuration connection string not set. Using local environment variables.")
            return
            
        try:
            # Connect to Azure App Configuration
            self.logger.info("Connecting to Azure App Configuration...")
            
            # Check if the required variables already exist in the environment
            # If they do, we can skip loading from Azure App Configuration
            required_vars = [
                "TRANSLATOR_KEY",
                "TRANSLATOR_ENDPOINT",
                "TRANSLATOR_LOCATION",
                "TEXT_ANALYTICS_KEY",
                "TEXT_ANALYTICS_ENDPOINT",
                "AI_API_KEY",
                "AI_ENDPOINT"
            ]
            
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            
            # If all variables are present in environment, skip Azure App Configuration
            if not missing_vars:
                self.logger.info("All required variables already in environment, skipping Azure App Configuration")
                return
                
            # Otherwise, load only missing variables from Azure App Configuration
            app_config_client = AzureAppConfigurationClient.from_connection_string(connection_string)

            # Fetch each missing variable from Azure App Configuration with retry
            for var_name in missing_vars:
                max_retries = 3
                retry_count = 0
                retry_delay = 1  # Start with 1 second delay
                
                while retry_count < max_retries:
                    try:
                        setting = app_config_client.get_configuration_setting(key=var_name)
                        value = setting.value
                        os.environ[var_name] = value  # Set the variable as an environment variable
                        print(f"Loaded {var_name} from Azure App Configuration.")
                        break  # Successfully loaded, exit retry loop
                    except Exception as e:
                        # Check if it's a rate limit error
                        if "429" in str(e) or "rate limit" in str(e).lower():
                            retry_count += 1
                            if retry_count < max_retries:
                                self.logger.warning(f"Rate limit hit for {var_name}, retrying in {retry_delay}s (attempt {retry_count}/{max_retries})")
                                time.sleep(retry_delay)
                                retry_delay *= 2  # Exponential backoff
                            else:
                                self.logger.error(f"Failed to load {var_name} after {max_retries} attempts")
                                # Continue with next variable instead of raising exception
                                break
                        else:
                            # Not a rate limit error
                            self.logger.error(f"Failed to fetch {var_name} from Azure App Configuration: {e}")
                            break
        except Exception as e:
            self.logger.error(f"Error initializing configuration: {e}")
            # Continue anyway - we'll use whatever environment variables are available
            pass

    def _initialise_clients(self):
        """Initialise Azure service clients for text analytics."""
        try:            
            self.text_analytics_client = TextAnalyticsClient(
                endpoint=os.getenv("TEXT_ANALYTICS_ENDPOINT"),
                credential=AzureKeyCredential(os.getenv("TEXT_ANALYTICS_KEY"))
            )

            self.logger.info("Successfully initialised Azure clients")
        except Exception as e:
            raise RuntimeError(f"Failed to initialise Azure clients: {e}")
        
    def _initialise_ai(self):
        """Initialise the OpenAI instance."""
        try:
            self.client = OpenAI(
                api_key=os.getenv("AI_API_KEY"),
                base_url=os.getenv("AI_ENDPOINT")
            )
            self.logger.info("OpenAI initialised successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialise OpenAI: {e}")
            raise
        
    async def chatbot_respond(self, turn_context: TurnContext, user_input, system_message):
        """Generate an AI response to the user input.""" 
        proficiency_level = self.user_state.get_proficiency_level()
        language = self.user_state.get_language()
        
        await turn_context.send_activity(Activity(type="typing"))
        
        # initialise memory for the conversation
        default_system_message = f"""You are LingoLizard, a language-learning assistant that helps users practice 
                        languages through interactive role-playing in {proficiency_level} level {language}.
                        You will only reply in {language}. Do not use any emojis or special characters. if using numbers,
                        write them out in words. For example, write "five" instead of "5". Only use euro currency. 
                        do not break the fourth wall. Do not mention that you are an AI or a bot or that you are helping them practice languages. """      
                        
        if proficiency_level == "beginner":
            default_system_message += (
                "In this role-play, the user is a beginner in the target language. "
                "You are a native speaker of that language. Use very simple and clear sentences. "
                "Avoid slang, idioms, advanced grammar, or rare vocabulary. "
                "Speak slowly and repeat or rephrase when needed."
            )
        elif proficiency_level == "intermediate":
            default_system_message += (
                "In this role-play, the user is an intermediate speaker of the target language. "
                "You are a native speaker. Use natural speech with some moderately complex grammar or vocabulary. "
                "Explain or rephrase if the user seems confused, and avoid overly idiomatic expressions."
            )
        else:
            default_system_message += (
                "In this role-play, the user is an advanced speaker of the target language. "
                "You are a native speaker. Speak naturally and professionally, using more fluent and authentic expressions. "
                "You may include some advanced vocabulary and nuanced phrasing, but keep clarity in mind."
            )


        if language == "pt":
            default_system_message += " Use Portuguese from Portugal not brazil."
        elif language == "fr":
            default_system_message += " Use French from France not Canada."
        elif language == "es":
            default_system_message += " Use Spanish from Spain not Latin America."

        combined_system_message = default_system_message + " " + system_message
        
        if not user_input:
            user_input = "fallback"
        try:
            # Build messages array with system message, conversation history, and current user input
            messages = [{"role": "system", "content": combined_system_message}]
            
            # Add conversation history to provide context
            for message in self.conversation_history[-self.max_history_length:]:
                messages.append(message)
                
            # Only add current user message if it's not already in conversation history
            if not self.conversation_history or self.conversation_history[-1]["role"] != "user":
                messages.append({"role": "user", "content": str(user_input)})
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages
            )
            
            bot_response = response.choices[0].message.content
            
            # Add bot response to conversation history
            self.conversation_history.append({"role": "assistant", "content": bot_response})
            
            # Trim conversation history if it gets too long
            if len(self.conversation_history) > self.max_history_length * 2:
                self.conversation_history = self.conversation_history[-self.max_history_length * 2:]
                
            return bot_response
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            return "I apologise, but I encountered an error. Please try again."

    def translate_text(self, text: str, target_language: Optional[str] = None) -> str:
        """Translate text using Azure Translator service."""
        LANGUAGE_CODE_MAP = {
            "english": "en",
            "spanish": "es",
            "french": "fr",
            "portuguese": "pt"
        }

        lang_name = self.user_state.get_language()
        target_language = LANGUAGE_CODE_MAP.get(lang_name)

        if not target_language:
            raise ValueError(f"Unsupported language for translation: {lang_name}")

        if not text:
            raise ValueError("No text provided for translation")

        url = f"{os.getenv('TRANSLATOR_ENDPOINT')}/translate?{urlencode({'api-version': '3.0', 'to': target_language})}"
        headers = {
            'Ocp-Apim-Subscription-Key': os.getenv("TRANSLATOR_KEY"),
            'Ocp-Apim-Subscription-Region': os.getenv("TRANSLATOR_LOCATION"),
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

        return response.sentiment

    def detect_language(self, text: str) -> str:
        """Detect the language of the given text using Azure Text Analytics."""
        if not text.strip():
            return "No text provided for language detection."
        response = self.text_analytics_client.detect_language(documents=[{"id": "1", "text": text}])[0]
        return response.primary_language.iso6391_name

    async def run(self, turn_context: TurnContext, accessor):
        """
        Runs the dialogue with the given context and state accessor.
        Handles the conversation flow using the DialogSet and DialogContext classes.
        """
        dialog_set = DialogSet(accessor)
        dialog_set.add(self)
        
        try:
            dialog_context = await dialog_set.create_context(turn_context)
            
            results = await dialog_context.continue_dialog()
            
            # Handle case where continue_dialog returns None
            if results is None:
                self.logger.warning("Dialog context continue_dialog returned None")
                # Initialize with empty result to avoid NoneType errors
                from botbuilder.dialogs import DialogTurnResult, DialogTurnStatus
                results = DialogTurnResult(DialogTurnStatus.Empty)
            
            if results.status == DialogTurnStatus.Empty:
                return await dialog_context.begin_dialog(self.id)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in dialog execution: {str(e)}", exc_info=True)
            # Send a message to the user that something went wrong
            await turn_context.send_activity("I apologize, but something went wrong. Let's try again.")
            # Return a default dialog result to prevent cascading errors
            from botbuilder.dialogs import DialogTurnResult, DialogTurnStatus
            return DialogTurnResult(DialogTurnStatus.Cancelled)
