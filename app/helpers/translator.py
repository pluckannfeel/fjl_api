# DEEPL translator class
import os
from deepl import Translator as DeeplTranslator
from dotenv import load_dotenv

load_dotenv()


class Translator:
    def __init__(self):
        self.deepl = DeeplTranslator(os.getenv("DEEPL_API_KEY"))

    def translate(self, text: str, target_lang: str = "JA"):
        return self.deepl.translate_text(text, target_lang=target_lang)
