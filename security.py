"""
security.py — OWASP LLM Top 10 security layer for DocChat.

Implements:
  LLM01 - Prompt Injection detection
  LLM02 - Insecure Output Handling (PII / sensitive data in responses)
  LLM04 - Model Denial of Service (input length limits)
  LLM06 - Sensitive Information Disclosure (system prompt extraction)
"""

import re
from dataclasses import dataclass, field


# ── Thresholds ────────────────────────────────────────────────────────────────
MAX_INPUT_CHARS  = 2000   # LLM04: reject inputs longer than this
MAX_OUTPUT_CHARS = 8000   # LLM02: flag suspiciously long outputs


# ── Threat result ─────────────────────────────────────────────────────────────
@dataclass
class ThreatResult:
    safe:     bool
    threat:   str = ""          # short threat category label
    detail:   str = ""          # human-readable explanation
    severity: str = ""          # "low" | "medium" | "high"


# ── LLM01: Prompt Injection patterns ─────────────────────────────────────────
_INJECTION_PATTERNS: list[tuple[str, str]] = [
    # Direct instruction override
    (r"ignore\s+(all\s+)?(previous|prior|above|your)\s+(instructions?|prompts?|rules?|context)",
     "Instruction override attempt"),
    (r"disregard\s+(all\s+)?(previous|prior|above|your)\s+(instructions?|prompts?|rules?)",
     "Instruction override attempt"),
    (r"forget\s+(everything|all|your instructions|what you were told)",
     "Instruction override attempt"),

    # Role/persona hijacking
    (r"you\s+are\s+now\s+(?!a\s+helpful)",
     "Persona hijacking attempt"),
    (r"act\s+as\s+(if\s+you\s+are\s+)?(a\s+)?(DAN|jailbreak|unrestricted|evil|malicious)",
     "Jailbreak persona attempt"),
    (r"\bDAN\b",
     "Known jailbreak keyword (DAN)"),
    (r"pretend\s+(you\s+)?(have\s+no|don't\s+have|without)\s+(restrictions?|rules?|guidelines?|filters?)",
     "Restriction bypass attempt"),

    # System prompt extraction
    (r"(reveal|show|print|output|repeat|tell me|what is|display)\s+(your\s+)?(system\s+prompt|instructions|initial prompt|original prompt|prompt template)",
     "System prompt extraction attempt"),
    (r"what\s+(were\s+you|are\s+you)\s+(told|instructed|programmed)",
     "System prompt extraction attempt"),

    # Indirect injection via document content trigger
    (r"when\s+you\s+(read|see|find|encounter)\s+this",
     "Indirect prompt injection trigger"),
    (r"<\s*[Ss][Yy][Ss][Tt][Ee][Mm]\s*>",
     "Injected system tag"),
    (r"\[\s*[Ss][Yy][Ss][Tt][Ee][Mm]\s*\]",
     "Injected system tag"),

    # Command injection attempts
    (r"(execute|run|eval|import|os\.system|subprocess)",
     "Code execution attempt"),
]


# ── LLM06: Sensitive information disclosure patterns (in outputs) ─────────────
_OUTPUT_PII_PATTERNS: list[tuple[str, str]] = [
    # Credit card numbers
    (r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11})\b",
     "Credit card number"),

    # Social Security Numbers (US)
    (r"\b\d{3}-\d{2}-\d{4}\b",
     "SSN-pattern number"),

    # Irish PPS numbers
    (r"\b\d{7}[A-Z]{1,2}\b",
     "PPS number pattern"),

    # Passwords in output
    (r"(password|passwd|secret|api[_\s]?key|token)\s*[:=]\s*\S+",
     "Credential disclosure"),

    # System prompt echoed back
    (r"you are a helpful assistant\.\s+answer the question using only the document context",
     "System prompt leaked in output"),
]


# ── LLM02: Suspicious output content ─────────────────────────────────────────
_OUTPUT_HARM_PATTERNS: list[tuple[str, str]] = [
    (r"(step[- ]by[- ]step|instructions?|guide|how\s+to).{0,50}(make|build|create|synthesize).{0,50}(bomb|explosive|weapon|malware|virus)",
     "Harmful instructions in output"),
    (r"(here'?s?\s+how\s+to\s+hack|to\s+bypass\s+security|exploit\s+this\s+vulnerability)",
     "Exploitation guidance in output"),
]


# ── Public API ─────────────────────────────────────────────────────────────────

def check_input(query: str) -> ThreatResult:
    """
    Validate a user query before it reaches the LLM.
    Returns ThreatResult with safe=False if a threat is detected.
    """

    # LLM04: Input length DoS
    if len(query) > MAX_INPUT_CHARS:
        return ThreatResult(
            safe=False,
            threat="LLM04 — Model DoS",
            detail=f"Input too long ({len(query)} chars). Maximum allowed: {MAX_INPUT_CHARS}.",
            severity="medium",
        )

    # LLM01 + LLM06: Prompt injection / system prompt extraction
    q_lower = query.lower()
    for pattern, label in _INJECTION_PATTERNS:
        if re.search(pattern, q_lower, re.IGNORECASE):
            return ThreatResult(
                safe=False,
                threat="LLM01 — Prompt Injection",
                detail=f"Detected: {label}. This input pattern is blocked for security.",
                severity="high",
            )

    return ThreatResult(safe=True)


def check_output(response: str) -> ThreatResult:
    """
    Scan the LLM response before returning it to the user.
    Returns ThreatResult with safe=False if sensitive content is detected.
    """

    # LLM02: PII / credential leakage
    for pattern, label in _OUTPUT_PII_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE):
            return ThreatResult(
                safe=False,
                threat="LLM02 — Sensitive Data Exposure",
                detail=f"Response contains potential sensitive data: {label}.",
                severity="high",
            )

    # LLM02: Harmful content in output
    for pattern, label in _OUTPUT_HARM_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE):
            return ThreatResult(
                safe=False,
                threat="LLM02 — Insecure Output",
                detail=f"Response flagged: {label}.",
                severity="high",
            )

    return ThreatResult(safe=True)


def sanitise_input(query: str) -> str:
    """
    Light sanitisation — strip null bytes, excessive whitespace,
    and HTML/script tags that could affect downstream rendering.
    Does NOT block — call check_input() first for blocking decisions.
    """
    query = query.replace("\x00", "")                          # null bytes
    query = re.sub(r"<script.*?>.*?</script>", "", query, flags=re.IGNORECASE | re.DOTALL)
    query = re.sub(r"<[^>]+>", "", query)                      # HTML tags
    query = re.sub(r"\s{3,}", "  ", query)                     # collapse whitespace
    return query.strip()
