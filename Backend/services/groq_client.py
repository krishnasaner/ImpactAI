"""
ImpactAI — Groq Cloud AI client and response validation engine.

Uses the Groq Python SDK to call Llama-3 (or whichever model is
configured via GROQ_MODEL). The assistant returns structured JSON
with text, severity, and suggestions. The module enforces strict Pydantic
schema validation and provides categorized fallback behavior.
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Literal, Optional

from groq import AsyncGroq, Groq
from pydantic import BaseModel, Field, ValidationError

from config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

# Reusable client singletons
_sync_client: Optional[Groq] = None
_async_client: Optional[AsyncGroq] = None

REQUEST_TIMEOUT_SECONDS = 15.0


def get_sync_client() -> Groq:
    global _sync_client
    if _sync_client is None:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not configured.")
        _sync_client = Groq(api_key=GROQ_API_KEY, timeout=REQUEST_TIMEOUT_SECONDS)
    return _sync_client


def get_async_client() -> AsyncGroq:
    global _async_client
    if _async_client is None:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not configured.")
        _async_client = AsyncGroq(api_key=GROQ_API_KEY, timeout=REQUEST_TIMEOUT_SECONDS)
    return _async_client


# ── Strict Pydantic Response Schema ──────────────────────────────────────────

class ZenithOutput(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000)
    severity: Literal["low", "medium", "high", "crisis"] = "low"
    emotion: Optional[str] = "neutral"
    intent: Optional[str] = "general_wellness"
    suggestions: List[str] = Field(default_factory=list, max_length=5)
    requires_followup: Optional[bool] = False


# ── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are Zenith, a perceptive, warm, and grounded mental wellness companion for college students on ImpactAI.
You chat naturally — like an experienced mentor who deeply understands academic, social, and emotional college life.

## Core Conversational Rules
1. SPECIFICITY OVER CLICHES: Never start with canned opening lines like "I'm sorry you're feeling that way", "You are not alone", "Try taking a deep breath", or "Everything will be okay". Respond directly to what the student actually said.
2. CONTEXTUAL RELEVANCE:
   - If they failed an exam or are stressed about grades, acknowledge the pressure and parental expectations honestly; do not offer shallow toxic positivity. Help them think through the immediate next step.
   - If they can't concentrate or keep scrolling, explore whether it is fatigue, overwhelm, or avoidance before suggesting a realistic 5-minute intervention.
   - If friends are ignoring them, acknowledge the pain without making assumptions about others' motives.
   - If they ask for practical study assistance, offer practical study structuring without imposing an unneeded mental health assessment.
3. ADAPTIVE LENGTH: Match your length to the student's message. Use 2 to 4 clear, thoughtful sentences for standard messages. Do not deliver mini-essays.
4. NO MEDICAL CLAIMS: You are not a doctor, psychiatrist, or licensed therapist. Do not diagnose conditions or suggest medication.
5. NO QUESTION OVERKILL: Ask at most ONE natural, open-ended question only when it genuinely moves the reflection forward. Do not end every turn with an interrogation.

## Output Format
Output ONLY valid JSON with no markdown fences or wrapper formatting:
{
  "text": "<your conversational response>",
  "severity": "<low | medium | high | crisis>",
  "emotion": "<anxiety | sadness | overwhelm | anger | calm | neutral>",
  "intent": "<academic_stress | exam_anxiety | relationship | sleep | social | general_wellness>",
  "suggestions": ["<short actionable tip 1>", "<short actionable tip 2>"],
  "requires_followup": false
}

## Severity Triage
- low     : Everyday thoughts, coursework planning, positive reflection, or light study stress.
- medium  : Noticeable distress, sadness, feeling overwhelmed, insomnia, or social anxiety.
- high    : Intense panic, severe emotional pain, trauma, hopelessness without explicit self-harm plan.
- crisis  : Explicit suicidal ideation, self-harm plan, or acute safety danger.

## Crisis Protocol
If severity is crisis, provide immediate, calm warmth and always prioritize India emergency helplines:
Tele-MANAS (14416 / 1800-89-14416), AASRA (+91-22-27546669), and Emergency (112).
"""

