from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.events import SlotSet
from typing import Text, Any, Dict
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

# Validation for language form
ALLOWED_LANGUAGES = [
    "spanish", "french", "portuguese"
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

class ValidateTaxiForm(FormValidationAction):
    def name(self) -> str:
        return "validate_taxi_form"

    async def validate_taxi_fare(
        self, value: str, dispatcher: CollectingDispatcher, tracker, domain: DomainDict
    ) -> dict:
        proficiency = tracker.get_slot("language_proficiency")
        language = tracker.get_slot("preferred_language")

        # Skip fare for beginners
        if proficiency == "beginner":
            return {"taxi_fare": None}

        # Provide localized prompt if fare is invalid
        if not value:
            localized_prompt = {
                "English": "Please provide a valid fare response.",
                "Spanish": "Por favor, proporcione una respuesta válida sobre la tarifa.",
                "Portuguese": "Por favor, forneça uma resposta válida sobre a tarifa.",
                "French": "Veuillez fournir une réponse valide concernant le tarif."
            }
            dispatcher.utter_message(text=localized_prompt.get(language, "Please provide a valid response."))
            return {"taxi_fare": None}

        return {"taxi_fare": value}

    async def validate_taxi_negotiation(
        self, value: str, dispatcher: CollectingDispatcher, tracker, domain: DomainDict
    ) -> dict:
        proficiency = tracker.get_slot("language_proficiency")
        language = tracker.get_slot("preferred_language")

        # Skip negotiation for non-advanced users
        if proficiency != "advanced":
            return {"taxi_negotiation": None}

        # Provide localized prompt if negotiation is invalid
        if not value:
            localized_prompt = {
                "English": "Please provide a valid negotiation response.",
                "Spanish": "Por favor, proporcione una respuesta válida para la negociación.",
                "Portuguese": "Por favor, forneça uma resposta válida para a negociação.",
                "French": "Veuillez fournir une réponse valide pour la négociation."
            }
            dispatcher.utter_message(text=localized_prompt.get(language, "Please provide a valid response."))
            return {"taxi_negotiation": None}

        return {"taxi_negotiation": value}

        



