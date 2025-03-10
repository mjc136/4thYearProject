from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import os

class Chatbot:
    def __init__(self, model_dir="trained_model"):
        """Initialise the chatbot with the trained model."""
        # Ensure absolute path resolution
        model_path = os.path.abspath(model_dir)

        # Load model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(model_path)

        # Initialise the text-generation pipeline
        self.chatbot = pipeline(
            "text-generation", 
            model=self.model, 
            tokenizer=self.tokenizer
        )

    def get_response(self, prompt: str) -> str:
        """Generate a response for the given prompt."""
        response = self.chatbot(
            prompt,
            max_length=100,
            num_return_sequences=1,
            do_sample=True,
            temperature=0.7,
            top_k=50,
            top_p=0.95
        )
        
        # Extract generated text while avoiding slicing issues
        generated_text = response[0]['generated_text']
        
        # Ensure we remove the prompt from the response if it is included
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):].strip()

        return generated_text

# For testing
if __name__ == '__main__':
    bot = Chatbot()
    print(bot.get_response("Hello, how are you?"))
