"""
utils.py — Pure utility functions for the TalentScout Hiring Assistant.

All functions here are stateless and side-effect-free, making them
easy to test in isolation.
"""

import re

# Keywords that signal the user wants to end the conversation.
# Stored as a frozenset for O(1) lookup and immutability.
EXIT_KEYWORDS: frozenset[str] = frozenset({
    "exit", "quit", "bye", "goodbye", "done", "end",
    "stop", "finish", "leave", "close", "thanks", "thank you",
})

# Word sets for keyword-based sentiment scoring.
_POSITIVE_WORDS: frozenset[str] = frozenset({
    "excited", "love", "passionate", "great", "strong", "confident",
    "enjoy", "happy", "thrilled", "excellent", "amazing", "fantastic",
    "awesome", "skilled", "proficient", "experienced", "eager",
    "enthusiastic", "motivated", "dedicated",
})

_NEGATIVE_WORDS: frozenset[str] = frozenset({
    "nervous", "worried", "unsure", "struggling", "difficult",
    "confused", "anxious", "stressed", "concerned", "afraid",
    "uncertain", "weak", "rusty", "beginner", "lacking",
    "overwhelmed", "intimidated",
})


def is_exit_keyword(message: str) -> bool:
    """
    Check whether the user's message contains an exit keyword.

    Uses whole-word matching so that e.g. "backend" does not trigger
    on "end".
    """
    words = set(re.findall(r"[a-zA-Z]+", message.lower()))
    return bool(words & EXIT_KEYWORDS)


def validate_email(email: str) -> bool:
    """Basic email format validation (not RFC 5322 strict)."""
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def validate_phone(phone: str) -> bool:
    """Check that the string contains at least 7 digits (loose validation)."""
    digits = re.sub(r"\D", "", phone)
    return 7 <= len(digits) <= 15


def format_tech_stack(raw_input: str) -> list[str]:
    """
    Parse a free-text tech stack string into a clean list of technology names.

    Handles comma-separated, "and"-separated, and mixed inputs.

    Examples:
        >>> format_tech_stack("Python, Django and React")
        ['Python', 'Django', 'React']
        >>> format_tech_stack("Java / Spring Boot / MySQL")
        ['Java', 'Spring Boot', 'MySQL']
    """
    # Normalise separators
    text = raw_input.replace(" and ", ",").replace(" & ", ",")
    text = text.replace("/", ",").replace(";", ",")

    # Split, strip whitespace, and remove empty strings
    techs = [t.strip() for t in text.split(",") if t.strip()]

    return techs


def analyze_sentiment(messages: list[str]) -> tuple[str, str]:
    """
    Perform keyword-based sentiment analysis on recent user messages.

    Scans the provided messages for positive and negative words
    and returns an emoji + label pair.

    Args:
        messages: List of the most recent user message strings.

    Returns:
        A tuple of (emoji, label), e.g. ("😊", "Confident").
    """
    score = 0

    for msg in messages:
        words = set(re.findall(r"[a-zA-Z]+", msg.lower()))
        score += len(words & _POSITIVE_WORDS)
        score -= len(words & _NEGATIVE_WORDS)

    if score > 0:
        return ("😊", "Confident")
    elif score < 0:
        return ("😟", "Nervous")
    else:
        return ("😐", "Neutral")
