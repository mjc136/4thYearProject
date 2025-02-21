class UserState:
    """
    A class to manage user state in-memory using a shared dictionary.
    """

    def __init__(self, user_id):
        """
        Initialize a UserState object for a specific user.
        :param user_id: Unique identifier for the user
        """
        self.user_id = user_id
        self.language = None  # Current language the user is learning
        self.proficiency_level = None  # Beginner, Intermediate, Advanced
        self.score = 0 # User's total score
        self.responses = 0  # Number of questions answered

    def set_language(self, language):
        """Set the current language the user is learning."""
        self.language = language

    def set_proficiency_level(self, level):
        """Set the user's proficiency level."""
        self.proficiency_level = level

    def update_score(self, points):
        """Update user score."""
        self.score += points
        self.responses += 1

    def get_final_score(self):
        """Calculate final score."""
        if self.responses == 0:
            return 0
        return round(self.score / self.responses * 100)  # Convert to percentage
