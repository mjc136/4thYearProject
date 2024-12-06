import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.shortcuts import render

def chat_view(request):
    return render(request, 'chat/index.html')  


@csrf_exempt
def chat_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message', '')

        # Send the message to the Rasa chatbot
        rasa_url = 'http://localhost:5005/webhooks/rest/webhook'  # Rasa webhook URL
        response = requests.post(rasa_url, json={"sender": "user", "message": user_message})

        # Extract the full list of bot responses
        bot_responses = response.json()  # This returns a list of messages

        # Send the responses back to the frontend
        return JsonResponse(bot_responses, safe=False)

