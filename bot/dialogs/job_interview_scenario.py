from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult, PromptOptions
from botbuilder.dialogs.prompts import TextPrompt
from botbuilder.core import MessageFactory
from .base_dialog import BaseDialog
from bot.state.user_state import UserState

class JobInterviewScenarioDialog(BaseDialog):
    def __init__(self, user_state: UserState):
        dialog_id = "JobInterviewScenarioDialog"
        super(JobInterviewScenarioDialog, self).__init__(dialog_id, user_state)
        self.user_state = user_state

        # Define and add dialogs
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(WaterfallDialog(f"{dialog_id}.waterfall", [
            self.intro_step,                # Introduction
            self.ask_about_experience_step, # Discuss past experience
            self.ask_about_skills_step,     # Discuss key skills
            self.ask_why_this_job_step,     # "Why do you want this job?"
            self.ask_strengths_step,        # Strengths & weaknesses
            self.ask_salary_expectation,    # Salary discussion
            self.final_step                 # Completion step
        ]))

        self.initial_dialog_id = f"{dialog_id}.waterfall"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Step: Introduction to the job interview scenario."""
        text = "Welcome to the Job Interview Scenario! Let's practice answering common job interview questions."
        translated_text = self.translate_text(text, self.user_state.language)  # Translate message

        # Send both original and translated messages
        await step_context.context.send_activity(text)
        await step_context.context.send_activity(translated_text)
        return await step_context.next(None)  # Move to the next step

    async def ask_about_experience_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Step: Discuss past work experience in customer service."""
        await step_context.context.send_activity("The interviewer asked: 'Tell me about your past work experience in customer service.'")
        return await self.prompt_and_validate(step_context, 
            "I have four years of experience as a customer service representative, handling inquiries, resolving complaints, and ensuring customer satisfaction.")

    async def ask_about_skills_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Step: Discuss key skills relevant to customer service."""
        await step_context.context.send_activity("The interviewer asked: 'What are your key skills that make you a good fit for this role?'")
        return await self.prompt_and_validate(step_context, 
            "I am skilled in active listening, conflict resolution, and multitasking in fast-paced environments.")

    async def ask_why_this_job_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Step: Why do you want to work in customer service?"""
        await step_context.context.send_activity("The interviewer asked: 'Why do you want to work in customer service?'")
        return await self.prompt_and_validate(step_context, 
            "I enjoy helping people and ensuring they have a positive experience. I believe my ability to communicate effectively and remain patient makes me a great fit for this role.")

    async def ask_strengths_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Step: Strengths & Weaknesses discussion in customer service."""
        await step_context.context.send_activity("The interviewer asked: 'What are your biggest strengths and weaknesses in customer service?'")
        return await self.prompt_and_validate(step_context, 
            "My biggest strength is my ability to stay calm and professional in high-pressure situations. A weakness I am working on is improving my ability to handle multiple customers simultaneously without feeling overwhelmed.")

    async def ask_salary_expectation(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Step: Salary expectation discussion in customer service."""
        await step_context.context.send_activity("The interviewer asked: 'What are your salary expectations for this role?'")
        return await self.prompt_and_validate(step_context, 
            "Based on my experience in customer service and industry standards, I am looking for a salary range of $40,000 - $50,000 per year.")


    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Step: Completion of the interview scenario."""
        text = "You've completed the job interview scenario! Well done."
        translated_text = self.translate_text(text, self.user_state.language)  # Translate the final message

        # Send final message in both languages
        await step_context.context.send_activity(text)
        await step_context.context.send_activity(translated_text)
        await step_context.context.send_activity(f"Your final score is: {self.user_state.get_final_score()}")  # Display final score
        return await step_context.end_dialog()  # End the dialog

    async def prompt_and_validate(self, step_context: WaterfallStepContext, text_to_translate: str) -> DialogTurnResult:
        """Helper function to handle translation and validation in one step."""
        if step_context.result:  # If there was a previous response, validate it
            user_translation = step_context.result  # Get user translation
            correct_translation = step_context.values["correct_translation"]  # Get correct translation
            feedback = self.evaluate_response(user_translation, correct_translation)  # Evaluate response
            await step_context.context.send_activity(feedback)  # Provide feedback

        # Set the correct translation for this step
        correct_translation = self.translate_text(text_to_translate, self.user_state.language)  # Correct translation
        step_context.values["correct_translation"] = correct_translation  # Save for validation

        # Ask user for the translation of the phrase
        await step_context.context.send_activity(f"How would you say: '{text_to_translate}'")
        return await step_context.prompt(
            TextPrompt.__name__,  # Prompt for user input
            PromptOptions(prompt=MessageFactory.text("Type your translation:"))  # Prompt text
        )
