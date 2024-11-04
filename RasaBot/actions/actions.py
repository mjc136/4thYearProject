from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.events import SlotSet
from typing import Text, Any, Dict
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

# Validation for language form
ALLOWED_LANGUAGES = [
    "spanish", "french", "german", "italian", "portuguese", "polish"
]
ALLOWED_LANGUAGE_PROFICIENCIES = [
    "beginner", "intermediate", "advanced"
]

class ValidateLanguageForm(FormValidationAction):
    def name(self) -> str:
        return "validate_language_form"
    
    def validate_preferred_language(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        """Validate `preferred_language` value."""
        if slot_value.lower() not in ALLOWED_LANGUAGES:
            dispatcher.utter_message(text=f"I can only teach: {', '.join(ALLOWED_LANGUAGES)}.")
            return {"preferred_language": None}
        
        dispatcher.utter_message(text=f"OK! We will practice {slot_value}.")
        return {"preferred_language": slot_value}
    
    def validate_language_proficiency(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        """Validate `language_proficiency` value."""
        if slot_value.lower() not in ALLOWED_LANGUAGE_PROFICIENCIES:
            dispatcher.utter_message(text="Only valid options are beginner, intermediate, advanced.")
            return {"language_proficiency": None}
        
        dispatcher.utter_message(text=f"We will practice at a {slot_value} level.")
        return {"language_proficiency": slot_value}
