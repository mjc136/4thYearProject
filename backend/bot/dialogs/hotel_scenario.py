from botbuilder.dialogs import (
    WaterfallDialog, WaterfallStepContext, DialogTurnResult, 
    PromptOptions, TextPrompt, ChoicePrompt, DateTimePrompt,
    NumberPrompt, ConfirmPrompt, DialogTurnStatus
)
from botbuilder.core import MessageFactory
from botbuilder.schema import ActivityTypes, Activity
from .base_dialog import BaseDialog
from backend.bot.state.user_state import UserState
import re

class HotelScenarioDialog(BaseDialog):
    def __init__(self, user_state: UserState):
        super().__init__("HotelScenarioDialog", user_state)
        self.user_state = user_state
        self.language = self.user_state.get_language()

        # User's booking information
        self.check_in_date = None
        self.num_nights = None
        self.room_type = None
        self.num_guests = None
        self.special_requests = None
        self.payment_method = None
        self.score = 0
        
        # Scoring flags - adding like in taxi scenario
        self.dates_provided = False
        self.room_type_specified = False
        self.guests_provided = False
        self.special_requests_provided = False
        self.booking_confirmed = False
        self.payment_method_provided = False
        self.messages = []
        
        # persona
        self.receptionist_persona = (
            "You are a hotel receptionist. Stay in character throughout the conversation. "
            "Politely greet the guest and ask about their booking or needs. "
            "Only offer information about room types, check-in, check-out, and amenities. "
            "Do not ask for real names or IDs. Keep replies short and easy to understand, using basic vocabulary for learners."
        )
        
        # Add different prompt types for better guidance
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(ChoicePrompt("room_type_prompt"))
        self.add_dialog(NumberPrompt("guests_prompt", self.verify_guest_count))
        self.add_dialog(ConfirmPrompt("confirm_prompt"))
        
        self.add_dialog(
            WaterfallDialog(
                "HotelScenarioDialog.waterfall",
                [
                    self.initial_receptionist_greeting,
                    self.ask_length_of_stay,
                    self.process_stay_duration,
                    self.handle_room_selection,
                    self.process_guest_count,
                    self.handle_special_requests,
                    self.verify_booking_details,
                    self.collect_payment_method,
                    self.finalize_reservation,
                    self.show_performance_feedback,
                    self.end_booking_scenario
                ]
            )
        )
        self.initial_dialog_id = "HotelScenarioDialog.waterfall"

    async def initial_receptionist_greeting(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Step One of Six: Initial greeting"))
        prompt = await self.chatbot_respond(
            step_context.context,
            "start",
            f"{self.receptionist_persona} Politely greet the guest and ask how you can help."
        )
        
        guidance = "Respond as if you're a guest inquiring about booking a room."
        example = self.translate_text(
            "Example: Hello! I'd like to book a room.", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def ask_length_of_stay(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Step Two of Six: Checking availability"))
        user_input = step_context.result
        feedback = await self.check_spelling_grammar(user_input)
        await step_context.context.send_activity(MessageFactory.text(feedback))
        
        prompt = await self.chatbot_respond(
            step_context.context,
            user_input,
            f"{self.receptionist_persona} Ask how many nights they would like to stay, assuming they're checking in today."
        )
        
        guidance = "The receptionist is asking about your stay duration. Tell them how many nights you'd like to stay."
        example = self.translate_text(
            "Example: I'd like to stay for 3 nights, please.", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def process_stay_duration(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Step Two of Six: Providing stay duration"))
        user_input = step_context.result
        feedback = await self.check_spelling_grammar(user_input)
        await step_context.context.send_activity(MessageFactory.text(feedback))
        
        self.check_in_date = "Today"
        
        # Use AI to extract the number of nights
        self.num_nights = await self.extract_nights_with_ai(step_context.context, user_input)
        
        # Store flag in step_context.values
        step_context.values["dates_provided"] = True
        
        # Calculate check-out description
        check_out_description = f"After {self.num_nights} nights" if self.num_nights else "Not specified"
        
        # Display what we understood from the dates
        dates_confirmation = (
            "I understand you want to book a room with these dates:\n"
            f"Check-in: Today\n"
            f"Check-out: {check_out_description}"
        )
        await step_context.context.send_activity(MessageFactory.text(dates_confirmation))
        
        prompt = await self.chatbot_respond(
            step_context.context,
            "dates provided",
            f"{self.receptionist_persona} Ask for preferred room type."
        )
        
        guidance = "The receptionist is asking about room preferences. Tell them what type of room you'd like."
        example = self.translate_text(
            "Example: I'd like a deluxe room with a king-sized bed, please.", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def handle_room_selection(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Step Three of Six: Selecting room type"))
        user_input = step_context.result
        feedback = await self.check_spelling_grammar(user_input)
        await step_context.context.send_activity(MessageFactory.text(feedback))
        
        self.room_type = user_input
        
        # Store flag in step_context.values
        step_context.values["room_type_specified"] = True
        
        prompt = await self.chatbot_respond(
            step_context.context,
            user_input,
            f"{self.receptionist_persona} Ask how many guests will stay."
        )
        
        guidance = "The receptionist wants to know how many people will be staying in the room."
        example = self.translate_text(
            "Example: There will be two adults and one child.", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text(prompt))
        )
    
    async def process_guest_count(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Captures the number of guests for the hotel booking."""
        await step_context.context.send_activity(MessageFactory.text("Step Three of Six: Specifying number of guests"))
        
        user_input = step_context.result
        feedback = await self.check_spelling_grammar(user_input)
        await step_context.context.send_activity(MessageFactory.text(feedback))
        
        self.num_guests = user_input
        
        # Add to conversation memory
        self.add_to_memory(f"User specified guests: {user_input}", "Bot asked about special requests")
        
        # Update success tracking flags
        self.guests_provided = True
        step_context.values["guests_provided"] = True
        
        prompt = await self.chatbot_respond(
            step_context.context,
            user_input,
            f"{self.receptionist_persona} Ask if they have any special requests or requirements."
        )
        
        guidance = "The receptionist is asking if you have any special requests. Mention any preferences or needs you might have."
        example = self.translate_text(
            "Example: I'd like a room on a higher floor with a non-smoking policy, and we'll need extra towels.", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text(prompt))
        )
    
    async def handle_special_requests(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Captures any special requests for the hotel booking."""
        await step_context.context.send_activity(MessageFactory.text("Step Four of Six: Noting special requests"))
        
        user_input = step_context.result
        feedback = await self.check_spelling_grammar(user_input)
        await step_context.context.send_activity(MessageFactory.text(feedback))
        
        self.special_requests = user_input
        
        # Use entity extraction to identify specific amenities or features in the request
        amenities = self.entity_extraction(user_input, ["Location", "Quantity", "DateTime", "Person"])
        
        # Analyze sentiment to gauge the importance of special requests
        sentiment = self.analyse_sentiment(user_input)
        
        # Add to conversation memory with detected entities
        special_requests_details = f"Special requests: {user_input}"
        if amenities and amenities != "No entities found.":
            special_requests_details += f" (Detected: {amenities})"
            
        self.add_to_memory(special_requests_details, "Bot asked for booking confirmation")
        
        # Get AI to determine the nature of the request for better handling
        ai_interpretation = await self.chatbot_respond(
            step_context.context,
            user_input,
            f"{self.receptionist_persona} The guest just provided this special request: '{user_input}'. Summarise the key points in this request in one sentence. Include any detected preferences for room location, amenities, or services."
        )
        
        # Update tracking flags
        self.special_requests_provided = True
        step_context.values["special_requests_provided"] = True
        
        # Add customised handling based on sentiment
        request_importance = ""
        if sentiment == "positive":
            request_importance = "We'll make sure to address your preferences."
        elif sentiment == "negative":
            request_importance = "We understand your concerns and will address them accordingly."
            
        # Calculate check-out description
        check_out_description = f"After {self.num_nights} nights" if self.num_nights else "Not specified"
            
        # Display a summary of the booking details so far
        booking_summary = (
            "Let me confirm your booking details:\n"
            f"Check-in: Today\n"
            f"Check-out: {check_out_description}\n"
            f"Room Type: {self.room_type}\n"
            f"Guests: {self.num_guests}\n"
            f"Special Requests: {self.special_requests}\n"
            f"Our understanding: {ai_interpretation}\n"
            f"{request_importance}"
        )
        
        await step_context.context.send_activity(MessageFactory.text(booking_summary))
        
        prompt = await self.chatbot_respond(
            step_context.context,
            user_input,
            f"{self.receptionist_persona} Ask the guest if all the booking details are correct and if they would like to confirm the booking."
        )
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text(prompt))
        )
    
    async def verify_booking_details(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Processes the user's confirmation of booking details."""
        await step_context.context.send_activity(MessageFactory.text("Step Five of Six: Confirming booking details"))
        
        user_input = step_context.result
        feedback = await self.check_spelling_grammar(user_input)
        await step_context.context.send_activity(MessageFactory.text(feedback))
        
        # Analyze sentiment to check if user is happy with the booking
        sentiment = self.analyse_sentiment(user_input)
        
        # Get AI to determine if the user is confirming or has issues
        ai_intent = await self.chatbot_respond(
            step_context.context,
            user_input,
            f"{self.receptionist_persona} The guest was asked to confirm their booking details and replied: '{user_input}'. Are they confirming the booking or do they have concerns? Reply with either 'CONFIRMED' or 'HAS_CONCERNS'.",
            temperature=0.1  # Lower temperature for intent detection
        )
        
        # Add to memory
        self.add_to_memory(f"User confirmation response: {user_input}", f"Bot interpretation: {ai_intent}")
        
        # Set booking confirmation flag
        self.booking_confirmed = "CONFIRMED" in ai_intent or sentiment == "positive"
        step_context.values["booking_confirmed"] = self.booking_confirmed
        
        if "HAS_CONCERNS" in ai_intent or sentiment == "negative":
            # Handle concerns
            concern_handling = await self.chatbot_respond(
                step_context.context,
                user_input,
                f"{self.receptionist_persona} The guest has concerns about their booking: '{user_input}'. Respond empathetically, addressing their concerns, then ask if they'd like to proceed with the booking."
            )
            
            await step_context.context.send_activity(MessageFactory.text(concern_handling))
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=MessageFactory.text(self.translate_text("Would you like to proceed with the booking?")))
            )
        
        # Continue with payment if confirmed
        prompt = await self.chatbot_respond(
            step_context.context,
            user_input,
            f"{self.receptionist_persona} Thank the guest for confirming the booking details and ask about payment method preferences (credit card, debit card, cash, etc.)."
        )
        
        guidance = "The receptionist is asking about payment method. Tell them how you'd like to pay."
        example = self.translate_text(
            "Example: I'd like to pay with my credit card.", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text(prompt))
        )
    
    async def collect_payment_method(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Captures the guest's preferred payment method."""
        await step_context.context.send_activity(MessageFactory.text("Step Six of Six: Payment method selection"))
        
        user_input = step_context.result
        feedback = await self.check_spelling_grammar(user_input)
        await step_context.context.send_activity(MessageFactory.text(feedback))
        
        self.payment_method = user_input
        self.payment_method_provided = True
        step_context.values["payment_method_provided"] = True
        
        self.add_to_memory(f"Payment method: {user_input}", "Bot summarising booking")
        
        # Prepare a complete booking summary
        booking_completed = await self.chatbot_respond(
            step_context.context,
            user_input,
            f"{self.receptionist_persona} The guest has provided their payment details ({user_input}). Confirm the booking is complete and provide a summary of their entire booking (check-in and check-out dates, room type, guests, special requests, and payment method). Conclude by saying 'Your booking is confirmed.' and provide a booking reference number that includes letters and numbers."
        )
        
        await step_context.context.send_activity(MessageFactory.text(booking_completed))
        
        # Ask if they have final questions
        prompt = await self.chatbot_respond(
            step_context.context,
            "booking complete",
            f"{self.receptionist_persona} Ask the guest if they have any final questions about their booking."
        )
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text(prompt))
        )
    
    async def finalize_reservation(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Handles any final questions and concludes the booking process."""
        user_input = step_context.result
        feedback = await self.check_spelling_grammar(user_input)
        await step_context.context.send_activity(MessageFactory.text(feedback))
        
        # Check if user has questions
        if len(user_input) > 10 and user_input.lower() != "no":
            response = await self.chatbot_respond(
                step_context.context,
                user_input,
                f"{self.receptionist_persona} The guest has asked: '{user_input}'. Respond helpfully to their question about their hotel booking, then thank them for choosing our hotel."
            )
            await step_context.context.send_activity(MessageFactory.text(response))
        else:
            conclusion = await self.chatbot_respond(
                step_context.context,
                user_input,
                f"{self.receptionist_persona} Thank the guest for their booking and wish them a pleasant stay."
            )
            await step_context.context.send_activity(MessageFactory.text(conclusion))
        
        # Calculate score before moving to feedback
        self.score = self.calculate_score(step_context)
        self.user_state.update_xp(self.score)
        
        await step_context.context.send_activity(MessageFactory.text("Your booking conversation is now complete. Let's see how you did!"))
        return await step_context.next(None)
    
    async def show_performance_feedback(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Displays performance feedback and score to the user."""
        await step_context.context.send_activity(MessageFactory.text("Scenario Feedback:"))
        
        # Display conversation memory
        memory = self.get_memory()
        await step_context.context.send_activity(MessageFactory.text("Here's a summary of your conversation:"))
        await step_context.context.send_activity(MessageFactory.text(memory))
        
        # Display score
        score_message = f"Your final score: {self.score}/100"
        await step_context.context.send_activity(MessageFactory.text(score_message))
        
        # Display feedback based on score
        feedback = self.generate_feedback()
        await step_context.context.send_activity(MessageFactory.text(feedback))
        
        # Send completion event for tracking
        completion_activity = Activity(
            type=ActivityTypes.event,
            name="scenario_complete",
            value={"scenario": "hotel", "score": self.score}
        )
        await step_context.context.send_activity(completion_activity)
        
        return await step_context.next(None)
    
    async def end_booking_scenario(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Completes the hotel scenario dialog."""
        thank_you = "Thank you for completing the Hotel Booking scenario!"
        await step_context.context.send_activity(MessageFactory.text(thank_you))
        await step_context.context.send_activity(MessageFactory.text(self.translate_text(thank_you, self.language)))
        
        return await step_context.end_dialog(result=True)
    
    async def verify_guest_count(self, prompt_context):
        if prompt_context.recognized.succeeded:
            # Make sure it's a positive number
            guests = prompt_context.recognized.value
            if guests <= 0:
                await prompt_context.context.send_activity("Please enter a positive number of guests.")
                return False
            if guests > 10:
                await prompt_context.context.send_activity("For large groups over ten, please call our special events department.")
                return False
            return True
        return False

    async def extract_nights_with_ai(self, turn_context, user_input):
        """Extract the number of nights from user input using AI."""
        response = await self.chatbot_respond(
            turn_context,
            user_input,
            f"{self.receptionist_persona} Extract ONLY the number of nights the guest wants to stay from their message. If they mention a specific number of nights, respond with just that number. If they don't specify a number, respond with 'unspecified'.",
            temperature=0.1  # Lower temperature for entity extraction
        )
        try:
            # Clean up AI response to get just the number
            response = response.strip()
            
            # Check if the AI couldn't determine the number
            if "unspecified" in response.lower():
                return None
                
            # Try to find a number in the AI's response
            number_match = re.search(r'(\d+)', response)
            if number_match:
                return int(number_match.group(1))
                
            return None
        except Exception as e:
            print(f"Error extracting nights with AI: {str(e)}")
            return None

    def add_to_memory(self, user_message: str, bot_response: str):
        """Add a user message and bot response to memory for context tracking."""
        if not hasattr(self, 'messages'):
            self.messages = []
        self.messages.append({"user": user_message, "bot": bot_response})
        if len(self.messages) > 10:  # Limit memory to the last 10 exchanges
            self.messages.pop(0)

    def get_memory(self) -> str:
        """Retrieve the conversation memory as a formatted string for context awareness."""
        if not hasattr(self, 'messages'):
            return "No conversation history available."
        return "\n".join([f"User: {msg['user']}\nBot: {msg['bot']}" for msg in self.messages])
        
    def generate_feedback(self) -> str:
        """Generates feedback text based on the user's score."""
        if self.score >= 90:
            return "Excellent job! Your hotel booking communication was clear and detailed."
        elif self.score >= 70:
            return "Good work! Try to be more specific about your requirements next time."
        else:
            return "Keep practising! Try to provide more complete information when booking a hotel."
    
    def calculate_score(self, step_context: WaterfallStepContext = None) -> int:
        """Calculate score based on interaction quality and task completion."""
        score = 0
        
        # Use step_context values if provided, otherwise fall back to instance variables
        if step_context:
            dates_provided = step_context.values.get("dates_provided", False) or self.check_in_date is not None
            room_type_specified = step_context.values.get("room_type_specified", False) or self.room_type is not None
            guests_provided = step_context.values.get("guests_provided", False) or self.guests_provided
            special_requests_provided = step_context.values.get("special_requests_provided", False) or self.special_requests_provided
            booking_confirmed = step_context.values.get("booking_confirmed", False) or self.booking_confirmed
            payment_method_provided = step_context.values.get("payment_method_provided", False) or self.payment_method_provided
        else:
            # Fall back to instance variables if no step_context is provided
            dates_provided = self.check_in_date is not None
            room_type_specified = self.room_type is not None
            guests_provided = self.guests_provided
            special_requests_provided = self.special_requests_provided
            booking_confirmed = self.booking_confirmed
            payment_method_provided = self.payment_method_provided
        
        # Basic completion points
        if dates_provided:
            score += 15
                
        if room_type_specified:
            score += 15
                
        if guests_provided:
            score += 15
            
        if special_requests_provided:
            score += 15
        
        if booking_confirmed:
            score += 15
            
        if payment_method_provided:
            score += 15
                
        # Base participation score
        score += 10
        
        return min(score, 100)
