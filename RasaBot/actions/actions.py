from rasa_sdk import Action
from rasa_sdk.events import SlotSet

class ActionSetGreeting(Action):
    def name(self):
        return "action_set_greeting"

    async def run(self, dispatcher, tracker, domain):
        preferred_language = tracker.get_slot("preferred_language")
        
        # Define greetings in various languages
        greetings = {
            "en": "Hello! How can I help you today?",
            "es": "¡Hola! ¿Cómo puedo ayudarte hoy?",
            "fr": "Bonjour! Comment puis-je vous aider aujourd'hui?",
            "de": "Hallo! Wie kann ich Ihnen heute helfen?",
            # Add more languages as needed
        }

        # Default to English if the language is not found
        greeting = greetings.get(preferred_language, greetings["en"])
        
        # Set the greeting as a slot
        return [SlotSet("greeting", greeting)]
