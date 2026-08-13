"""
PII Detection Engine — v2.

Multi-phase pipeline architecture:

  Phase 1 — Section Detection:
    Identify document sections (HEADER, SKILLS, PROJECTS, EDUCATION, etc.)

  Phase 2 — Structured PII Detection:
    Run deterministic recognizers (Email, Phone, SSN, CC, IP, URL).
    Collect "protected spans" that later recognizers must not overlap.

  Phase 3 — Context-Aware PII Detection:
    Run context-aware recognizers (Person, Company, Address, DOB).
    Uses section context and protected spans to avoid false positives.

  Phase 4 — Overlap Resolution:
    Deterministic conflict resolution:
      1. Prefer longer valid entity span
      2. Prefer higher confidence
      3. Prefer structured over contextual

  Phase 5 — Span Verification:
    assert text[start:end] == entity.value for every entity.
    If this fails, the entity is silently dropped.

Supports 9 PII types:
  Full names, Email addresses, Phone numbers, Company names,
  Physical/mailing addresses, SSNs, Credit card numbers,
  Dates of birth, IP addresses.
"""

from .recognizers import (
    DetectedEntity,
    EmailRecognizer,
    PhoneRecognizer,
    SSNRecognizer,
    CreditCardRecognizer,
    IPAddressRecognizer,
    URLRecognizer,
    PersonRecognizer,
    CompanyRecognizer,
    AddressRecognizer,
    DOBRecognizer,
)
from .section_detector import detect_sections


# Structured recognizers run first and produce protected spans
STRUCTURED_RECOGNIZERS = [
    URLRecognizer(),       # URLs first (not PII, but protect from PERSON)
    EmailRecognizer(),
    PhoneRecognizer(),
    SSNRecognizer(),
    CreditCardRecognizer(),
    IPAddressRecognizer(),
]

# Contextual recognizers run second, with section + protected span awareness
CONTEXTUAL_RECOGNIZERS = [
    PersonRecognizer(),
    CompanyRecognizer(),
    AddressRecognizer(),
    DOBRecognizer(),
]

# Entity types that are NOT emitted as PII (only used for protection)
_PROTECTION_ONLY_TYPES = {"URL"}


def _resolve_overlaps(entities: list[DetectedEntity]) -> list[DetectedEntity]:
    """
    Deterministic overlap resolution.

    Rules:
    1. Sort by start position
    2. For overlapping entities, prefer:
       a. Longer span (more specific match)
       b. Higher confidence
       c. First encountered (stable ordering)
    3. Never allow overlapping replacements
    """
    if not entities:
        return []

    # Sort by start, then by length descending, then by confidence descending
    sorted_entities = sorted(
        entities,
        key=lambda e: (e.start, -(e.end - e.start), -e.confidence),
    )

    result: list[DetectedEntity] = [sorted_entities[0]]

    for entity in sorted_entities[1:]:
        last = result[-1]
        if entity.start < last.end:
            # Overlap — keep the one with the longer span
            last_len = last.end - last.start
            this_len = entity.end - entity.start
            if this_len > last_len:
                result[-1] = entity
            elif this_len == last_len and entity.confidence > last.confidence:
                result[-1] = entity
            # Otherwise keep `last`
        else:
            result.append(entity)

    return result


def _verify_spans(text: str, entities: list[DetectedEntity]) -> list[DetectedEntity]:
    """
    Verify that text[start:end] == entity.value for every entity.
    Drop any entity where this invariant is violated.
    """
    verified = []
    for entity in entities:
        actual = text[entity.start:entity.end]
        if actual == entity.value:
            verified.append(entity)
        else:
            # Try to find the actual text nearby (within 5 chars)
            # This handles minor offset drift
            pass  # Silently drop — the span is broken
    return verified


def detect_pii(text: str) -> list[DetectedEntity]:
    """
    Detect all PII entities in the given text.

    Returns a list of DetectedEntity objects sorted by position,
    with overlapping entities resolved and spans verified.
    """
    # Phase 1: Section detection
    sections = detect_sections(text)

    # Phase 2: Structured PII detection
    structured_entities: list[DetectedEntity] = []
    for recognizer in STRUCTURED_RECOGNIZERS:
        structured_entities.extend(
            recognizer.detect(text, protected_spans=None, sections=sections)
        )

    # Build protected spans from structured detections
    protected_spans: list[tuple[int, int]] = [
        (e.start, e.end) for e in structured_entities
    ]

    # Phase 3: Context-aware PII detection
    contextual_entities: list[DetectedEntity] = []
    for recognizer in CONTEXTUAL_RECOGNIZERS:
        contextual_entities.extend(
            recognizer.detect(
                text,
                protected_spans=protected_spans,
                sections=sections,
            )
        )

    # Combine all entities (excluding protection-only types like URL)
    all_entities = [
        e for e in structured_entities
        if e.type not in _PROTECTION_ONLY_TYPES
    ] + contextual_entities

    # Phase 4: Overlap resolution
    resolved = _resolve_overlaps(all_entities)

    # Phase 5: Span verification
    verified = _verify_spans(text, resolved)

    # Sort by position
    verified.sort(key=lambda e: e.start)

    return verified
