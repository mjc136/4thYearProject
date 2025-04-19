from flask import session
from backend.models import User
from backend.common import app  # Ensure this points to your actual Flask app (flask_app.flask_app)
import uuid
import logging
from backend.common import db
from typing import Optional, Any, List, Dict

# Configure logging
logger = logging.getLogger(__name__)

class UserState:
    """
    A class to manage user state using user data from the database.
    Provides methods to track conversation state, dialog context, and user progress.
    """

    def __init__(self, user_id: str):
        """
        Initialize a UserState object using user record from DB.
        Sets up conversation tracking, dialog state, and user information.
        """
        self.user_id: str = user_id

        # Ensure we're inside Flask app context
        with app.app_context():
            logger.debug(f"Looking for user ID {user_id}")
            try:
                user = User.query.get(int(user_id))  # Ensure ID is int
            except Exception as e:
                logger.error(f"Invalid user ID '{user_id}': {e}")
                raise ValueError(f"[ERROR] Invalid user ID '{user_id}': {e}")

            if not user:
                logger.error(f"User with ID {user_id} not found")
                raise ValueError(f"User with ID {user_id} not found")

            # User attributes
            self.language: str = user.language
            self.gender: str = "neutral"
            self.xp: int = user.xp if hasattr(user, 'xp') else 0
            
            # Dialog tracking
            self._active_dialog = None
            self.final_score = 0
            self.dialog_state = {}  # Store dialog-specific state
            
            # Conversation tracking
            self.new_conversation = True
            self.conversation_history: List[Dict[str, str]] = []
            
            # Generate a unique conversation ID for KV cache tracking
            self.conversation_id = str(uuid.uuid4())
            logger.debug(f"Initialized new conversation with ID: {self.conversation_id}")

    def get_language(self) -> str:
        """Get the user's preferred language."""
        return self.language

    def set_active_dialog(self, dialog_id: str) -> None:
        """
        Store the active dialog ID and ensure dialog state exists.
        This helps maintain context between dialog turns.
        """
        self._active_dialog = dialog_id
        # Initialize dialog state if it doesn't exist
        if dialog_id and dialog_id not in self.dialog_state:
            self.dialog_state[dialog_id] = {}
        logger.debug(f"Set active dialog to: {dialog_id}")

    def get_active_dialog(self) -> Optional[str]:
        """Get the currently active dialog ID."""
        return self._active_dialog

    def get_dialog_state(self, key: str = None, dialog_id: str = None) -> Any:
        """
        Get state specific to the current or specified dialog.
        This helps maintain context between dialog turns.
        
        Args:
            key: Optional specific state key to retrieve
            dialog_id: Optional dialog ID, defaults to active dialog
        """
        if not dialog_id:
            dialog_id = self.get_active_dialog()
            
        if not dialog_id or dialog_id not in self.dialog_state:
            return None
            
        if key:
            return self.dialog_state[dialog_id].get(key)
        return self.dialog_state[dialog_id]

    def set_dialog_state(self, key: str, value: Any, dialog_id: str = None) -> None:
        """
        Set state specific to the current or specified dialog.
        
        Args:
            key: State key to set
            value: Value to store
            dialog_id: Optional dialog ID, defaults to active dialog
        """
        if not dialog_id:
            dialog_id = self.get_active_dialog()
            
        if not dialog_id:
            logger.warning("Attempted to set dialog state without active dialog")
            return
            
        if dialog_id not in self.dialog_state:
            self.dialog_state[dialog_id] = {}
            
        self.dialog_state[dialog_id][key] = value
        logger.debug(f"Set dialog state {key}={value} for dialog {dialog_id}")

    def get_new_conversation(self) -> bool:
        """Get whether this is a new conversation."""
        return self.new_conversation
        
    def set_new_conversation(self, new_conversation: bool) -> None:
        """Set whether this is a new conversation."""
        self.new_conversation = new_conversation

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history."""
        return self.conversation_history
        
    def set_conversation_history(self, history: List[Dict[str, str]]) -> None:
        """Set the conversation history."""
        self.conversation_history = history
        
    def clear_conversation_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
        logger.debug("Conversation history cleared")

    def get_conversation_id(self) -> str:
        """
        Get the current conversation ID used for DeepSeek's KV Cache.
        """
        return self.conversation_id
    
    def reset_conversation_id(self) -> str:
        """
        Generate a new conversation ID and return it.
        This should be called when you want to start a fresh conversation context.
        """
        old_id = self.conversation_id
        self.conversation_id = str(uuid.uuid4())
        logger.debug(f"Reset conversation ID: {old_id} -> {self.conversation_id}")
        
        # Also clear the conversation history when resetting the ID
        self.clear_conversation_history()
        
        return self.conversation_id
    
    def update_xp(self, xp: int) -> None:
        """
        Update the user's XP in the database.
        Adds the provided XP amount to the user's total.
        """
        try:
            with app.app_context():
                user = User.query.get(int(self.user_id))
                if user:
                    user.xp = (user.xp or 0) + xp  # Handle None value
                    self.xp = user.xp  # Update local state too
                    db.session.commit()
                    logger.info(f"Updated XP for user {self.user_id}: {user.xp}")
                else:
                    logger.error(f"User with ID {self.user_id} not found for XP update")
        except Exception as e:
            logger.error(f"Error updating XP: {str(e)}")
    
    def update_score(self, score: int) -> None:
        """
        Update the user's scenario score.
        This is an alias for update_xp for backward compatibility.
        """
        self.update_xp(score)
