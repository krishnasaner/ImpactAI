"""
ImpactAI — Groq Cloud AI client.

Uses the Groq Python SDK to call Llama‑3 (or whichever model is
configured via GROQ_MODEL).  The assistant returns structured JSON
with text, severity, and suggestions — but the "text" field reads
like a warm, natural conversation, not a clinical template.
"""

import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

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


SYSTEM_PROMPT = """\
You are ImpactAI, a warm and empathetic mental health companion. You chat naturally — like a caring friend who also happens to be knowledgeable about mental wellness.

## Conversation Rules
- Be conversational, warm, and genuine. Use natural language — NOT clinical jargon.
- Keep responses concise (2-4 sentences max for normal exchanges). Be brief when the user is brief.
- Actually respond to what the user SAID. Reference their specific words. Don't give generic advice.
- Ask ONE thoughtful follow-up question when appropriate — not multiple.
- Vary your tone to match the user: casual with casual users, gentler when someone is upset.
- NEVER start with "I'm here to listen and support you" or similar canned openers.
- NEVER list suggestions in your main response text — that goes in the suggestions field only.
- If the user says "hi" or "hello", just greet them back naturally and ask how they're doing.

## Output Format
Output ONLY valid JSON (no markdown, no code fences) with exactly these fields:
  "text": "<your natural, conversational response>",
  "severity": "<low | medium | high | crisis>",
  "suggestions": ["<short action 1>", "<action 2>", "<action 3>"]

## Severity Guide
  low     — general chat, wellness question, or positive feeling
  medium  — mild distress, anxiety, sadness, or stress
  high    — significant distress, self-harm ideation without plan
  crisis  — active suicidal ideation, self-harm plan, or emergency

## Crisis Protocol
If severity is crisis, include India emergency helpline numbers in your response text naturally:
  Tele-MANAS 14416 / 1800-89-14416, AASRA +91-22-27546669, Emergency 112.

## Suggestions Field
The suggestions array should contain 2-3 short, actionable things (not generic platitudes).
Examples: "Try a 5-minute walk outside", "Write down 3 things that went well today", "Text a friend you trust"

Do NOT include any additional JSON keys.
"""


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

    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.75,
            max_tokens=512,
        )
    except Exception as exc:
        logger.error(
            "Groq API request failed (model=%s): %s",
            GROQ_MODEL,
            exc,
        )
        raise

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
