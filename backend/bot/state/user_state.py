from flask import session
from models import User
from common import app  # Ensure this points to your actual Flask app (flask_app.flask_app)

class UserState:
    """
    A class to manage user state using user data from the database.
    """

    def __init__(self, user_id: str, language: str = "en", proficiency_level: str = "Beginner"):
        """
        Initialise a UserState object using user record from DB.
        """
        self.user_id: str = user_id

        # Ensure we're inside Flask app context
        with app.app_context():
            print(f"[DEBUG] Looking for user ID {user_id}")
            try:
                user = User.query.get(int(user_id))  # Ensure ID is int
            except Exception as e:
                raise ValueError(f"[ERROR] Invalid user ID '{user_id}': {e}")

            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            self.language: str = user.language
            self.proficiency_level: str = user.proficiency
            self.gender: str = "neutral"
            self.active_dialog = None
            self.final_score = 0
            self.new_conversation = True  # Add this line

    def get_language(self) -> str:
        return self.language

    def get_proficiency_level(self) -> str:
        return self.proficiency_level

    def get_gender(self) -> str:
        return self.gender

    def set_active_dialog(self, dialog_id: str):
        """Store the active dialog ID."""
        self._active_dialog = dialog_id

    def get_active_dialog(self) -> str:
        """Get the currently active dialog ID."""
        return getattr(self, '_active_dialog', None)

    def get_new_conversation(self):
        """Get whether this is a new conversation."""
        return self.new_conversation
        
    def set_new_conversation(self, new_conversation):
        """Set whether this is a new conversation."""
        self.new_conversation = new_conversation
