from flask import session
from backend.models import User

class UserState:
    """
    A class to manage user state in-memory using a shared dictionary.
    """

    def __init__(self, user_id: str, language: str = "en", proficiency_level: str = "Beginner"):
        """
        Initialise a UserState object for a specific user.
        :param user_id: Unique identifier for the user
        :param language: Default language the user is learning
        :param proficiency_level: Default proficiency level (Beginner, Intermediate, Advanced)
        """
        self.user_id: str = user_id
        user = User.query.get(user_id)

        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        self.language: str = user.language
        self.proficiency_level: str = user.proficiency
        self.gender: str = "neutral"

    def get_language(self) -> str:
        """Get the current language the user is learning."""
        return self.language

    def get_proficiency_level(self) -> str:
        """Get the user's proficiency level."""
        return self.proficiency_level
    
    def get_gender(self) -> str:
        """Get current user gender"""
        return self.gender
