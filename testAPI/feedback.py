from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine

# Is this code i strip the text and convert it to lowercase to clean it. Then i convert the text to a vector representation using the model.encode() method.
# I then calculate the cosine similarity between the two vectors using the scipy.spatial.distance.cosine() method.
# I then provide feedback based on the similarity score. If the similarity score is greater than 0.85, i provide positive feedback.
# If the similarity score is greater than 0.6, i provide a hint to the user. Otherwise, i provide the correct phrase to the user.

# Load the model once (lightweight and fast)
model = SentenceTransformer("paraphrase-MiniLM-L6-v2")

def evaluate_response(response: str, correct_text: str) -> str:
    """Evaluate user response based on meaning, not exact wording."""

    # Clean and Encode both sentences into vector representations
    response_embedding = model.encode(response.lower().strip())
    correct_embedding = model.encode(correct_text.lower().strip())

    # Compute cosine similarity (higher = more similar)
    # read about it here https://www.geeksforgeeks.org/cosine-similarity/
    similarity = 1 - cosine(response_embedding, correct_embedding)
    print(f"Similarity: {similarity:.2f}")

    # Provide feedback based on similarity
    if similarity > 0.85:
        return "Excellent! That's correct!"
    elif similarity > 0.6:
        return f"Good try! Your response is close in meaning but should be: '{correct_text}'"
    else:
        return f"Keep practicing! The correct phrase is: '{correct_text}'"

# Run independently
if __name__ == "__main__":
    print("Semantic Similarity Checker\n")
    user_response = "I'd love to drive your car around a few times!"
    correct_translation = "I would really like to drive your car around the block a few times!"

    # Evaluate user input
    feedback = evaluate_response(user_response, correct_translation)
    print("\nFeedback:", feedback)
