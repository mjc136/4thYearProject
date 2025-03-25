from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult, PromptOptions
from botbuilder.dialogs.prompts import TextPrompt
from botbuilder.core import MessageFactory
from botbuilder.schema import Activity
from .base_dialog import BaseDialog
from bot.state.user_state import UserState
import re

class JobInterviewScenarioDialog(BaseDialog):
    def __init__(self, user_state: UserState):
        dialog_id = "JobInterviewScenarioDialog"
        super().__init__(dialog_id, user_state)
        self.user_state = user_state
        self.language = self.user_state.get_language()

        self.experience = None
        self.skills = None
        self.strengths = None
        self.weaknesses = None
        self.salary_expectation = None
        self.score = 0

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
        message = "Welcome to the Job Interview Scenario (Advanced Level)."
        tip = "Try to answer using professional, formal language and give specific examples."
        await step_context.context.send_activity(self.translate_text(message, self.language))
        await step_context.context.send_activity(self.translate_text(tip, self.language))
        return await step_context.next(None)

    async def initial_greeting_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(Activity(type="typing"))
        prompt = await self.chatbot_respond(
            step_context.context,
            "interview start",
            "You are the interviewer. Begin formally. Ask the candidate to introduce themselves and outline their background."
        )
        await step_context.context.send_activity(self.translate_text("Example: Good morning. Please introduce yourself and tell me about your background.", self.language))
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def experience_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.initial_impression = step_context.result
        await step_context.context.send_activity(Activity(type="typing"))
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask for specific customer service experience. Encourage the user to talk about responsibilities and achievements."
        )
        await step_context.context.send_activity(self.translate_text("Tip: Use specific examples and action verbs like 'handled', 'led', or 'resolved'.", self.language))
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def skills_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.experience = step_context.result
        await step_context.context.send_activity(Activity(type="typing"))
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask the candidate to describe their key skills and how they align with the role."
        )
        await step_context.context.send_activity(self.translate_text("Example: I have strong communication and problem-solving skills which help me handle customer issues effectively.", self.language))
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def motivation_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.skills = step_context.result
        await step_context.context.send_activity(Activity(type="typing"))
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask about the candidate's motivation for working in customer service and what they enjoy most about it."
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def strengths_weaknesses_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.motivation = step_context.result
        await step_context.context.send_activity(Activity(type="typing"))
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask the candidate to discuss both strengths and areas for improvement with honesty and self-awareness."
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def salary_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.strengths_weaknesses = step_context.result
        await step_context.context.send_activity(Activity(type="typing"))
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask about salary expectations. Encourage the user to justify their expectation based on experience and value."
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def questions_for_interviewer_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.salary_expectation = step_context.result
        await step_context.context.send_activity(Activity(type="typing"))
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask if the candidate has any questions for the interviewer about the company or position."
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def closing_remarks_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.questions_for_interviewer = step_context.result
        await step_context.context.send_activity(Activity(type="typing"))
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Conclude the interview. Thank the candidate and briefly mention the next steps."
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def final_confirmation_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.score = self.calculate_score(step_context.result)
        self.user_state.update_score(self.score)
        await step_context.context.send_activity(Activity(type="typing"))
        feedback = self.generate_feedback()
        await step_context.context.send_activity(feedback)
        return await step_context.next(None)

    async def feedback_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        message = f"You completed the job interview scenario. Your score: {self.score}/100"
        translated_message = self.translate_text(message, self.language)
        await step_context.context.send_activity(Activity(type="typing"))
        await step_context.context.send_activity(message)
        await step_context.context.send_activity(translated_message)
        return await step_context.end_dialog()

    def calculate_score(self, final_response: str) -> int:
        score = 60
        if self.experience:
            score += 10
        if self.skills:
            score += 10
        if self.strengths and self.weaknesses:
            score += 10

        thank_you_phrases = ["thank", "gracias", "merci", "obrigado", "obrigada"]
        if any(word in final_response.lower() for word in thank_you_phrases):
            score += 5

        if any(keyword in final_response.lower() for keyword in ["question", "ask", "pregunta", "pergunta", "demander"]):
            score += 5

        return min(score, 100)

    def generate_feedback(self) -> str:
        feedback = "Here's your interview feedback:\n"
        if self.score >= 90:
            feedback += "Outstanding! You demonstrated fluent and professional communication throughout the interview."
        elif self.score >= 70:
            feedback += "Strong performance. You addressed the questions well and showed clear motivation."
        else:
            feedback += "Keep practicing. Focus on expressing ideas more clearly and using formal language."
        return feedback
