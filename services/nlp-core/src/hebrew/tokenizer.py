import re

class HebrewTokenizer:
    def __init__(self, strip_vowels=False, strip_cantillation=False):
        self.strip_vowels = strip_vowels
        self.strip_cantillation = strip_cantillation
        
        # Unicode ranges for Hebrew diacritics
        self.vowel_range = re.compile(r'[\u0591-\u05BD\u05BF-\u05C2\u05C4-\u05C5\u05C7]')
        self.cantillation_range = re.compile(r'[\u0591-\u05AF]')

    def normalize(self, text: str) -> str:
        """Normalizes text by optionally stripping vowels and cantillation marks."""
        if self.strip_cantillation:
            text = self.cantillation_range.sub('', text)
        if self.strip_vowels:
            text = self.vowel_range.sub('', text)
        return text

    def tokenize(self, text: str) -> list[str]:
        """Tokenizes Hebrew text by splitting on spaces and punctuation."""
        normalized = self.normalize(text)
        # Split by whitespace, keeping standard punctuation intact (simplistic for stub)
        tokens = re.findall(r'[\w\u0590-\u05FF]+|[^\w\s]', normalized)
        return tokens