# ── Categorized Fallback Responses ───────────────────────────────────────────

CRISIS_RESOURCES = [
    "Call Tele-MANAS (Toll-Free, 24/7): 14416 or 1800-89-14416",
    "Call AASRA Helpline: +91-22-27546669",
    "Emergency Services: 112",
]

FALLBACK_RESPONSES = {
    "crisis": {
        "text": (
            "I hear how much pain you're carrying right now, and your safety is the most important thing. "
            "You do not have to carry this alone. Please reach out to someone who can help you right now: "
            "Tele-MANAS helpline is available 24/7 at 14416 (or 1800-89-14416), AASRA is at +91-22-27546669, "
            "or contact emergency services at 112. Are you in a safe place right now?"
        ),
        "severity": "crisis",
        "suggestions": CRISIS_RESOURCES,
    },
    "rate_limit": {
        "text": (
            "Zenith is currently receiving a high volume of student messages. "
            "I want to make sure I give your thoughts the care they deserve. "
            "Please take a slow, deep breath, and try sending your message again in a moment."
        ),
        "severity": "low",
        "suggestions": [
            "Try a 4-7-8 relaxation breath in the Breathing section",
            "Pause for 30 seconds and take a sip of water",
            "Retry your message in a few moments",
        ],
    },
    "timeout": {
        "text": (
            "I apologize, but my response took a little longer than expected to process. "
            "Your message matters to me — please send it again, and I'll be right here to continue."
        ),
        "severity": "low",
        "suggestions": [
            "Resend your message",
            "Try a grounding exercise",
            "Check out our guided wellness exercises",
        ],
    },
    "missing_config": {
        "text": (
            "Thank you for reaching out. Zenith AI is currently running in local offline mode. "
            "Please know that your feelings are valid. You can explore our guided breathing exercises, "
            "wellness articles, and student counseling booking while AI cloud services are being configured."
        ),
        "severity": "low",
        "suggestions": [
            "Explore guided breathing exercises",
            "Browse student wellness resources",
            "Book a session with a campus counselor",
        ],
    },
    "service_error": {
        "text": (
            "Thank you for sharing that with me. Even though our cloud AI service is experiencing a temporary "
            "delay, you are not alone. Take things one gentle breath at a time. If you need immediate "
            "support, campus counselors and student wellness resources are always here for you."
        ),
        "severity": "low",
        "suggestions": [
            "Practice a quick 4-7-8 breathing exercise",
            "Reach out to a trusted friend or counselor",
            "Take a short five-minute walk or stretch",
        ],
    },
}


def get_fallback(category: str = "service_error", is_crisis: bool = False) -> Dict:
    """Return a well-structured fallback response based on error category and safety state."""
    if is_crisis:
        return dict(FALLBACK_RESPONSES["crisis"])
    return dict(FALLBACK_RESPONSES.get(category, FALLBACK_RESPONSES["service_error"]))


# ── Strict Response Sanitization & Validation ─────────────────────────────────

