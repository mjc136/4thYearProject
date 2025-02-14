from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine

# Load the model once (lightweight and fast)
model = SentenceTransformer("paraphrase-MiniLM-L6-v2")

def evaluate_response(response: str, correct_text: str) -> str:
    """Evaluate user response based on meaning, not exact wording."""

    # Encode both sentences into vector representations
    response_embedding = model.encode(response.lower().strip())
    correct_embedding = model.encode(correct_text.lower().strip())

    # Compute cosine similarity (higher = more similar)
    similarity = 1 - cosine(response_embedding, correct_embedding)

    # Provide feedback based on similarity
    if similarity > 0.85:
        return "Excellent! That's correct! ⭐"
    elif similarity > 0.6:
        return f"Good try! Your response is close in meaning but should be: '{correct_text}'"
    else:
        return f"Keep practicing! The correct phrase is: '{correct_text}'"

# Run independently
if __name__ == "__main__":
    print("Semantic Similarity Checker\n")
    user_response = input("Enter your translation: ")
    correct_translation = input("Enter the correct translation: ")

    # Evaluate user input
    feedback = evaluate_response(user_response, correct_translation)
    print("\nFeedback:", feedback)
