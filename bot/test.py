import os
import uuid
import requests
import json
from dotenv import load_dotenv, dotenv_values

# Load environment variables from the .env file
load_dotenv()
        
# Get the Translator Text API key and endpoint from the .env file
config = dotenv_values(".env")
print(config)
TRANSLATOR_KEY = config["TRANSLATOR_KEY"]
TRANSLATOR_ENDPOINT = config["TRANSLATOR_ENDPOINT"]
TRANSLATOR_LOCATION = config["TRANSLATOR_LOCATION"]

path = '/translate?api-version=3.0'
params = '&to=de&to=it&to=ja'
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