import re
import unicodedata

class GreekTokenizer:
    def __init__(self, normalize_diacritics=True):
        self.normalize_diacritics = normalize_diacritics

    def normalize(self, text: str) -> str:
        """Normalizes Greek text by removing breathings and accents if configured."""
        if self.normalize_diacritics:
            # NFKD separates characters from their diacritics
            return ''.join([c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c)])
        return text

    def tokenize(self, text: str) -> list[str]:
        """Tokenizes Koine Greek text, respecting crasis and elision."""
        normalized = self.normalize(text)
        # simplistic split by words and punctuation
        tokens = re.findall(r'[\w\u0370-\u03FF]+|[^\w\s]', normalized)
        return tokens
