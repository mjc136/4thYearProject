import language_tool_python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpellChecker:
    """Spell and grammar checker using LanguageTool."""
    
    def __init__(self):
        """Initialize the LanguageTool instance."""
        try:
            self.tool = language_tool_python.LanguageTool('en-US')
            logger.info("LanguageTool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LanguageTool: {e}")
            raise

    def check_grammar_and_spelling(self, text: str) -> str:
        """
        Check grammar and spelling using LanguageTool and format output.
        
        Args:
            text: The text to check
            
        Returns:
            str: Formatted string with corrections and corrected text
        """
        if not text or not text.strip():
            return "No text provided for checking."

        try:
            matches = self.tool.check(text)
            if not matches:
                return f"No mistakes found in: '{text}'"

            # Get all corrections at once
            corrections = []
            corrected_text = language_tool_python.utils.correct(text, matches)
            mistake_count = len(matches)

            # Compile all mistakes into a single message
            if mistake_count > 0:
                corrections = [
                    f"'{text[m.offset:m.offset + m.errorLength]}' should be "
                    f"'{m.replacements[0] if m.replacements else 'N/A'}'"
                    for m in matches
                ]
                mistake_summary = "; ".join(corrections)
                
                return (
                    f"Found {mistake_count} mistake{'s' if mistake_count > 1 else ''}\n"
                    f"Original text: {text}\n"
                    f"Mistakes found: {mistake_summary}\n"
                    f"Corrected text: {corrected_text}"
                )

        except Exception as e:
            logger.error(f"Error checking text: {e}")
            return f"Error checking text: {str(e)}"

    def __del__(self):
        """Cleanup LanguageTool resources."""
        if hasattr(self, 'tool'):
            self.tool.close()


if __name__ == "__main__":
    # Test the spell checker
    try:
        checker = SpellChecker()
        test_texts = [
            "This is a test sentnce with a speling mistake.",
            "She dont like ice cream.",
            "Its going to rain tomorrow.",
            ""  # Empty string test
        ]

        for text in test_texts:
            print("\nChecking text:", text)
            result = checker.check_grammar_and_spelling(text)
            print(result)
            print("-" * 50)

    except Exception as e:
        logger.error(f"Test failed: {e}")