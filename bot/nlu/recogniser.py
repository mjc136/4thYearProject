import spacy

nlp = spacy.load("en_core_web_sm")

def recognise_intent_and_entities(message):
    """
    Recognises user intent and extracts entities.
    Args:
        message (str): The user's input message.

    Returns:
        tuple: (intent, entities)
    """
    # Ensure the message is a valid string
    if not isinstance(message, str) or not message.strip():
        return "unknown", []

    doc = nlp(message)
    intent = None
    entities = []

    # Basic intent recognition
    if "taxi" in message.lower():
        intent = "select_taxi_scenario"
    elif "hotel" in message.lower():
        intent = "select_hotel_scenario"
    else:
        intent = "unknown"

    # Extract entities
    for ent in doc.ents:
        entities.append({"text": ent.text, "label": ent.label_})

    return intent, entities
