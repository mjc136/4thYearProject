from flask import Blueprint, render_template, redirect, session, request, jsonify
from models import User
import requests
import os
import logging
import time

user_bp = Blueprint("user", __name__, template_folder="templates")
BOT_URL = os.getenv("BOT_URL", "http://localhost:3978")

@user_bp.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")
    user = User.query.get(session["user_id"])
    return render_template("profile.html", user=user)

@user_bp.route("/chat")
def chat():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("chat.html")

@user_bp.route("/send", methods=["POST"])
def send_message():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]
    message = request.json.get("message")

    # Special trigger to auto-start conversation (sends blank to bot)
    if message == "__start__":
        message = ""

    if message is None:
        return jsonify({"error": "Missing message"}), 400

    message = message.strip()
    if len(message) > 500:
        return jsonify({"error": "Message too long"}), 400

    # Set up retry mechanism
    max_retries = 3
    retry_count = 0
    while retry_count < max_retries:
        try:
            logging.info(f"Sending message to bot service for user {user_id}: {message[:50]}...")
            
            # Get the bot URL from environment, ensure it points to the correct endpoint
            bot_url = os.getenv("BOT_URL", "http://localhost:3978/api/messages")
            
            # If BOT_URL doesn't end with /api/messages, append it
            if not bot_url.endswith("/api/messages"):
                bot_url = f"{bot_url.rstrip('/')}/api/messages"
                
            logging.info(f"Using bot URL: {bot_url}")
            
            bot_response = requests.post(
                bot_url,
                headers={
                    "Content-Type": "application/json",
                    "X-User-ID": str(user_id)
                },
                json={
                    "type": "message",
                    "text": message
                },
                timeout=15
            )
            
            bot_response.raise_for_status()
            data = bot_response.json()
            
            if not data.get("reply"):
                logging.warning(f"Bot returned empty response for user {user_id}")
                if retry_count < max_retries - 1:
                    retry_count += 1
                    time.sleep(1)  # Wait before retrying
                    continue
                else:
                    # If we've exhausted our retries and still have no reply, return a friendly message
                    return jsonify({
                        "reply": "I'm having trouble understanding. Let me try again...",
                        "attachments": []
                    })
            
            # Success - return the response
            return jsonify({
                "reply": data.get("reply", ""),
                "attachments": data.get("attachments", [])
            })

        except requests.RequestException as e:
            logging.error(f"Failed to contact bot service (attempt {retry_count+1}/{max_retries}): {e}")
            if retry_count < max_retries - 1:
                retry_count += 1
                time.sleep(1)  # Wait before retrying
            else:
                # We've exhausted our retries
                return jsonify({
                    "error": "Bot service unavailable", 
                    "reply": "I'm currently unavailable. Please try again in a moment."
                }), 503