def sanitize_and_parse_response(raw_text: str, is_crisis: bool = False) -> Dict:
    """
    Parse and validate raw model output using Pydantic.
    Handles markdown code fences, embedded JSON blocks, and field cleaning.
    """
    cleaned = raw_text.strip()

    # 1. Strip markdown fences if present
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()

    # 2. If text contains non-JSON text surrounding a JSON block, extract JSON
    json_match = re.search(r"(\{[\s\S]*\})", cleaned)
    if json_match:
        candidate_json = json_match.group(1)
    else:
        candidate_json = cleaned

    try:
        data = json.loads(candidate_json)
        # Clean suggestions: strip whitespace, filter out empty strings, cap lengths
        raw_sugg = data.get("suggestions", [])
        if isinstance(raw_sugg, list):
            cleaned_sugg = [str(s).strip()[:100] for s in raw_sugg if str(s).strip()][:4]
        elif isinstance(raw_sugg, str) and raw_sugg.strip():
            cleaned_sugg = [raw_sugg.strip()[:100]]
        else:
            cleaned_sugg = []

        candidate_text = str(data.get("text") or data.get("reply") or "").strip()
        validated = ZenithOutput(
            text=candidate_text,
            severity=data.get("severity", "low"),
            emotion=data.get("emotion", "neutral"),
            intent=data.get("intent", "general_wellness"),
            suggestions=cleaned_sugg,
            requires_followup=bool(data.get("requires_followup", False)),
        )

        result = validated.model_dump()
        result["reply"] = result["text"]

        # If crisis was deterministically detected upstream, prevent LLM downgrade
        if is_crisis:
            result["severity"] = "crisis"
            if not any("14416" in s for s in result["suggestions"]):
                result["suggestions"] = CRISIS_RESOURCES[:2] + result["suggestions"][:2]

        if not result["suggestions"]:
            result["suggestions"] = [
                "Take a moment to breathe slowly",
                "Write down what you are feeling",
            ]

        return result

    except (json.JSONDecodeError, ValidationError) as err:
        logger.warning("Failed to validate Zenith AI JSON output (%s). Raw: %s", err, raw_text[:200])
        # If model returned pure text without valid JSON, salvage the text if readable
        if len(cleaned) > 20 and not cleaned.startswith("{") and not cleaned.startswith("["):
            severity = "crisis" if is_crisis else "low"
            return {
                "text": cleaned[:1000],
                "severity": severity,
                "suggestions": CRISIS_RESOURCES if is_crisis else [
                    "Take a slow, calming breath",
                    "Talk to someone you trust",
                ],
            }
        return get_fallback("service_error", is_crisis=is_crisis)


# ── AI Generation Calls ───────────────────────────────────────────────────────

async def generate_ai_chat_async(
    message: str,
    history: Optional[List[Dict]] = None,
    is_crisis: bool = False,
) -> Dict:
    """
    Asynchronously send a user message (+ conversation history) to Groq Cloud.
    Returns validated dict: {"text": str, "severity": str, "suggestions": list}.
    """
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY is not configured; returning fallback.")
        return get_fallback("missing_config", is_crisis=is_crisis)

    try:
        client = get_async_client()
    except Exception as exc:
        logger.error("Failed to initialize AsyncGroq client: %s", exc)
        return get_fallback("missing_config", is_crisis=is_crisis)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})

    # Call with controlled timeout and retries
    retries = 1
    for attempt in range(retries + 1):
        try:
            chat_completion = await asyncio.wait_for(
                client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=512,
                ),
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            raw_text = chat_completion.choices[0].message.content or ""
            return sanitize_and_parse_response(raw_text, is_crisis=is_crisis)

        except asyncio.TimeoutError:
            logger.warning("Groq API timed out after %ss (attempt %d)", REQUEST_TIMEOUT_SECONDS, attempt + 1)
            if attempt == retries:
                return get_fallback("timeout", is_crisis=is_crisis)

        except Exception as exc:
            err_str = str(exc).lower()
            logger.error("Groq API request failed (attempt %d, model=%s): %s", attempt + 1, GROQ_MODEL, exc)
            if "rate_limit" in err_str or "429" in err_str:
                if attempt == retries:
                    return get_fallback("rate_limit", is_crisis=is_crisis)
                await asyncio.sleep(1.0)
            elif "401" in err_str or "auth" in err_str:
                return get_fallback("missing_config", is_crisis=is_crisis)
            else:
                if attempt == retries:
                    return get_fallback("service_error", is_crisis=is_crisis)
                await asyncio.sleep(0.5)

    return get_fallback("service_error", is_crisis=is_crisis)


def generate_ai_chat(
    message: str,
    history: Optional[List[Dict]] = None,
    is_crisis: bool = False,
) -> Dict:
    """Synchronous wrapper for generate_ai_chat_async."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.run_coroutine_threadsafe(
                generate_ai_chat_async(message, history, is_crisis=is_crisis), loop
            ).result()
    except Exception:
        pass
    return asyncio.run(generate_ai_chat_async(message, history, is_crisis=is_crisis))
