"""
ImpactAI — Groq Cloud AI client (replaces OpenAI).

Uses the Groq Python SDK to call Llama‑3 (or whichever model is
configured via GROQ_MODEL).  The assistant returns structured JSON
with text, severity, and suggestions.
"""

import json
from typing import Dict, List, Optional

from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL

_client: Optional[Groq] = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set.  "
                "Add it to Backend/.env  →  GROQ_API_KEY=gsk_..."
            )
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


SYSTEM_PROMPT = (
    "You are ImpactAI, a compassionate mental health support assistant. "
    "Answer with empathy, safety, and clarity. "
    "Output ONLY valid JSON (no markdown, no code fences) with exactly these fields:\n"
    '  "text": "<your empathetic response>",\n'
    '  "severity": "<low | medium | high | crisis>",\n'
    '  "suggestions": ["<short supportive action 1>", "<action 2>", "<action 3>"]\n'
    "Severity guide:\n"
    "  low     — general wellness question or positive feeling\n"
    "  medium  — mild distress, anxiety, or sadness\n"
    "  high    — significant distress, self-harm ideation without plan\n"
    "  crisis  — active suicidal ideation, self-harm plan, or emergency\n"
    "If severity is crisis, always include emergency helpline numbers "
    "(988 Suicide & Crisis Lifeline, 741741 Crisis Text Line).\n"
    "Do NOT include any additional keys."
)


def _normalize_response(response_text: str) -> Dict:
    """
    Parse AI output.  If the model wraps it in ```json ... ``` fences,
    strip them first.
    """
    cleaned = response_text.strip()
    # Strip markdown code fences if present
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "text": response_text.strip(),
            "severity": "low",
            "suggestions": ["Please try again or rephrase your message."],
        }


def generate_ai_chat(
    message: str,
    history: Optional[List[Dict]] = None,
) -> Dict:
    """
    Send a user message (+optional conversation history) to Groq Cloud
    and return a normalised dict with keys: text, severity, suggestions.
    """
    client = _get_client()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})

    chat_completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=512,
    )

    raw_text = chat_completion.choices[0].message.content.strip()
    parsed = _normalize_response(raw_text)

    # ── Validate & fill defaults ───────────────────────────────────────────
    if "text" not in parsed:
        parsed["text"] = raw_text
    if parsed.get("severity") not in {"low", "medium", "high", "crisis"}:
        parsed["severity"] = "low"
    parsed["suggestions"] = parsed.get("suggestions") or [
        "Take a moment to breathe.",
        "Reach out to a friend you trust.",
        "Consider speaking with a counselor.",
    ]
    if not isinstance(parsed["suggestions"], list):
        parsed["suggestions"] = [str(parsed["suggestions"])]

    return parsed
