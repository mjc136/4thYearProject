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
        valid_levels = ["beginner", "intermediate", "advanced"]
        if level.lower() in valid_levels:
            self.proficiency_level = level.capitalize()
        else:
            raise ValueError("Invalid proficiency level. Choose Beginner, Intermediate, or Advanced.")

    def is_language_and_proficiency_set(self):
        """Check if both language and proficiency are set."""
        return self.language is not None and self.proficiency_level is not None