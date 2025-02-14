import os
import uuid
import requests
import json
from dotenv import load_dotenv, dotenv_values
# Load environment variables from the .env file
load_dotenv()
        
# Load environment variables from a specific path
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bot', '.env')
load_dotenv(dotenv_path=env_path)

# Get translator settings from environment
TRANSLATOR_KEY = os.getenv("TRANSLATOR_KEY")
TRANSLATOR_ENDPOINT = os.getenv("TRANSLATOR_ENDPOINT")
TRANSLATOR_LOCATION = os.getenv("TRANSLATOR_LOCATION")

path = '/translate?api-version=3.0'
params = {
    'to': 'es'
}
constructed_url = TRANSLATOR_ENDPOINT + path
headers = {
    'Ocp-Apim-Subscription-Key': TRANSLATOR_KEY,
    # location required if you're using a multi-service or regional (not global) resource.
    'Ocp-Apim-Subscription-Region': TRANSLATOR_LOCATION,
    'Content-type': 'application/json',
    'X-ClientTraceId': str(uuid.uuid4())
}
# You can pass more than one object in body.
body = [{
    'text': 'I would really like to drive your car around the block a few times!'
}]
request = requests.post(constructed_url, params=params, headers=headers, json=body)
response = request.json()
print(json.dumps(response, sort_keys=True, ensure_ascii=False, indent=4, separators=(',', ': ')))