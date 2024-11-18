from deep_translator import GoogleTranslator

def translate_text(text, target_lang):
    # Initialize GoogleTranslator with target language
    translator = GoogleTranslator(target=target_lang)
    translation = translator.translate(text)
    return translation

print(translate_text("hello", 'de'))  # Should output "Hallo" for German
