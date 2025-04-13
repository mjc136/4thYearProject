from flask import Blueprint, jsonify, session
from backend.models import User
from backend.common import db

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/user/profile', methods=['GET'])
def get_user_profile():
    """Return the user's profile information for frontend use."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Map internal language codes to display names
    language_display = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'pt': 'Portuguese'
    }
    
    return jsonify({
        'username': user.username,
        'language': language_display.get(user.language, user.language),
        'proficiency': user.proficiency,
        'xp': user.xp,
        'level': user.level
    })
