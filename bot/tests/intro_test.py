import pytest
from unittest.mock import MagicMock
from botbuilder.core import MemoryStorage, ConversationState, TurnContext
from botbuilder.dialogs import DialogSet
from botbuilder.dialogs.prompts import TextPrompt
from dialogs.main_dialog import MainDialog
from state.user_state import UserState

@pytest.mark.asyncio
async def test_main_dialog():
    # Setup memory and conversation state
    memory = MemoryStorage()
    conversation_state = ConversationState(memory)
    dialog_state = conversation_state.create_property("DialogState")

    # Create UserState instance for testing
    user_state = UserState()

    # Create the DialogSet and add dialogs
    dialogs = DialogSet(dialog_state)
    dialogs.add(TextPrompt("text_prompt"))
    dialogs.add(MainDialog(user_state))  # Pass UserState to MainDialog

    # Mock TurnContext
    turn_context = MagicMock(spec=TurnContext)
    turn_context.activity = MagicMock()
    turn_context.turn_state = {"DialogState": dialog_state}  # Ensure consistent dialog state

    # Create DialogContext
    dialog_context = await dialogs.create_context(turn_context)

    # Step 1: Intro step
    turn_context.activity.text = None
    await dialog_context.begin_dialog("MainDialog")
    assert dialog_context.active_dialog is not None

    # Step 2: Language step
    turn_context.activity.text = "Spanish"
    await dialog_context.continue_dialog()
    assert user_state.language == "Spanish"  # Validate language is set

    # Step 3: Proficiency step
    turn_context.activity.text = "Intermediate"
    await dialog_context.continue_dialog()
    assert user_state.proficiency_level == "Intermediate"

    # Step 4: Final step
    results = await dialog_context.continue_dialog()
    assert results.status.name == "Complete"

    # Validate final state
    assert user_state.language == "Spanish"
    assert user_state.proficiency_level == "Intermediate"




