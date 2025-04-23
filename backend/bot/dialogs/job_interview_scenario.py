from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult, PromptOptions
from botbuilder.dialogs.prompts import TextPrompt
from botbuilder.core import MessageFactory
from botbuilder.schema import Activity, CardAction, SuggestedActions, ActionTypes
from .base_dialog import BaseDialog
from backend.bot.state.user_state import UserState
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
        self.feedback_points = []

        self.add_dialog(TextPrompt(TextPrompt.__name__))
        waterfall_dialog = WaterfallDialog(
            f"{dialog_id}.waterfall",
            [
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
        
    async def check_formality(self, text: str, context=None) -> str:
        prompt = """Check if the text is formal and professional for a job interview do not
        be too harsh here just make sure grammar is good and that no slang is used.
        Return FORMAL if it is appropriate, or provide a brief suggestion for improvement if not."""
        response = await self.chatbot_respond(
            context,
            text,
            prompt,
            temperature=0.1  # Lower temperature for formality assessment
        )
        return response

    async def initial_greeting_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # Scenario context to help user understand the role
        context_message = "Interview Context: You're applying for a Customer Service Representative position at a technology company. The role involves handling customer inquiries, resolving issues, and ensuring customer satisfaction."
        await step_context.context.send_activity(context_message)
        
        prompt = await self.chatbot_respond(
            step_context.context,
            "interview start",
            "You are the interviewee for a customer service position. Begin formally. Ask the candidate to introduce themselves and outline their background. Keep your question concise."
        )
        
        example = "Example: 'Good morning! I'm [Your Name], and I have [X years] of experience in customer service. My background includes...' (Feel free to create a professional persona for this practice)"
        await step_context.context.send_activity(self.translate_text(example, self.language))
        
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def experience_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.initial_impression = step_context.result
        
        # Check formality and provide feedback if needed
        formality_check = await self.check_formality(step_context.result, step_context.context)
        if "FORMAL" not in formality_check.upper():
            await step_context.context.send_activity(f"Tip for improvement: {formality_check}")
            self.feedback_points.append("Work on maintaining professional tone throughout the interview")
        
        
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask for specific customer service experience. Encourage the user to talk about responsibilities and achievements. Be encouraging and professional."
        )
        
        # More helpful guidance with structure
        tips = "Response Tips:\n- Mention 1-2 specific roles where you handled customer service\n- Describe key responsibilities using action verbs\n- Share a brief achievement that shows your skills\n- Keep your answer to 3-5 sentences"
        await step_context.context.send_activity(self.translate_text(tips, self.language))
        
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def skills_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.experience = step_context.result
        
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask the candidate to describe their key skills and how they align with the role."
        )
        await step_context.context.send_activity(self.translate_text("Example: I have strong communication and problem-solving skills which help me handle customer issues effectively.", self.language))
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def motivation_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.skills = step_context.result
        
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask about the candidate's motivation for working in customer service and what they enjoy most about it."
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def strengths_weaknesses_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.motivation = step_context.result
        
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask the candidate to discuss both strengths and areas for improvement with honesty and self-awareness."
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def salary_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.strengths_weaknesses = step_context.result
        
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask about salary expectations. Encourage the user to justify their expectation based on experience and value."
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def questions_for_interviewer_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.salary_expectation = step_context.result
        
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Ask if the candidate has any questions for the interviewer about the company or position."
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def closing_remarks_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.questions_for_interviewer = step_context.result
        
        prompt = await self.chatbot_respond(
            step_context.context,
            step_context.result,
            "Conclude the interview. Thank the candidate and briefly mention the next steps."
        )
        return await step_context.prompt(TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt)))

    async def final_confirmation_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.score = await self.calculate_score(step_context.result)
        self.user_state.update_score(self.score)
        
        feedback = self.generate_feedback()
        await step_context.context.send_activity(feedback)
        return await step_context.next(None)

    async def feedback_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        message = f"You completed the job interview scenario. Your score: {self.score}/100"
        translated_message = self.translate_text(message, self.language)
        
        await step_context.context.send_activity(message)
        await step_context.context.send_activity(translated_message)
        return await step_context.end_dialog()

    async def calculate_score(self, final_response: str) -> int:
        score = 60
        
        # Check response quality based on length and content
        if self.experience:
            if len(self.experience) > 30:
                score += 5
            
            # Use AI to evaluate content quality rather than specific English keywords
            experience_quality = await self.chatbot_respond(
                None,  # We don't have a context here, so use None
                self.experience,
                "Evaluate if this response mentions specific job responsibilities or achievements. Return YES if it does, NO if it doesn't.",
                temperature=0.1
            )
            if "YES" in experience_quality.upper():
                score += 5
            else:
                self.feedback_points.append("Provide more detailed examples about your experience")
        
        if self.skills:
            if len(self.skills) > 30:
                score += 5
            
            skills_quality = await self.chatbot_respond(
                None,  # We don't have a context here, so use None
                self.skills,
                "Evaluate if this response mentions specific skills relevant to customer service. Return YES if it does, NO if it doesn't."
            )
            if "YES" in skills_quality.upper():
                score += 5
            else:
                self.feedback_points.append("Elaborate more on relevant skills for the role")
        
        if self.strengths_weaknesses:
            if len(self.strengths_weaknesses) > 40:
                score += 5
            
            strengths_weaknesses_quality = await self.chatbot_respond(
                None,  # We don't have a context here, so use None
                self.strengths_weaknesses,
                "Evaluate if this response discusses both strengths and weaknesses/areas for improvement. Return YES if it covers both, NO if it doesn't."
            )
            if "YES" in strengths_weaknesses_quality.upper():
                score += 5
            else:
                self.feedback_points.append("Be more specific about your strengths and areas for improvement")

        # Use language-independent detection for politeness
        politeness_check = await self.chatbot_respond(
            None,  # We don't have a context here, so use None
            final_response,
            "Does this response include expressions of gratitude or thanks in any language? Return YES or NO.",
            temperature=0.1
        )
        if "YES" in politeness_check.upper():
            score += 5
        
        # Use language-independent detection for questions
        questions_check = await self.chatbot_respond(
            None,  # We don't have a context here, so use None
            final_response,
            "Does this response include questions for the interviewer or mentions asking questions? Return YES or NO.",
            temperature=0.1
        )
        if "YES" in questions_check.upper():
            score += 5
        
        return min(score, 100)

    def generate_feedback(self) -> str:
        feedback = "Interview Performance Feedback:\n\n"
        
        if self.score >= 90:
            feedback += "Outstanding! You demonstrated fluent and professional communication throughout the interview.\n\n"
        elif self.score >= 70:
            feedback += "Strong performance! You addressed the questions well and showed clear motivation.\n\n"
        else:
            feedback += "Good start! With more practice, you'll continue to improve your interview skills.\n\n"
        
        feedback += "Strengths:\n"
        if self.score >= 80:
            feedback += "- Professional communication style\n"
        if self.score >= 75:  
            feedback += "- Good use of specific examples\n"
        if self.score >= 70:
            feedback += "- Clear structure in responses\n"
            
        feedback += "\nAreas to Improve:\n"
        if self.feedback_points:
            for point in self.feedback_points[:3]:  # Show top 3 improvement areas
                feedback += f"- {point}\n"
        else:
            feedback += "- Continue practising concise, example-driven responses\n"
            
        feedback += "\nNext Steps:\n"
        feedback += "- Review common interview questions for customer service roles\n"
        feedback += "- Practice with different scenarios to build confidence\n"
        feedback += "- Consider recording yourself to review your speaking pace and clarity"
        
        return feedback
