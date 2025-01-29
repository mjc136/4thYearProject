import os
from dotenv import load_dotenv
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

def test_text_analytics():
    # Load environment variables
    load_dotenv()
    
    # Get credentials
    key = os.getenv("TEXT_ANALYTICS_KEY")
    endpoint = os.getenv("TEXT_ANALYTICS_ENDPOINT")
    
    if not all([key, endpoint]):
        print("Environment variables not found. Please check your .env file")
        print(f"KEY: {'Found' if key else 'Missing'}")
        print(f"ENDPOINT: {'Found' if endpoint else 'Missing'}")
        return
    
    try:
        # Initialize client
        credential = AzureKeyCredential(key)
        client = TextAnalyticsClient(endpoint=endpoint, credential=credential)
        
        # Test documents
        documents = [
            "my name is bob and I am a software engineer at Microsoft.",
            "I am learning how to speak French.",
            "i wanna go home.",
            "minha casa é muito bonita.",
        ]
        
        # Analyze entities
        print("Analyzing text...")
        response = client.recognize_entities(documents)
        
        # Process results
        for idx, doc in enumerate(response):
            print(f"\nDocument {idx + 1} entities:")
            for entity in doc.entities:
                print(f"- {entity.text} ({entity.category}): {entity.confidence_score:.2f}")
                
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print("Check your Azure credentials and network connection")

if __name__ == "__main__":
    test_text_analytics()