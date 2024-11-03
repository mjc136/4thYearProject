from rasa_sdk import Action
from rasa_sdk.events import SlotSet
from deep_translator import GoogleTranslator

class ActionSetPreferredLanguage(Action):
    def name(self) -> str:
        return "action_set_preferred_language"

    async def run(self, dispatcher, tracker, domain):
        # Get the user's language preference from the conversation
        language_preference = tracker.get_slot("preferred_language")
        # Optionally do some logic, e.g., verify or map the language

        dispatcher.utter_message(text=f"Setting language preference to: {language_preference}")
        return [SlotSet("preferred_language", language_preference)]


class ActionRespondInPreferredLanguage(Action):
    def name(self) -> str:
        return "action_respond_in_preferred_language"

    async def run(self, dispatcher, tracker, domain):
        # Get the user's preferred language from the slot
        preferred_language = tracker.get_slot("preferred_language")
        response_text = "This is a test message. How can I assist you further?"

        if preferred_language and preferred_language != "en":
            # Translate the response using GoogleTranslator
            try:
                translated_text = GoogleTranslator(source='en', target=preferred_language).translate(response_text)
                dispatcher.utter_message(text=translated_text)
            except Exception as e:
                dispatcher.utter_message(text=f"Sorry, I couldn't translate the message. Error: {str(e)}")
        else:
            # If no preferred language or the preferred language is English, respond in English
            dispatcher.utter_message(text=response_text)

        return []
