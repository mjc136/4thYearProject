from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables from a specific path
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bot', '.env')
load_dotenv(dotenv_path=env_path)

AI_KEY = os.getenv("AI_API_KEY")
AI_ENDPOINT = os.getenv("AI_ENDPOINT")

client = OpenAI(api_key=AI_KEY, base_url=AI_ENDPOINT)

# Function to test the API
def test_deepseek():
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are LingoLizard, a language-learning assistant that helps users practice languages through interactive role-playing. You correct mistakes, provide feedback, and make learning fun."},
            {"role": "user", "content": "I want to practice ordering food in Portuguese. Can you simulate a restaurant conversation?"}
        ]
    )

    print(response.choices[0].message.content)


if __name__ == "__main__":
    test_deepseek()
