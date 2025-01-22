from dotenv import load_dotenv
import os

class Config:
    def __init__(self):
        load_dotenv()
        self.TRANSLATOR_KEY = os.getenv("TRANSLATOR_KEY")
        self.TRANSLATOR_ENDPOINT = os.getenv("TRANSLATOR_ENDPOINT")
        self.TRANSLATOR_LOCATION = os.getenv("TRANSLATOR_LOCATION")

    def validate(self):
        if not all([self.TRANSLATOR_KEY, self.TRANSLATOR_ENDPOINT, self.TRANSLATOR_LOCATION]):
            raise ValueError("Missing required environment variables")