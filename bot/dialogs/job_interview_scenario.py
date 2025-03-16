from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult, PromptOptions
from botbuilder.dialogs.prompts import TextPrompt
from botbuilder.core import MessageFactory
from .base_dialog import BaseDialog
from bot.state.user_state import UserState

class JobInterviewScenarioDialog(BaseDialog):
    def __init__(self, user_state: UserState):
        dialog_id = "JobInterviewScenarioDialog"
        super().__init__(dialog_id, user_state)
        self.user_state = user_state
        self.language = self.user_state.get_language()
        
        # Add conversation state
        self.experience = None
        self.skills = None
        self.strengths = None
        self.weaknesses = None
        self.salary_expectation = None
        self.score = 0

        # Initialize dialogues
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        waterfall_dialog = WaterfallDialog(
            f"{dialog_id}.waterfall",
            [
                self.intro_step,
                self.initial_greeting_step,
                self.experience_step,
                self.skills_step,
                self.motivation_step,
                self.strengths_weaknesses_step,
                self.salary_step,
                self.questions_for_interviewer_step,
                self.closing_remarks_step,
                self.final_confirmation_step,
                self.feedback_step
            ]
        )
        self.add_dialog(waterfall_dialog)
        self.initial_dialog_id = f"{dialog_id}.waterfall"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        message = "Welcome to the Job Interview Scenario! Let's practice for a customer service position interview."
        translated_message = self.translate_text(message, self.language)
        
        await step_context.context.send_activity(message)
        await step_context.context.send_activity(translated_message)
        return await step_context.next(None)

    async def initial_greeting_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        prompt = self.chatbot_respond(
            "interview start",
            "As an interviewer, greet the candidate warmly and ask them to introduce themselves briefly."
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def experience_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.initial_impression = step_context.result
        prompt = self.chatbot_respond(
            step_context.result,
            "Ask about their relevant experience in customer service roles."
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def skills_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.experience = step_context.result
        prompt = self.chatbot_respond(
            step_context.result,
            "What are your key skills that make you a good fit for this role?"
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def motivation_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.skills = step_context.result
        prompt = self.chatbot_respond(
            step_context.result,
            "Why do you want to work in customer service?"
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def strengths_weaknesses_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.motivation = step_context.result
        prompt = self.chatbot_respond(
            step_context.result,
            "What are your biggest strengths and weaknesses in customer service?"
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def salary_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.strengths_weaknesses = step_context.result
        prompt = self.chatbot_respond(
            step_context.result,
            "What are your salary expectations for this role?"
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def questions_for_interviewer_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.salary_expectation = step_context.result
        prompt = self.chatbot_respond(
            step_context.result,
            "Do you have any questions for the interviewer?"
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def closing_remarks_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.questions_for_interviewer = step_context.result
        prompt = self.chatbot_respond(
            step_context.result,
            "Thank the candidate for their time and provide any closing remarks."
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(prompt))
        )

    async def final_confirmation_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.score = self.calculate_score(step_context.result)
        self.user_state.update_score(self.score)
        
        feedback = self.generate_feedback()
        await step_context.context.send_activity(feedback)
        return await step_context.next(None)

    async def feedback_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        text = "You've completed the job interview scenario! Well done."
        translated_text = self.translate_text(text, self.language)
        
        await step_context.context.send_activity(text)
        await step_context.context.send_activity(translated_text)
        await step_context.context.send_activity(f"Your final score is: {self.user_state.get_final_score()}")
        return await step_context.end_dialog()

    def calculate_score(self, final_response: str) -> int:
        score = 60  # Base score
        if self.experience:
            score += 10
        if self.skills:
            score += 10
        if self.strengths and self.weaknesses:
            score += 10
        if "thank" in final_response.lower():
            score += 5
        if any(word in final_response.lower() for word in ["question", "ask"]):
            score += 5
        return min(score, 100)

    def generate_feedback(self) -> str:
        feedback = "Here's your interview feedback:\n"
        if self.score >= 90:
            feedback += "Excellent interview! You demonstrated strong communication skills and provided comprehensive responses."
        elif self.score >= 70:
            feedback += "Good interview! You covered most key points but could add more detail to some responses."
        else:
            feedback += "Keep practicing! Focus on expanding your answers and using professional language."
        return feedback
