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

ALLOWED_SCENARIOS = [
    "restaurant", "taxi", "hotel", "directions"
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
            dispatcher.utter_message(text="Invalid proficiency")
            return {"language_proficiency": None}
        
        dispatcher.utter_message(text=f"We will practice at a {slot_value} level.")
        return {"language_proficiency": slot_value}
    
class ValidateScenarioForm(FormValidationAction):
    def name(self) -> str:
        return "validate_scenario_form"
    
    def validate_selected_scenario(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        """Validate `selected_scenario` value."""
        if slot_value.lower() not in ALLOWED_SCENARIOS:
            dispatcher.utter_message(text=f"Invalid scenario. Available options are: {', '.join(ALLOWED_SCENARIOS)}.")
            return {"selected_scenario": None}
        
        dispatcher.utter_message(text=f"OK! We will practice the {slot_value} scenario.")
        return {"selected_scenario": slot_value}
        
from translation_utils import translate_text

class ActionTranslateUtterance(Action):
    def name(self) -> str:
        return "action_translate_utterance"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> list:
        # Get the text to translate from the tracker and the preferred language slot
        target_language = tracker.get_slot("preferred_language")
        response_text = tracker.get_slot("utterance_to_translate")  # Use a slot to capture utterance text

        # Translate the response if a target language is set
        if target_language and response_text:
            translated_response = translate_text(response_text, target_lang=target_language)
        else:
            translated_response = response_text  # Default to original text if no language is set

        # Send translated response to the user
        dispatcher.utter_message(text=translated_response)
        return []

