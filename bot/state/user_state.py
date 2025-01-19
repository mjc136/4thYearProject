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

    def save_state(self):
        """
        Save the current user's state in memory.
        """
        UserState.user_data[self.user_id] = {
            "language": self.language,
            "proficiency_level": self.proficiency_level
        }
        print(f"State saved for user {self.user_id}: {UserState.user_data[self.user_id]}")

    def load_state(self):
        """
        Load the user's state from memory if it exists.
        """
        if self.user_id in UserState.user_data:
            data = UserState.user_data[self.user_id]
            self.language = data.get("language")
            self.proficiency_level = data.get("proficiency_level")
            print(f"State loaded for user {self.user_id}: {data}")
        else:
            print(f"No state found for user {self.user_id}. Starting fresh.")

    def clear_state(self):
        """
        Clear the user's state from memory.
        """
        if self.user_id in UserState.user_data:
            del UserState.user_data[self.user_id]
            print(f"State cleared for user {self.user_id}")
        else:
            print(f"No state to clear for user {self.user_id}")

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
