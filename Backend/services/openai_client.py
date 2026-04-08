import json
from typing import Dict, List, Optional

import openai

from config import OPENAI_API_KEY

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

SYSTEM_PROMPT = (
    "You are ImpactAI, a mental health support assistant. "
    "Answer with empathy, safety, and clarity. "
    "Output only valid JSON with the following fields: "
    "text, severity, suggestions. "
    "Severity must be one of: low, medium, high, crisis. "
    "Suggestions should be an array of short supportive actions. "
    "Do not include any additional keys."
)


def _normalize_response(response_text: str) -> Dict:
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return {
            "text": response_text.strip(),
            "severity": "low",
            "suggestions": ["Please try again or rephrase your request."],
        }


def generate_ai_chat(message: str, history: Optional[List[Dict]] = None) -> Dict:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set in the backend environment.")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": message})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.75,
        max_tokens=400,
    )

    raw_text = response.choices[0].message.content.strip()
    parsed = _normalize_response(raw_text)

    if "text" not in parsed:
        parsed["text"] = raw_text
    if parsed.get("severity") not in {"low", "medium", "high", "crisis"}:
        parsed["severity"] = "low"
    parsed["suggestions"] = parsed.get("suggestions") or ["Please try again if you need more help."]

    if not isinstance(parsed["suggestions"], list):
        parsed["suggestions"] = [str(parsed["suggestions"])]

    return parsed
