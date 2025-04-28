from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.appconfiguration import AzureAppConfigurationClient
from dotenv import load_dotenv
import os

# Load environment variables from a specific path
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend', '.env')
load_dotenv(dotenv_path=env_path)
        
connection_string = os.getenv("AZURE_APP_CONFIG_CONNECTION_STRING")
if not connection_string:
    raise ValueError("Azure App Configuration connection string is not set.")

# Connect to Azure App Configuration
app_config_client = AzureAppConfigurationClient.from_connection_string(connection_string)

required_vars = [
    "TRANSLATOR_KEY",
    "TRANSLATOR_ENDPOINT",
    "TRANSLATOR_LOCATION",
    "TEXT_ANALYTICS_KEY",
    "TEXT_ANALYTICS_ENDPOINT",
    "AI_API_KEY",
    "AI_ENDPOINT"
]

# Fetch each variable from Azure App Configuration
for var_name in required_vars:
    try:
        setting = app_config_client.get_configuration_setting(key=var_name)
        value = setting.value
        os.environ[var_name] = value  # Set the variable as an environment variable
        print(f"Loaded {var_name} from Azure App Configuration.")
    except Exception as e:
        raise ValueError(f"Failed to fetch {var_name} from Azure App Configuration: {e}")

def authenticate_client():
    """Authenticate the client using credentials and endpoint."""
    KEY = os.getenv("TEXT_ANALYTICS_KEY")
    ENDPOINT = os.getenv("TEXT_ANALYTICS_ENDPOINT")
    if not KEY or not ENDPOINT:
        raise ValueError("Environment variables for TEXT_ANALYTICS_KEY and TEXT_ANALYTICS_ENDPOINT must be set.")
    return TextAnalyticsClient(endpoint=ENDPOINT, credential=AzureKeyCredential(KEY))

def sentiment_analysis_example(client):
    """Analyse sentiment for a given text."""
    input_text = "yes that is correct"
    response = client.analyze_sentiment(documents=[input_text])[0]

    # print(f"Document sentiment: {response.sentiment}\n")
    # for sentence in response.sentences:
    #     print(f"\tText: \"{sentence.text}\"")
    #     print(f"\tSentence sentiment: {sentence.sentiment}")
    #     print(f"\tPositive score: {sentence.confidence_scores.positive:.2f}")
    #     print(f"\tNegative score: {sentence.confidence_scores.negative:.2f}")
    #     print(f"\tNeutral score: {sentence.confidence_scores.neutral:.2f}\n")
        
    if response.sentiment == "positive":
        print("The sentiment is positive.")

def language_detection_example(client):
    """Detect the language of a given text."""
    input_text = "Eu tehno uma casa muito bonita."
    response = client.detect_language(documents=[input_text])[0]

    print("Language:")
    print(f"\t{response.primary_language.name}\tISO-6391: {response.primary_language.iso6391_name}\n")

def entity_recognition_example(client):
    """Extract entities from text."""
    input_text = "i wanna go to the beach"
    response = client.recognize_entities(documents=[{"id": "1", "text": input_text}])[0]

    print("Named Entities:")
    for entity in response.entities:
        if entity.category == "Location" or (True):
            print(f"\tText: {entity.text}, Category: {entity.category}, Confidence: {entity.confidence_score:.2f}\n")

def key_phrase_extraction(client):
    """Extract key phrases from text."""
    text = "I will travel to Paris next Friday. I will visit the Eiffel Tower and enjoy a croissant."

    response = client.extract_key_phrases(documents=[text])[0]
    print("Key Phrases:")
    print(f"\tKey Phrases: {', '.join(response.key_phrases)}\n")

if __name__ == "__main__":
    # Authenticate the client
    client = authenticate_client()

    # Perform sentiment analysis
    sentiment_analysis_example(client)

    # # Perform language detection
    # language_detection_example(client)

    # Perform entity recognition
    entity_recognition_example(client)

    # # Perform key phrase extraction
    # key_phrase_extraction(client)