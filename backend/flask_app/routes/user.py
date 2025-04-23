from flask import Blueprint, render_template, redirect, session, request, jsonify
from backend.models import User, UserScenarioProgress
import requests
import os
import logging
import time
import traceback

user_bp = Blueprint("user", __name__, template_folder="templates")
BOT_URL = os.getenv("BOT_URL", "http://localhost:3978")

@user_bp.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")
        
    user = User.query.get(session["user_id"])
    
    # Calculate level progress
    from backend.bot.state.user_state import UserState
    user_state = UserState(str(user.id))
    user.level_progress = user_state.calculate_level_progress(user.xp)
    
    # Get streak info if available
    streak_info = user_state.get_streak_info()
    user.streak_count = streak_info.get("streak_count", 0)
    user.highest_streak = streak_info.get("highest_streak", 0)
    
    return render_template("profile.html", user=user)

@user_bp.route("/scenarios")
def scenarios():
    """Render scenarios based on user proficiency and progress."""
    if "user_id" not in session:
        return redirect("/login")
    user = User.query.get(session["user_id"])
    
    # Define scenario tiers for progression tracking
    scenario_tiers = {
        'beginner': ['taxi', 'restaurant', 'shopping'],
        'intermediate': ['hotel', 'doctor'],
        'advanced': ['interview']
    }

    # Get completed scenarios from DB
    completed = [
        p.scenario_name for p in user.scenario_progress if p.completed
    ]

    # Determine unlocked scenarios
    if user.admin:  
        # Admins can access everything
        unlocked = [s for tier in scenario_tiers.values() for s in tier]
    else:
        unlocked = scenario_tiers['beginner'].copy()

        if all(s in completed for s in scenario_tiers['beginner']):
            unlocked += scenario_tiers['intermediate']

            if all(s in completed for s in scenario_tiers['intermediate']):
                unlocked += scenario_tiers['advanced']

    # Attach dynamic lists to the user object for the template
    user.completed_scenarios = completed
    user.unlocked_scenarios = unlocked

    return render_template("scenarios.html", user=user, scenario_tiers=scenario_tiers)

@user_bp.route("/chat")
def chat():
    """Render chat interface with custom welcome message."""
    if "user_id" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user_id"])
    
    # Get scenario from query params or use default based on proficiency
    scenario = request.args.get("scenario", "")
    if not scenario:
        proficiency = user.proficiency or "beginner"
        if proficiency == "beginner":
            scenario = "taxi"
        elif proficiency == "intermediate":
            scenario = "hotel"
        else:
            scenario = "interview"
    
    # Define scenario info dictionary
    scenario_info = {
        'taxi': {
            'title': 'Taxi Ride',
            'intro': 'Imagine you just entered a taxi. You need to communicate with the driver to get to your destination.',
            'tier': 'Beginner',
            'badge': 'success'
        },
        'restaurant': {
            'title': 'Restaurant Order',
            'intro': 'You\'re at a local restaurant and need to order food and drinks.',
            'tier': 'Beginner',
            'badge': 'success'
        },
        'shopping': {
            'title': 'Shopping',
            'intro': 'You\'re at a clothing store and want to buy some new clothes.',
            'tier': 'Beginner',
            'badge': 'success'
        },
        'hotel': {
            'title': 'Hotel Booking',
            'intro': 'Imagine you are at a hotel reception. You need to book a room and discuss accommodations with the staff.',
            'tier': 'Intermediate',
            'badge': 'warning'
        },
        'doctor': {
            'title': 'Doctor\'s Visit',
            'intro': 'You\'re visiting a doctor and need to explain your symptoms and understand medical advice.',
            'tier': 'Intermediate',
            'badge': 'warning'
        },
        'interview': {
            'title': 'Job Interview',
            'intro': 'Imagine you are attending a job interview. You need to showcase your skills and experience to make a good impression.',
            'tier': 'Advanced',
            'badge': 'danger'
        }
    }
    
    # Update the user's settings for the bot to use
    language = user.language
    
    # Map language codes to display names
    language_map = {
        "es": "Spanish",
        "fr": "French", 
        "pt": "Portuguese"
    }
    
    # Get current scenario info
    current_scenario = scenario_info[scenario]
    
    return render_template(
        "chat.html", 
        user=user,
        scenario=scenario,
        scenario_title=current_scenario['title'],
        scenario_intro=current_scenario['intro'],
        scenario_tier=current_scenario['tier'],
        scenario_badge=current_scenario['badge'],
        language=language,
        language_display=language_map.get(language, "Spanish"),
    )

@user_bp.route("/send", methods=["POST"])
def send_message():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]
    message = request.json.get("message")
    scenario = request.json.get("scenario")  # Get scenario from request JSON

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
            logging.info(f"Sending message to bot service for user {user_id}: {message[:50]}... (Scenario: {scenario})")
            
            # Get the bot URL from environment, ensure it points to the correct endpoint
            bot_url = os.getenv("BOT_URL", "http://localhost:3978/api/messages")
            
            # If BOT_URL doesn't end with /api/messages, append it
            if not bot_url.endswith("/api/messages"):
                bot_url = f"{bot_url.rstrip('/')}/api/messages"
                
            logging.info(f"Using bot URL: {bot_url}")
            
            # Include the scenario in headers
            headers = {
                "Content-Type": "application/json",
                "X-User-ID": str(user_id)
            }
            
            # Only add X-Scenario header if scenario is present
            if scenario:
                headers["X-Scenario"] = scenario
                logging.info(f"Added X-Scenario header: {scenario}")
            
            bot_response = requests.post(
                bot_url,
                headers=headers,
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
