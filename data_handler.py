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

    # Field order matches the system prompt's collection sequence
    FIELD_ORDER: list[str] = [
        "full_name",
        "email",
        "phone",
        "years_of_experience",
        "desired_positions",
        "current_location",
        "tech_stack",
    ]

    def extract_candidate_info(self, conversation_history: list[dict]) -> dict:
        """
        Extract candidate fields from the conversation history.

        Uses a dual strategy:
          1. Index-based mapping (user message N → field N)
          2. Regex fallback for email and phone patterns
        """
        user_messages = [
            msg["content"]
            for msg in conversation_history
            if msg["role"] == "user"
        ]

        # Skip the first message (hidden greeting trigger)
        actual_responses = user_messages[1:] if len(user_messages) > 1 else []

        candidate_data: dict = {}

        # Strategy A — Index-based extraction
        for idx, field_name in enumerate(self.FIELD_ORDER):
            if idx < len(actual_responses):
                candidate_data[field_name] = actual_responses[idx].strip()
            else:
                candidate_data[field_name] = "Not provided"

        # Strategy B — Regex fallback for email
        if not validate_email(candidate_data.get("email", "")):
            email_match = self._find_email_in_messages(actual_responses)
            if email_match:
                candidate_data["email"] = email_match

        # Strategy B — Regex fallback for phone
        if not validate_phone(candidate_data.get("phone", "")):
            phone_match = self._find_phone_in_messages(actual_responses)
            if phone_match:
                candidate_data["phone"] = phone_match

        # Metadata
        candidate_data["extracted_at"] = datetime.now().isoformat()
        candidate_data["total_messages"] = len(conversation_history)

        return candidate_data

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
