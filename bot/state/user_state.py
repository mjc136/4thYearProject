class UserState:
    """
    A class to manage user state in-memory using a shared dictionary.
    """
    # Shared dictionary to store all user data in memory
    user_data = {}

    def __init__(self, user_id):
        """
        Initialize a UserState object for a specific user.
        :param user_id: Unique identifier for the user
        """
        self.user_id = user_id
        self.language = None  # Current language the user is learning
        self.proficiency_level = None  # Beginner, Intermediate, Advanced

    def set_language(self, language):
        """Set the current language the user is learning."""
        self.language = language

    def set_proficiency_level(self, level):
        """Set the user's proficiency level."""
        self.proficiency_level = level
