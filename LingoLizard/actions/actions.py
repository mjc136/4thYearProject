from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.events import SlotSet
from typing import Text, Any, Dict
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

# Validation for language form
ALLOWED_LANGUAGES = [
    "spanish", "french", "german", "portuguese"
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
        
        return {"selected_scenario": slot_value}
        



