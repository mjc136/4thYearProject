from botbuilder.dialogs import (
    WaterfallDialog, WaterfallStepContext, DialogTurnResult, 
    PromptOptions, TextPrompt, DialogTurnStatus
)
from botbuilder.core import MessageFactory
from botbuilder.schema import ActivityTypes, Activity
import asyncio
from .base_dialog import BaseDialog
from backend.bot.state.user_state import UserState

class DoctorVisitScenarioDialog(BaseDialog):
    def __init__(self, user_state: UserState):
        super().__init__("DoctorVisitScenarioDialog", user_state)
        self.user_state = user_state
        self.language = self.user_state.get_language()

        # Patient information
        self.symptoms_described = None
        self.treatment_received = None
        self.score = 0
        
        # Scoring flags
        self.greeted_receptionist = False
        self.described_symptoms = False
        self.asked_questions = False
        self.understood_treatment = False
        self.thanked_doctor = False
        
        # Add prompts
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        
        self.add_dialog(
            WaterfallDialog(
                "DoctorVisitScenarioDialog.waterfall",
                [
                    self.reception_greeting,
                    self.doctor_greeting,
                    self.symptom_description,
                    self.diagnosis,
                    self.treatment_plan,
                    self.show_feedback,
                    self.end_scenario
                ]
            )
        )
        self.initial_dialog_id = "DoctorVisitScenarioDialog.waterfall"

    async def reception_greeting(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Step One of Five: Checking in at the clinic"))
        
        prompt = await self.chatbot_respond(
            step_context.context,
            "start",
            "You are a receptionist at a medical clinic. Greet the patient warmly and ask for their name and what brings them in today."
        )
        
        guidance = "Greet the receptionist and explain that you have a sunburn."
        example = self.translate_text(
            "Example: Good morning. My name is Alex. I'm here because I have a bad sunburn.", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def doctor_greeting(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Step Two of Five: Meeting the doctor"))
        user_input = step_context.result
        
        # Track that user greeted receptionist
        self.greeted_receptionist = True
        step_context.values["greeted_receptionist"] = True
        
        # Receptionist responds and doctor arrives
        await step_context.context.send_activity(MessageFactory.text("*The receptionist takes your information and asks you to wait...*"))
        await asyncio.sleep(1)
        await step_context.context.send_activity(MessageFactory.text("*After a short wait, the doctor calls your name*"))
        
        doctor_greeting = await self.chatbot_respond(
            step_context.context,
            user_input,
            "You are now a doctor. Greet the patient by name (extract from their previous message) and ask them to describe their sunburn in more detail."
        )
        
        await step_context.context.send_activity(MessageFactory.text(doctor_greeting))
        
        guidance = "Greet the doctor and explain where your sunburn is and how it feels."
        example = self.translate_text(
            "Example: Hello doctor. I got a bad sunburn on my shoulders and back yesterday at the beach. It's very red and painful.", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text("How would you describe your sunburn?"))
        )

    async def symptom_description(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Step Three of Five: Describing your symptoms"))
        user_input = step_context.result
        
        # Store symptom information
        self.symptoms_described = user_input
        self.described_symptoms = True
        step_context.values["described_symptoms"] = True
        
        # Doctor asks follow-up questions
        follow_up = await self.chatbot_respond(
            step_context.context,
            user_input,
            "Ask the patient follow-up questions: When did they get the sunburn? Have they applied anything to it? Are they experiencing any other symptoms like fever or chills?"
        )
        
        await step_context.context.send_activity(MessageFactory.text(follow_up))
        
        guidance = "Answer the doctor's questions about your sunburn."
        example = self.translate_text(
            "Example: I got the sunburn yesterday afternoon. I haven't applied anything to it yet. I don't have a fever, but the area feels hot and tight.", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text("Can you tell me more about your sunburn?"))
        )

    async def diagnosis(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Step Four of Five: Receiving a diagnosis"))
        user_input = step_context.result
        
        ai_question = await self.chatbot_respond(
            step_context.context,
            user_input,
            "The doctor is now explaining the treatment plan. Did the patient ask any questions about the treatment? Reply with 'YES' or 'NO'.",
            temperature=0.1  # Lower temperature for intent detection
        )
        
        # Patient provided more info and possibly asked questions
        if ai_question.strip().upper() == "YES":
            self.asked_questions = True
            step_context.values["asked_questions"] = True
        
        # Doctor provides diagnosis
        diagnosis_response = await self.chatbot_respond(
            step_context.context,
            user_input,
            "Provide a simple diagnosis for second-degree sunburn. Explain it's not serious but needs proper care. Mention they should avoid further sun exposure and that you'll recommend some treatments."
        )
        
        await step_context.context.send_activity(MessageFactory.text(diagnosis_response))
        
        guidance = "Ask the doctor what you should do for your sunburn."
        example = self.translate_text(
            "Example: What should I do to treat it? Is there anything I should avoid?", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text("Do you have any questions about the diagnosis?"))
        )

    async def treatment_plan(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Step Five of Five: Understanding treatment"))
        user_input = step_context.result
        
        # Use lower temperature (0.1) for intent detection to get more deterministic results
        ai_question = await self.chatbot_respond(
            step_context.context,
            user_input,
            "The doctor is now explaining the treatment plan. Did the patient ask any questions about the treatment? Reply with 'YES' or 'NO'.",
            temperature=0.1  # Lower temperature for intent detection
        )
        
        # Patient asked about treatment
        if ai_question.strip().upper() == "YES":
            self.asked_questions = True
            step_context.values["asked_questions"] = True
        
        # Doctor provides treatment advice - use default temperature (0.5) for more natural responses
        treatment_response = await self.chatbot_respond(
            step_context.context,
            user_input,
            "Recommend cool compresses, aloe vera gel, over-the-counter pain relievers, and plenty of water. Advise against petroleum jelly, butter, or other home remedies that trap heat. Ask if they understand the treatment plan."
            # Using default temperature of 0.5 for conversational responses
        )
        
        await step_context.context.send_activity(MessageFactory.text(treatment_response))
        
        guidance = "Tell the doctor you understand and thank them for their help."
        example = self.translate_text(
            "Example: I understand. Thank you for your help, doctor. I'll follow your advice.", 
            self.language
        )
        
        await step_context.context.send_activity(MessageFactory.text(guidance))
        await step_context.context.send_activity(MessageFactory.text(example))
        
        return await step_context.prompt(
            TextPrompt.__name__, 
            PromptOptions(prompt=MessageFactory.text("Do you understand the treatment plan?"))
        )

    async def show_feedback(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        user_input = step_context.result
        
        # Check if patient understood treatment and thanked doctor
        ai_understood = await self.chatbot_respond(
            step_context.context,
            user_input,
            "The patient just responded after hearing the treatment plan. Did they confirm understanding? Reply with 'YES' or 'NO'."
        )

        if ai_understood.strip().upper() == "YES":
            self.understood_treatment = True
            step_context.values["understood_treatment"] = True
            
        sentiment = self.analyse_sentiment(user_input)
        ai_thanks = await self.chatbot_respond(
            step_context.context,
            user_input,
            "The patient just responded at the end of the visit. Did they thank the doctor? Reply with 'YES' or 'NO'."
        )

        if sentiment == "positive" or ai_thanks.strip().upper() == "YES":
            self.thanked_doctor = True
            step_context.values["thanked_doctor"] = True

        
        # Doctor's final advice
        final_advice = await self.chatbot_respond(
            step_context.context,
            user_input,
            "Give some final encouragement and advice. Tell the patient they can call if they have any concerns and wish them a quick recovery."
        )
        
        await step_context.context.send_activity(MessageFactory.text(final_advice))
        
        # Calculate score
        self.score = self.calculate_score(step_context)
        self.user_state.update_xp(self.score)
        
        await step_context.context.send_activity(MessageFactory.text("Your doctor visit is now complete. Let's see how you did!"))
        
        # Display score
        await step_context.context.send_activity(MessageFactory.text("Scenario Feedback:"))
        score_message = f"Your final score: {self.score}/100"
        await step_context.context.send_activity(MessageFactory.text(score_message))
        
        # Display feedback
        feedback = self.generate_feedback()
        await step_context.context.send_activity(MessageFactory.text(feedback))
        
        # Send completion event
        completion_activity = Activity(
            type=ActivityTypes.event,
            name="scenario_complete",
            value={"scenario": "doctor_visit", "score": self.score}
        )
        await step_context.context.send_activity(completion_activity)
        
        return await step_context.next(None)
    
    async def end_scenario(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Completes the doctor visit scenario dialog."""
        thank_you = "Thank you for completing the Doctor Visit scenario!"
        await step_context.context.send_activity(MessageFactory.text(thank_you))
        await step_context.context.send_activity(MessageFactory.text(self.translate_text(thank_you, self.language)))
        
        return await step_context.end_dialog(result=True)
        
    def generate_feedback(self) -> str:
        """Generates feedback text based on the user's score."""
        if self.score >= 90:
            return "Excellent job! You communicated your symptoms clearly and understood the treatment."
        elif self.score >= 70:
            return "Good work! You successfully described your condition to the doctor."
        else:
            return "Keep practicing! Try to be more specific about your symptoms next time and ask more questions."
    
    def calculate_score(self, step_context: WaterfallStepContext = None) -> int:
        """Calculate score based on interaction quality and task completion."""
        score = 0
        
        # Use step_context values if provided, otherwise fall back to instance variables
        if step_context:
            greeted_receptionist = step_context.values.get("greeted_receptionist", False) or self.greeted_receptionist
            described_symptoms = step_context.values.get("described_symptoms", False) or self.described_symptoms
            asked_questions = step_context.values.get("asked_questions", False) or self.asked_questions
            understood_treatment = step_context.values.get("understood_treatment", False) or self.understood_treatment
            thanked_doctor = step_context.values.get("thanked_doctor", False) or self.thanked_doctor
        else:
            # Fall back to instance variables
            greeted_receptionist = self.greeted_receptionist
            described_symptoms = self.described_symptoms
            asked_questions = self.asked_questions
            understood_treatment = self.understood_treatment
            thanked_doctor = self.thanked_doctor
        
        # Basic completion points
        if greeted_receptionist:
            score += 15
                
        if described_symptoms:
            score += 20
                
        if asked_questions:
            score += 25
            
        if understood_treatment:
            score += 20
            
        if thanked_doctor:
            score += 10
        
        # Base participation score
        score += 10
        
        return min(score, 100)
