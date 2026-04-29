"""
data_handler.py — Candidate data extraction, persistence, and export.

Extraction strategy:
    The system prompt forces one-at-a-time field collection in a fixed order,
    so user message N maps to field N (index-based extraction). A regex
    fallback scans all messages for email/phone patterns as a safety net.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from utils import validate_email, validate_phone


# Directory for storing candidate JSON files
CANDIDATES_DIR = Path("candidates")


class CandidateDataHandler:
    """Handles extraction of structured data from conversation history."""

    FIELD_ORDER: list[str] = [
        "full_name", "email", "phone", "years_of_experience",
        "desired_positions", "current_location", "tech_stack",
    ]

    # Keywords in the assistant's message that indicate which field is being asked
    _FIELD_KEYWORDS: dict[str, list[str]] = {
        "full_name":           ["name", "full name", "what should i call you"],
        "email":               ["email", "e-mail", "email address"],
        "phone":               ["phone", "phone number", "contact number", "reach you"],
        "years_of_experience": ["years", "experience", "how long", "how many years"],
        "desired_positions":   ["position", "role", "applying for", "interested in"],
        "current_location":    ["location", "located", "city", "where are you", "based"],
        "tech_stack":          ["tech stack", "technologies", "languages", "frameworks",
                                "tools", "proficient", "stack"],
    }

    def extract_candidate_info(self, conversation_history: list[dict]) -> dict:
        """
        Extract candidate fields from the conversation history.

        Uses a context-aware strategy: for each user message, checks the
        preceding assistant message to determine which field was being asked.
        This handles re-entries gracefully — if the chatbot asks for a field
        again (e.g. invalid phone), the latest answer overwrites the previous.
        Falls back to regex scanning for email and phone patterns.
        """
        candidate_data: dict = {field: "Not provided" for field in self.FIELD_ORDER}

        # Walk through the conversation as (assistant, user) pairs
        for i, msg in enumerate(conversation_history):
            if msg["role"] != "user":
                continue

            # Skip the hidden greeting trigger
            if i == 0 and "apply for a position" in msg["content"].lower():
                continue

            # Find the assistant message that preceded this user message
            assistant_text = ""
            if i > 0 and conversation_history[i - 1]["role"] == "assistant":
                assistant_text = conversation_history[i - 1]["content"].lower()

            # Match the assistant's question to a field
            matched_field = self._detect_field(assistant_text)
            if matched_field:
                candidate_data[matched_field] = msg["content"].strip()

        # Regex fallback for email (in case keyword matching missed it)
        if not validate_email(candidate_data.get("email", "")):
            all_user_msgs = [m["content"] for m in conversation_history if m["role"] == "user"]
            email_match = self._find_email_in_messages(all_user_msgs)
            if email_match:
                candidate_data["email"] = email_match

        # Regex fallback for phone
        if not validate_phone(candidate_data.get("phone", "")):
            all_user_msgs = [m["content"] for m in conversation_history if m["role"] == "user"]
            phone_match = self._find_phone_in_messages(all_user_msgs)
            if phone_match:
                candidate_data["phone"] = phone_match

        # Metadata
        candidate_data["extracted_at"] = datetime.now().isoformat()
        candidate_data["total_messages"] = len(conversation_history)

        return candidate_data

    def _detect_field(self, assistant_text: str) -> str | None:
        """Determine which field the assistant was asking about."""
        for field, keywords in self._FIELD_KEYWORDS.items():
            if any(kw in assistant_text for kw in keywords):
                return field
        return None

    def save_candidate(self, candidate_data: dict) -> str:
        """
        Save candidate data as a timestamped JSON file.

        Returns:
            The file path of the saved JSON file.
        """
        CANDIDATES_DIR.mkdir(exist_ok=True)

        name = candidate_data.get("full_name", "unknown")
        safe_name = re.sub(r"[^a-zA-Z0-9]", "_", name.lower()).strip("_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}.json"

        filepath = CANDIDATES_DIR / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(candidate_data, f, indent=2, ensure_ascii=False)

        return str(filepath)

    def list_candidates(self) -> list[dict]:
        """Load and return all previously saved candidate records."""
        if not CANDIDATES_DIR.exists():
            return []

        candidates = []
        for filepath in sorted(CANDIDATES_DIR.glob("*.json")):
            with open(filepath, "r", encoding="utf-8") as f:
                candidates.append(json.load(f))

        return candidates

    # ── Private helpers ──────────────────────────────────────────────────

    @staticmethod
    def _find_email_in_messages(messages: list[str]) -> str | None:
        """Scan all messages for an email pattern."""
        pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
        for msg in messages:
            match = re.search(pattern, msg)
            if match:
                return match.group()
        return None

    @staticmethod
    def _find_phone_in_messages(messages: list[str]) -> str | None:
        """Scan all messages for a phone number pattern."""
        pattern = r"[\+]?[\d\s\-\(\)]{7,15}"
        for msg in messages:
            match = re.search(pattern, msg)
            if match:
                cleaned = match.group().strip()
                if len(re.sub(r"\D", "", cleaned)) >= 7:
                    return cleaned
        return None


def generate_candidate_summary_text(candidate_data: dict) -> str:
    """Generate a formatted plain-text summary for export/download."""
    name = candidate_data.get("full_name", "N/A")
    email = candidate_data.get("email", "N/A")
    phone = candidate_data.get("phone", "N/A")
    experience = candidate_data.get("years_of_experience", "N/A")
    positions = candidate_data.get("desired_positions", "N/A")
    location = candidate_data.get("current_location", "N/A")
    tech = candidate_data.get("tech_stack", "N/A")
    extracted = candidate_data.get("extracted_at", "N/A")
    total_msgs = candidate_data.get("total_messages", "N/A")

    return (
        "=" * 60 + "\n"
        "       TALENTSCOUT — CANDIDATE SCREENING SUMMARY\n"
        "=" * 60 + "\n\n"
        f"  Full Name          : {name}\n"
        f"  Email              : {email}\n"
        f"  Phone              : {phone}\n"
        f"  Years of Experience: {experience}\n"
        f"  Desired Position(s): {positions}\n"
        f"  Current Location   : {location}\n"
        f"  Tech Stack         : {tech}\n\n"
        "-" * 60 + "\n"
        f"  Extracted At       : {extracted}\n"
        f"  Total Messages     : {total_msgs}\n"
        "-" * 60 + "\n\n"
        "  Thank you for using TalentScout Hiring Assistant!\n"
    )
