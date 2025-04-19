from flask import session
from backend.models import User
from backend.common import app  # Ensure this points to your actual Flask app (flask_app.flask_app)
import uuid

class UserState:
    """
    A class to manage user state using user data from the database.
    """

    def __init__(self, user_id: str):
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
            self.gender: str = "neutral"
            self.active_dialog = None
            self.final_score = 0
            self.new_conversation = True

            # Initialize conversation history
            self.conversation_history = []
            
            # Generate a unique conversation ID for KV cache tracking
            self.conversation_id = str(uuid.uuid4())
            print(f"[DEBUG] Initialized new conversation with ID: {self.conversation_id}")

    def get_language(self) -> str:
        return self.language

    def set_active_dialog(self, dialog_id: str):
        """Store the active dialog ID."""
        self._active_dialog = dialog_id

    def get_active_dialog(self) -> str:
        """Get the currently active dialog ID."""
        return getattr(self, '_active_dialog', None)

    def get_new_conversation(self):
        """Get whether this is a new conversation."""
        return getattr(self, 'new_conversation', True)
        
    def set_new_conversation(self, new_conversation):
        """Set whether this is a new conversation."""
        self.new_conversation = new_conversation

    def get_conversation_history(self):
        """Get the conversation history."""
        return getattr(self, 'conversation_history', [])
        
    def set_conversation_history(self, history):
        """Set the conversation history."""
        self.conversation_history = history
        
    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history = []

    def get_conversation_id(self) -> str:
        """
        Get the current conversation ID used for DeepSeek's KV Cache.
        """
        return getattr(self, 'conversation_id', None)
    
    def reset_conversation_id(self) -> str:
        """
        Generate a new conversation ID and return it.
        This should be called when you want to start a fresh conversation context.
        """
        old_id = getattr(self, 'conversation_id', None)
        self.conversation_id = str(uuid.uuid4())
        print(f"[DEBUG] Reset conversation ID: {old_id} -> {self.conversation_id}")
        
        # Also clear the conversation history when resetting the ID
        self.clear_conversation_history()
        
        return self.conversation_id
