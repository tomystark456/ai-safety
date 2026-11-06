"""Microsoft Presidio-style detection of sensitive information in user text.

Category B: https://github.com/microsoft/presidio
Redacts emails, phone numbers and card-like digit groups before the model sees them.
"""

from __future__ import annotations

import re

EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", re.I)
PHONE = re.compile(r"\b(?:\+?\d[\d\-() ]{8,}\d)\b")
CARD = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


def redact_pii(text: str) -> str:
    text = EMAIL.sub("[REDACTED_EMAIL]", text)
    text = PHONE.sub("[REDACTED_PHONE]", text)
    text = CARD.sub("[REDACTED_CARD]", text)
    return text
