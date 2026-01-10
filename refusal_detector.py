"""
Detect if a model refused to generate a press release.
"""

import re


REFUSAL_PATTERNS = [
    r"I (?:cannot|can't|won't|will not|must not|should not)",
    r"I'm (?:unable|not able|sorry)",
    r"(?:cannot|can't) (?:help|assist|provide|generate|write|create)",
    r"(?:inappropriate|unethical|harmful|problematic|concerning)",
    r"against my (?:guidelines|principles|values|programming)",
    r"not comfortable",
    r"I don't feel comfortable",
    r"I must (?:decline|refuse)",
    r"goes against",
    r"violates",
    r"I'm designed to",
    r"as an AI",
    r"my purpose is",
]


def is_refusal(text: str) -> bool:
    """
    Detect if the text contains a refusal to generate content.

    Args:
        text: The generated text to check

    Returns:
        True if text appears to be a refusal, False otherwise
    """
    # Check if text is suspiciously short (likely a refusal or error)
    if len(text.strip()) < 50:
        return True

    # Check for common refusal patterns
    text_lower = text.lower()
    for pattern in REFUSAL_PATTERNS:
        if re.search(pattern, text_lower):
            return True

    return False


def get_refusal_reason(text: str) -> str:
    """
    Get the reason for refusal if detected.

    Args:
        text: The generated text

    Returns:
        String describing the refusal reason
    """
    if len(text.strip()) < 50:
        return "Response too short (likely refusal or error)"

    text_lower = text.lower()
    for pattern in REFUSAL_PATTERNS:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            # Get surrounding context (50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()
            return f"Refusal detected: ...{context}..."

    return "Unknown refusal reason"
