class UserState:
    def __init__(self):
        # Language proficiency attributes
        self.language = None  # Current language the user is learning
        self.proficiency_level = None  # Beginner, Intermediate, Advanced

    def set_language(self, language):
        """Set the current language the user is learning."""
        self.language = language

    def set_proficiency_level(self, level):
        """Set the user's proficiency level."""
        if level in ["Beginner", "Intermediate", "Advanced"]:
            self.proficiency_level = level
        else:
            raise ValueError("Invalid proficiency level. Choose Beginner, Intermediate, or Advanced.")
