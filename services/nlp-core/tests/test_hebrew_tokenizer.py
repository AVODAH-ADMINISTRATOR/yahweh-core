import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from hebrew.tokenizer import HebrewTokenizer

def test_hebrew_tokenizer_basic():
    tokenizer = HebrewTokenizer(strip_vowels=True, strip_cantillation=True)
    # Genesis 1:1 "בְּרֵאשִׁית בָּרָא אֱלֹהִים" -> "בראשית ברא אלהים"
    raw_text = "בְּרֵאשִׁית בָּרָא אֱלֹהִים"
    tokens = tokenizer.tokenize(raw_text)
    
    assert len(tokens) == 3
    assert tokens[0] == "בראשית"
    assert tokens[1] == "ברא"
    assert tokens[2] == "אלהים"

def test_hebrew_tokenizer_keep_vowels():
    tokenizer = HebrewTokenizer(strip_vowels=False, strip_cantillation=True)
    raw_text = "בְּרֵאשִׁית בָּרָא אֱלֹהִים"
    tokens = tokenizer.tokenize(raw_text)
    
    assert len(tokens) == 3
    assert tokens[0] == "בְּרֵאשִׁית"
