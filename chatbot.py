"""
chatbot.py — Groq/Llama API wrapper for TalentScout Hiring Assistant.

Encapsulates all LLM interaction: client setup, message dispatch,
and conversation history management.
"""

import os
from groq import Groq
from prompts import SYSTEM_PROMPT


class TalentScoutChatbot:
    """Manages a stateful conversation with Llama 3.3 via the Groq API."""

    MODEL_ID: str = "llama-3.3-70b-versatile"
    MAX_OUTPUT_TOKENS: int = 1024

    def __init__(self) -> None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable is not set. "
                "Create a .env file — see .env.example for the template."
            )

        self.client = Groq(api_key=api_key)
        self.conversation_history: list[dict] = []

    def chat(self, user_message: str) -> str:
        """
        Send a message and return the model's response.

        The full conversation history (system prompt + all prior messages)
        is sent on every call so the model retains context.
        """
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
        })

        # Build message list: system instruction first, then full history
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *self.conversation_history,
        ]

        response = self.client.chat.completions.create(
            model=self.MODEL_ID,
            messages=messages,
            max_tokens=self.MAX_OUTPUT_TOKENS,
            temperature=0.7,
        )

        assistant_text: str = response.choices[0].message.content

        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_text,
        })

        return assistant_text

    def get_history(self) -> list[dict]:
        """Return the full conversation history."""
        return self.conversation_history

    def reset(self) -> None:
        """Clear history for a new interview session."""
        self.conversation_history = []
