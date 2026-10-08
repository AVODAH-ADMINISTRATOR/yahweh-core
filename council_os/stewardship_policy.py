"""Input normalization and conservative stewardship action screening."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterable

from council_os.constraints import CharterViolation

MAX_INPUT_LENGTH = 4096
_ACTION_RULES = {
    "deceit": re.compile(r"\b(?:deceiv\w*|dishonest\w*|mislead\w*|falsif\w*|lie)\b", re.I),
    "theft": re.compile(r"\b(?:steal\w*|theft|stolen|embezzl\w*|exfiltrat\w*|unauthorized transfer)\b", re.I),
    "harm": re.compile(r"\b(?:harm\w*|weapon\w*|exploit\w*|abuse\w*|injur\w*)\b", re.I),
    "fraud": re.compile(r"\b(?:fraud\w*|forged|forgery|scam\w*|deceptive billing|forge\s+(?:an?\s+|the\s+)?(?:invoice|signature|record|document|approval))\b", re.I),
}


def sanitize_text(value: str, *, field: str = "input", max_length: int = MAX_INPUT_LENGTH) -> str:
    if not isinstance(value, str):
        raise CharterViolation(f"{field} must be text")
    normalized = unicodedata.normalize("NFKC", value)
    normalized = "".join(
        character for character in normalized
        if not unicodedata.category(character).startswith("C") or character in "\n\t"
    ).strip()
    if not normalized:
        raise CharterViolation(f"{field} must not be empty")
    if len(normalized) > max_length:
        raise CharterViolation(f"{field} exceeds maximum length")
    return normalized


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _strings(nested)
    elif isinstance(value, (list, tuple, set)):
        for nested in value:
            yield from _strings(nested)


def check_action_policy(action: str, payload: Any = None) -> None:
    content = [sanitize_text(item, field="action content") for item in _strings(payload) if item.strip()]
    text = " ".join([sanitize_text(action, field="action"), *content])
    for category, pattern in _ACTION_RULES.items():
        if pattern.search(text):
            raise CharterViolation(f"stewardship policy refused {category}")
