from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

BOT_ENDPOINT = "http://localhost:3978/api/messages"

@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/send", methods=["POST"])
def send():
    user_message = request.json.get("message", "")

    activity = {
        "type": "message",
        "from": {"id": "user", "name": "User"},
        "text": user_message,
        "recipient": {"id": "bot", "name": "LingoLizard"},
        "channelId": "flask",
        "conversation": {"id": "conv1"},
        "id": "msg1",
        "locale": "en-US",
        "serviceUrl": "http://localhost",
    }

    try:
        response = requests.post(BOT_ENDPOINT, json=activity)
        bot_reply = response.json().get("bot_reply", "No reply")
        return jsonify({"bot": bot_reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)
