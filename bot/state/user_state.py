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
        self.score: int = 0  # User's total score
        self.responses: int = 0  # Number of questions answered

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

    def update_score(self, points: int) -> None:
        """
        Update user score.
        :param points: Points to add to the user's total score
        """
        if points < 0:
            raise ValueError("Points cannot be negative")  # Ensure points are positive
        self.score += points
        self.responses += 1

    def get_final_score(self) -> int:
        """
        Calculate final score as a percentage.
        If no responses, return 0 to prevent division by zero.
        """
        return round(self.score / self.responses * 100) if self.responses > 0 else 0

    def reset_progress(self) -> None:
        """Reset the user's score and response count."""
        self.score = 0
        self.responses = 0

    def to_dict(self) -> dict:
        """Convert user state to a dictionary for easy saving/loading."""
        return {
            "user_id": self.user_id,
            "language": self.language,
            "proficiency_level": self.proficiency_level,
            "score": self.score,
            "responses": self.responses,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create a UserState object from a dictionary."""
        return cls(
            user_id=data.get("user_id", ""),
            language=data.get("language", "English"),
            proficiency_level=data.get("proficiency_level", "Beginner"),
        )
