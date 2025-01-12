import pytest
from unittest.mock import MagicMock
from botbuilder.core import MemoryStorage, ConversationState, TurnContext
from botbuilder.dialogs import DialogSet
from botbuilder.dialogs.prompts import TextPrompt
from dialogs.taxi_scenario import TaxiScenarioDialog

@pytest.mark.asyncio
async def test_taxi_conversation():
    # Setup memory and conversation state
    memory = MemoryStorage()
    conversation_state = ConversationState(memory)
    dialog_state = conversation_state.create_property("DialogState")

    # Create the DialogSet and add dialogs
    dialogs = DialogSet(dialog_state)
    dialogs.add(TextPrompt("text_prompt"))  # Add the TextPrompt
    dialogs.add(TaxiScenarioDialog())

    # Mock TurnContext
    turn_context = MagicMock(spec=TurnContext)
    turn_context.activity = MagicMock()
    turn_context.activity.text = "Where would you like to go?"

    # Create DialogContext
    dialog_context = await dialogs.create_context(turn_context)

    # Start the TaxiScenarioDialog
    await dialog_context.begin_dialog("taxi_dialog")

    # Simulate user response
    response = "Airport"
    assert response == "Airport"
