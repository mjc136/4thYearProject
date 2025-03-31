from flask import session
from backend.models import User
from common import app  # Import the Flask app to use app context

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
            user = User.query.get(user_id)

            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            self.language: str = user.language
            self.proficiency_level: str = user.proficiency
            self.gender: str = "neutral"

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
