# import spacy

# nlp = spacy.load("en_core_web_sm")

# intents = {
#     "beginner": ["beginner", "basic", "novice"],
#     "intermediate": ["intermediate", "medium", "average"],
#     "advanced": ["advanced", "expert", "proficient", "fluent"],
#     "greeting": ["hello", "hi", "hey", "greetings"],
#     "farewell": ["bye", "goodbye", "see you", "farewell"],
#     "thanks": ["thanks", "thank you", "appreciate", "grateful"],
#     "affirmative": ["yes", "yep", "yeah", "correct", "right"],
#     "negative": ["no", "nope", "nah", "incorrect", "wrong"]
# }

# def recognise_intent_and_entities(message):
#     # Ensure the message is a valid string
#     if not isinstance(message, str) or not message.strip():
#         return "unknown", []

#     doc = nlp(message)
#     intent = "unknown"
#     entities = []

#     # Intent recognition with keyword matching
#     for key, keywords in intents.items():
#         if any(keyword in message.lower() for keyword in keywords):
#             intent = key
#             break

#     # Extract entities using SpaCy
#     for ent in doc.ents:
#         entities.append({"text": ent.text, "label": ent.label_})

#     return intent, entities
