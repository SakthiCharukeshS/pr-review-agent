"""Hide secrets before they reach the AI or a public PR comment.

Redaction is pattern-based, so it is a safety net, not a guarantee.
"""

import re

REDACTED = "[REDACTED]"

# Well-known token formats: the whole token is replaced.
_TOKEN_PATTERNS = [
    re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
        re.DOTALL,
    ),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{8,}"),
]

# Secret-looking assignments:  API_KEY = "value"   "password": 'value'
# Only the value is replaced, so the variable name stays visible to the reviewer.
_ASSIGNMENT = re.compile(
    r"(?P<head>(?:password|passwd|pwd|secret|token|api[_-]?key|apikey|credential"
    r"|private[_-]?key)[A-Za-z0-9_\-]{0,40}[\"']?\s*[:=]\s*)"
    r"(?P<quote>[\"'])(?P<value>[^\"'\n]{3,})(?P=quote)",
    re.IGNORECASE,
)


def redact_secrets(text: str) -> str:
    """Returns the text with secret values replaced by [REDACTED]."""
    if not text:
        return text
    for pattern in _TOKEN_PATTERNS:
        text = pattern.sub(REDACTED, text)
    return _ASSIGNMENT.sub(
        lambda m: f"{m['head']}{m['quote']}{REDACTED}{m['quote']}", text
    )