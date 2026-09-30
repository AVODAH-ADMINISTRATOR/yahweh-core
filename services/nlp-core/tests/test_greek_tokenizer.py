import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from greek.tokenizer import GreekTokenizer

def test_greek_tokenizer_basic():
    tokenizer = GreekTokenizer(normalize_diacritics=True)
    # John 1:1 "Ἐν ἀρχῇ ἦν ὁ λόγος"
    raw_text = "Ἐν ἀρχῇ ἦν ὁ λόγος"
    tokens = tokenizer.tokenize(raw_text)
    
    assert len(tokens) == 5
    assert tokens[0] == "Εν"  # normalized Epsilon
    assert tokens[4] == "λογος" # normalized omicron with tonoc

def test_greek_tokenizer_keep_diacritics():
    tokenizer = GreekTokenizer(normalize_diacritics=False)
    raw_text = "Ἐν ἀρχῇ ἦν ὁ λόγος"
    tokens = tokenizer.tokenize(raw_text)
    
    assert len(tokens) == 5
    assert tokens[0] == "Ἐν"
