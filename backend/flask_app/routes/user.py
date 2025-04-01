from flask import Blueprint, render_template, redirect, session, request, jsonify
from backend.models import User
import requests
import os

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

    if not message:
        return jsonify({"error": "Missing message"}), 400

    message = message.strip()
    if len(message) > 500:
        return jsonify({"error": "Message too long"}), 400

    try:
        bot_response = requests.post(
            f"{BOT_URL}/api/messages",
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
        return jsonify({
            "reply": data.get("bot_reply", ""),
            "attachments": data.get("attachments", [])
        })

    except requests.RequestException as e:
        print("[ERROR] Failed to contact bot:", e)
        return jsonify({"error": "Bot connection failed", "details": str(e)}), 502
