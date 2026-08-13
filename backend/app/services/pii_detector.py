"""
PII Detection Engine.

Uses regex patterns with context-aware scoring to detect 9 types of PII:
- Full names
- Email addresses
- Phone numbers
- Company names
- Physical/mailing addresses
- Social Security Numbers (SSNs)
- Credit card numbers
- Dates of birth
- IP addresses
"""

import re
from dataclasses import dataclass, field


@dataclass
class DetectedEntity:
    """Raw detected PII entity before pseudonymization."""
    type: str
    value: str
    start: int
    end: int
    confidence: float
    context: str = ""


# ──────────────────────────────────────────────
# Regex patterns for each PII type
# ──────────────────────────────────────────────

PATTERNS: dict[str, list[tuple[re.Pattern, float]]] = {
    "EMAIL": [
        (re.compile(
            r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
        ), 0.99),
    ],
    "SSN": [
        # Standard format: 123-45-6789
        (re.compile(
            r'\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b'
        ), 0.95),
        # No dashes: 123456789 (only in context)
        (re.compile(
            r'\b(?!000|666|9\d{2})\d{3}(?!00)\d{2}(?!0000)\d{4}\b'
        ), 0.60),
    ],
    "CREDIT_CARD": [
        # Visa
        (re.compile(r'\b4\d{3}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'), 0.95),
        # Mastercard
        (re.compile(r'\b5[1-5]\d{2}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'), 0.95),
        # Amex
        (re.compile(r'\b3[47]\d{2}[\s\-]?\d{6}[\s\-]?\d{5}\b'), 0.95),
        # Discover
        (re.compile(r'\b6(?:011|5\d{2})[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'), 0.95),
        # Generic 16-digit
        (re.compile(r'\b\d{4}[\s\-]\d{4}[\s\-]\d{4}[\s\-]\d{4}\b'), 0.80),
    ],
    "PHONE": [
        # US format: (555) 867-5309 or 555-867-5309 or +1-555-867-5309
        (re.compile(
            r'(?:\+?1[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}\b'
        ), 0.92),
        # International format
        (re.compile(
            r'\+\d{1,3}[\s\-.]?\(?\d{1,4}\)?[\s\-.]?\d{3,4}[\s\-.]?\d{3,4}\b'
        ), 0.85),
    ],
    "IP_ADDRESS": [
        # IPv4
        (re.compile(
            r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b'
        ), 0.97),
        # IPv6 (simplified)
        (re.compile(
            r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
        ), 0.95),
    ],
    "DOB": [
        # MM/DD/YYYY or MM-DD-YYYY
        (re.compile(
            r'\b(?:0[1-9]|1[0-2])[/\-](?:0[1-9]|[12]\d|3[01])[/\-](?:19|20)\d{2}\b'
        ), 0.80),
        # YYYY-MM-DD (ISO)
        (re.compile(
            r'\b(?:19|20)\d{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])\b'
        ), 0.80),
        # Month DD, YYYY (e.g., January 15, 1990)
        (re.compile(
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(?:19|20)\d{2}\b',
            re.IGNORECASE
        ), 0.85),
        # DD Month YYYY
        (re.compile(
            r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s+(?:19|20)\d{2}\b',
            re.IGNORECASE
        ), 0.85),
    ],
    "ADDRESS": [
        # US street address: 123 Main St, City, ST 12345
        (re.compile(
            r'\b\d{1,5}\s+(?:[A-Z][a-z]+\s?){1,4}'
            r'(?:Street|St\.?|Avenue|Ave\.?|Boulevard|Blvd\.?|Drive|Dr\.?|'
            r'Lane|Ln\.?|Road|Rd\.?|Way|Court|Ct\.?|Circle|Cir\.?|'
            r'Place|Pl\.?|Terrace|Ter\.?|Trail|Trl\.?|Parkway|Pkwy\.?)'
            r'(?:\s*,?\s*(?:[A-Z][a-z]+\s?){1,3})?'
            r'(?:\s*,?\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?)?',
            re.MULTILINE
        ), 0.82),
        # PO Box
        (re.compile(
            r'\bP\.?O\.?\s*Box\s+\d+\b', re.IGNORECASE
        ), 0.90),
    ],
    "PERSON": [
        # Title + Name pattern: Mr./Mrs./Dr./Prof. First Last
        (re.compile(
            r'\b(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Prof\.?)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b'
        ), 0.90),
        # Two or three capitalized words (generic name pattern)
        (re.compile(
            r'\b[A-Z][a-z]{1,15}\s+(?:[A-Z]\.?\s+)?[A-Z][a-z]{1,15}\b'
        ), 0.65),
    ],
    "COMPANY": [
        # Company with suffix: Inc., LLC, Corp., Ltd., etc.
        (re.compile(
            r'\b(?:[A-Z][A-Za-z&\'\-]*\s*){1,5}'
            r'(?:Inc\.?|LLC|L\.L\.C\.?|Corp\.?|Corporation|'
            r'Ltd\.?|Limited|Co\.?|Company|Group|Holdings|'
            r'Partners|Associates|Enterprises|International|'
            r'Technologies|Solutions|Services|Industries|Systems)\b'
        ), 0.88),
    ],
}

# Context keywords that boost confidence for ambiguous patterns
CONTEXT_BOOSTERS: dict[str, list[str]] = {
    "PERSON": ["name", "named", "contact", "employee", "mr", "mrs", "ms", "dr", "prof",
               "sir", "madam", "patient", "client", "applicant", "defendant", "plaintiff",
               "witness", "subject", "recipient", "sender", "author", "signed", "behalf"],
    "DOB": ["born", "birth", "birthday", "dob", "date of birth", "age", "birthdate",
            "born on", "d.o.b", "natal"],
    "SSN": ["ssn", "social security", "social", "ss#", "ss #", "tax id", "taxpayer",
            "social security number", "ein"],
    "CREDIT_CARD": ["card", "credit", "debit", "visa", "mastercard", "amex",
                    "american express", "discover", "payment", "account number",
                    "card number", "cc#", "cc #"],
    "PHONE": ["phone", "call", "tel", "telephone", "mobile", "cell", "fax",
              "contact number", "reach", "dial"],
    "ADDRESS": ["address", "street", "avenue", "boulevard", "road", "city",
                "state", "zip", "postal", "mailing", "residence", "located",
                "lives at", "resides"],
    "EMAIL": ["email", "e-mail", "mail", "contact", "send", "write to", "reach"],
    "IP_ADDRESS": ["ip", "address", "server", "host", "network", "connection",
                   "logged from", "accessed from"],
    "COMPANY": ["company", "corporation", "employer", "organization", "firm",
                "business", "enterprise", "works at", "employed by"],
}

# How much context boosts confidence
CONTEXT_BOOST = 0.10
MAX_CONFIDENCE = 1.0


def _get_context(text: str, start: int, end: int, window: int = 80) -> str:
    """Extract surrounding context for a match."""
    ctx_start = max(0, start - window)
    ctx_end = min(len(text), end + window)
    return text[ctx_start:ctx_end]


def _check_context_boost(text: str, start: int, end: int, entity_type: str) -> float:
    """Check if surrounding context contains keywords that boost confidence."""
    context = _get_context(text, start, end, window=120).lower()
    boosters = CONTEXT_BOOSTERS.get(entity_type, [])
    for keyword in boosters:
        if keyword in context:
            return CONTEXT_BOOST
    return 0.0


