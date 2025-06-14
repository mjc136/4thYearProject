from backend.models import User
from backend.common import app  # Ensure this points to your actual Flask app (flask_app.flask_app)
import uuid
import logging
from backend.common import db
from typing import Optional, Any, List, Dict

# Configure logging
logger = logging.getLogger(__name__)

class UserProfile:
    def __init__(self):
        self.streak_count = 0
        self.last_activity_date = None
        self.highest_streak = 0

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
    
    def get_level(self) -> int:
        """
        Get the user's current level from the database.
        """
        try:
            with app.app_context():
                user = User.query.get(int(self.user_id))
                if user:
                    return user.level
                else:
                    logger.error(f"User with ID {self.user_id} not found when getting level")
                    return 1  # Default level
        except Exception as e:
            logger.error(f"Error getting level: {str(e)}")
            return 1  # Default level

    def calculate_level(self, xp: int) -> int:
        """
        Calculate what level a user should be based on their XP.
        You can customize the XP thresholds for each level here.
        
        Basic formula: level = 1 + floor(sqrt(xp / 100))
        This means:
        - Level 1: 0-99 XP
        - Level 2: 100-399 XP
        - Level 3: 400-899 XP
        - Level 4: 900-1599 XP
        And so on...
        """
        import math
        return 1 + math.floor(math.sqrt(xp / 100))

    def update_xp(self, xp: int) -> int:
        """
        Update the user's XP in the database and handle level ups.
        Adds the provided XP amount to the user's total.
        
        Returns:
            int: The new total XP
        """
        try:
            with app.app_context():
                user = User.query.get(int(self.user_id))
                if user:
                    # Store old level to check for level up
                    old_level = user.level
                    
                    # Update XP
                    old_xp = user.xp or 0
                    new_xp = old_xp + xp
                    user.xp = new_xp
                    self.xp = new_xp  # Update local state too
                    
                    # Calculate and update level if needed
                    new_level = self.calculate_level(new_xp)
                    if new_level > old_level:
                        user.level = new_level
                        logger.info(f"User {self.user_id} leveled up to {new_level}!")
                    
                    db.session.commit()
                    logger.info(f"Updated XP for user {self.user_id}: {old_xp} -> {new_xp}")
                    return new_xp
                else:
                    logger.error(f"User with ID {self.user_id} not found for XP update")
                    return 0
        except Exception as e:
            logger.error(f"Error updating XP: {str(e)}")
            return 0

    def update_score(self, score: int) -> None:
        """
        Update the user's scenario score.
        This is an alias for update_xp for backward compatibility.
        """
        self.update_xp(score)

    def calculate_level_progress(self, xp: int = None) -> int:
        """
        Calculate the percentage progress within the current level.
        Returns a value from 0-100 representing current level progress.
        """
        if xp is None:
            xp = self.xp
            
        current_level = self.calculate_level(xp)
        
        # Calculate XP thresholds for current and next level
        xp_for_current_level = 100 * (current_level - 1) ** 2
        xp_for_next_level = 100 * current_level ** 2
        
        # Calculate progress percentage within current level
        if xp_for_next_level == xp_for_current_level:  # Edge case
            return 100
            
        progress = ((xp - xp_for_current_level) / 
                   (xp_for_next_level - xp_for_current_level)) * 100
        
        return int(progress)
        
    def get_streak_info(self) -> dict:
        """
        Get the user's streak information.
        """
        try:
            with app.app_context():
                user = User.query.get(int(self.user_id))
                if user:
                    return {
                        "streak_count": user.streak_count if hasattr(user, 'streak_count') else 0,
                        "highest_streak": user.highest_streak if hasattr(user, 'highest_streak') else 0,
                        "last_activity_date": user.last_activity_date
                    }
                else:
                    logger.error(f"User with ID {self.user_id} not found when getting streak info")
                    return {"streak_count": 0, "highest_streak": 0, "last_activity_date": None}
        except Exception as e:
            logger.error(f"Error getting streak info: {str(e)}")
            return {"streak_count": 0, "highest_streak": 0, "last_activity_date": None}
            
    def update_streak(self) -> dict:
        """
        Update the user's streak based on their last activity date.
        Returns the updated streak information.
        """
        from datetime import datetime, timedelta
        
        try:
            with app.app_context():
                user = User.query.get(int(self.user_id))
                if not user:
                    logger.error(f"User with ID {self.user_id} not found for streak update")
                    return {"streak_count": 0, "highest_streak": 0}
                
                current_date = datetime.now().date()
                
                # Initialize streak fields if they don't exist
                if not hasattr(user, 'streak_count'):
                    user.streak_count = 0
                
                if not hasattr(user, 'highest_streak'):
                    user.highest_streak = 0
                    
                if not hasattr(user, 'last_activity_date'):
                    user.last_activity_date = None
                
                # If this is the first activity ever
                if user.last_activity_date is None:
                    user.streak_count = 1
                    user.highest_streak = 1
                    user.last_activity_date = current_date
                    db.session.commit()
                    return {"streak_count": 1, "highest_streak": 1}
                
                # Get the last activity date
                last_date = user.last_activity_date
                
                # If it's the same day, don't update streak
                if current_date == last_date:
                    return {
                        "streak_count": user.streak_count,
                        "highest_streak": user.highest_streak
                    }
                    
                # If it's the next day, increment streak
                if current_date == last_date + timedelta(days=1):
                    user.streak_count += 1
                    # Update highest streak if current streak is higher
                    if user.streak_count > user.highest_streak:
                        user.highest_streak = user.streak_count
                # If more than one day has passed, reset streak
                elif current_date > last_date + timedelta(days=1):
                    user.streak_count = 1
                
                # Update the last activity date to today
                user.last_activity_date = current_date
                db.session.commit()
                
                return {
                    "streak_count": user.streak_count,
                    "highest_streak": user.highest_streak
                }
                
        except Exception as e:
            logger.error(f"Error updating streak: {str(e)}")
            return {"streak_count": 0, "highest_streak": 0}
