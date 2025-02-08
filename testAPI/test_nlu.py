from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
import os

# Load environment variables from a specific path
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bot', '.env')
load_dotenv(dotenv_path=env_path)

# Replace with your Azure Text Analytics Key and Endpoint
KEY = os.getenv("AZURE_TEXT_ANALYTICS_KEY")
ENDPOINT = os.getenv("AZURE_TEXT_ANALYTICS_ENDPOINT")

def authenticate_client():
    """Authenticate the client using credentials and endpoint."""
    return TextAnalyticsClient(endpoint=ENDPOINT, credential=AzureKeyCredential(KEY))

def sentiment_analysis_example(client):
    """Analyze sentiment for a given text."""
    input_text = "I had the best day of my life. I wish you were there with me."
    response = client.analyze_sentiment(documents=[input_text])[0]

    print(f"Document sentiment: {response.sentiment}\n")
    for sentence in response.sentences:
        print(f"\tText: \"{sentence.text}\"")
        print(f"\tSentence sentiment: {sentence.sentiment}")
        print(f"\tPositive score: {sentence.confidence_scores.positive:.2f}")
        print(f"\tNegative score: {sentence.confidence_scores.negative:.2f}")
        print(f"\tNeutral score: {sentence.confidence_scores.neutral:.2f}\n")

def language_detection_example(client):
    """Detect the language of a given text."""
    input_text = "Ce document est rédigé en Français."
    response = client.detect_language(documents=[input_text])[0]

    print("Language:")
    print(f"\t{response.primary_language.name}\tISO-6391: {response.primary_language.iso6391_name}\n")

if __name__ == "__main__":
    # Authenticate the client
    client = authenticate_client()

    # Perform sentiment analysis
    sentiment_analysis_example(client)

    # Perform language detection
    language_detection_example(client)
