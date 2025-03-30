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
        self.language: str = language  # Default to English
        self.proficiency_level: str = proficiency_level  # Default to Beginner
        self.gender: str = "neutral"

    def set_language(self, language: str) -> None:
        """Set the current language the user is learning."""
        self.language = language

    def get_language(self) -> str:
        """Get the current language the user is learning."""
        return self.language
    
    def set_proficiency_level(self, level: str) -> None:
        """Set the user's proficiency level."""
        self.proficiency_level = level

    def get_proficiency_level(self) -> str:
        """Get the user's proficiency level."""
        return self.proficiency_level
