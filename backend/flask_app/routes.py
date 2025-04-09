# Add this code to your routes.py file if it doesn't already exist or modify it accordingly

from flask import request, jsonify, session
import requests
import json
import os
import logging

from . import app

@app.route('/send', methods=['POST'])
def send_message():
    try:
        user_id = session.get('user_id', 'anonymous')
        data = request.json
        message = data.get('message')
        
        if not message:
            return jsonify({"error": "No message provided"}), 400
        
        # Send to bot framework endpoint
        bot_url = os.getenv('BOT_URL', 'http://localhost:3978/api/messages')
        headers = {
            'Content-Type': 'application/json',
            'X-User-ID': user_id
        }
        
        response = requests.post(
            bot_url,
            headers=headers,
            json={'text': message}
        )
        
        if response.status_code != 200:
            logging.error(f"Bot API error: {response.text}")
            return jsonify({"error": "Failed to communicate with bot service"}), 500
        
        bot_response = response.json()
        return jsonify(bot_response)
        
    except Exception as e:
        logging.exception("Error in send_message endpoint")
        return jsonify({"error": str(e)}), 500
