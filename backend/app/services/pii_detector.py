"""
PII Detection Engine — Hybrid Presidio + Contextual Validation.

Pipeline:
1. Document sections detected.
2. Microsoft Presidio Analyzer (w/ spaCy) generates candidates.
3. Protected spans (URLs, Emails, Phones) are identified.
4. Contextual validation layer filters out false positives 
   (e.g. spaCy PERSON predictions inside TECHNICAL SKILLS).
5. Deterministic overlap resolution.
"""

from dataclasses import dataclass
from typing import Optional
import re
from presidio_analyzer import RecognizerResult

from .section_detector import detect_sections
from .presidio_engine import analyze


@dataclass
class DetectedEntity:
    type: str
    value: str
    start: int
    end: int
    confidence: float
    context: str = ""
    recognizer: str = ""


# Entity types that are NOT emitted as PII (only used for protection)
_PROTECTION_ONLY_TYPES = set()

# Sections where PERSON/ORG detection from spaCy should be heavily suppressed
_SUPPRESSED_SECTIONS = {
    "SKILLS", "TECHNICAL_SKILLS", "PROJECTS", "TRAINING",
    "CERTIFICATIONS", "ACHIEVEMENTS", "EDUCATION",
}


def _get_context(text: str, start: int, end: int, window: int = 80) -> str:
    ctx_start = max(0, start - window)
    ctx_end = min(len(text), end + window)
    return text[ctx_start:ctx_end]


def _is_in_protected_span(start: int, end: int, protected_spans: list[tuple[int, int]]) -> bool:
    for ps, pe in protected_spans:
        if start < pe and end > ps:
            return True
    return False


def _is_in_suppressed_section(pos: int, sections: list) -> bool:
    for section in sections:
        if section.start <= pos < section.end:
            if section.name in _SUPPRESSED_SECTIONS:
                return True
    return False


def _resolve_overlaps(entities: list[DetectedEntity]) -> list[DetectedEntity]:
    if not entities:
        return []

    sorted_entities = sorted(
        entities,
        key=lambda e: (e.start, -(e.end - e.start), -e.confidence),
    )

    result: list[DetectedEntity] = [sorted_entities[0]]

    for entity in sorted_entities[1:]:
        last = result[-1]
        if entity.start < last.end:
            last_len = last.end - last.start
            this_len = entity.end - entity.start
            if this_len > last_len:
                result[-1] = entity
            elif this_len == last_len and entity.confidence > last.confidence:
                result[-1] = entity
        else:
            result.append(entity)

    return result


def _verify_spans(text: str, entities: list[DetectedEntity]) -> list[DetectedEntity]:
    verified = []
    for entity in entities:
        actual = text[entity.start:entity.end]
        if actual == entity.value:
            verified.append(entity)
    return verified


def _validate_person_candidate(text: str, result: RecognizerResult, sections: list) -> float:
    """Validate spaCy PERSON predictions."""
    if _is_in_suppressed_section(result.start, sections):
        return 0.0
        
    value = text[result.start:result.end]
    
    # Reject common non-names that spaCy sometimes mislabels
    if value.lower() in ["email", "mobile", "phone", "github", "linkedin", "address", "date"]:
        return 0.0
    
    tokens = value.split()
    if len(tokens) < 2 or len(tokens) > 4:
        pass
        
    ctx_left = text[max(0, result.start - 30):result.start]
    label_pattern = re.compile(
        r'(?:Name|Contact|Candidate|Applicant|Employee|Client|Patient|Witness)[ \t]*[:]\s*$',
        re.IGNORECASE
    )
    if label_pattern.search(ctx_left):
        return 0.99
        
    is_header = False
    for s in sections:
        if s.name == "HEADER" and s.start <= result.start < s.end:
            is_header = True
            break
            
    if is_header:
        lines = text.split('\n')
        for line in lines:
            if line.strip():
                if value in line:
                    return 0.95
                break
                
    return result.score if result.score > 0.8 else 0.0


def _validate_company_candidate(text: str, result: RecognizerResult) -> float:
    """Validate COMPANY predictions to prevent case-insensitive regex false positives."""
    value = text[result.start:result.end]
    
    # Must start with a capital letter
    if not value or not value[0].isupper():
        return 0.0
        
    # Presidio's case-insensitivity causes "microservices" to match "Services".
    # Ensure it ends with an exact allowed suffix, case-sensitive or properly bounded.
    suffix_pattern = re.compile(
        r'\b(Pvt\.? Ltd\.?|Private Limited|Ltd\.?|Limited|LLP|L\.L\.P\.?|LLC|L\.L\.C\.?|'
        r'Inc\.?|Incorporated|Corp\.?|Corporation|Co\.? Ltd\.?|'
        r'Technologies|Solutions|Systems|Industries|Enterprises|Services|Group|Holdings|Partners|Associates)\b',
        # Do NOT use IGNORECASE here, we want strict case for the suffix itself to avoid matching "microservices"
    )
    if not suffix_pattern.search(value):
        return 0.0
        
    return result.score


def detect_pii(text: str) -> list[DetectedEntity]:
    """
    Detect all PII entities using Presidio/spaCy + Context Validation.
    """
    # 1. Section detection
    sections = detect_sections(text)

    # 2. Presidio Candidate Generation (spaCy + PatternRecognizers)
    presidio_results: list[RecognizerResult] = analyze(text)
    
    # 3. Identify Protected Spans (structured types like URL, EMAIL, PHONE)
    # These are highly deterministic and shouldn't be overridden by spaCy
    protected_types = {"URL", "EMAIL", "PHONE", "SSN", "CREDIT_CARD", "IP_ADDRESS"}
    protected_spans = []
    
    structured_candidates = []
    ambiguous_candidates = []
    
    for res in presidio_results:
        if res.entity_type in protected_types:
            structured_candidates.append(res)
            protected_spans.append((res.start, res.end))
        else:
            ambiguous_candidates.append(res)
            
    # 4. Contextual Validation Layer
    validated_entities = []
    
    # Process structured (auto-approve unless they overlap each other, which overlap resolver handles)
    for res in structured_candidates:
        if res.entity_type in _PROTECTION_ONLY_TYPES:
            continue
        if res.score < 0.85:
            continue
        validated_entities.append(DetectedEntity(
            type=res.entity_type,
            value=text[res.start:res.end],
            start=res.start,
            end=res.end,
            confidence=res.score,
            context=_get_context(text, res.start, res.end),
            recognizer="presidio"
        ))
        
    # Process ambiguous (spaCy PERSON/ORG, Pattern DOB/COMPANY)
    for res in ambiguous_candidates:
        if _is_in_protected_span(res.start, res.end, protected_spans):
            continue
            
        value = text[res.start:res.end]
        final_score = res.score
        
        if res.entity_type == "PERSON":
            final_score = _validate_person_candidate(text, res, sections)
        elif res.entity_type == "ORG" or res.entity_type == "COMPANY":
            res.entity_type = "COMPANY"
            final_score = _validate_company_candidate(text, res)
            
            # If our strict validate failed, and it was an ORG, we can reject.
            # If it had 'University' we explicitly reject in validation or here.
            # I added the university check back in just to be safe.
            if final_score > 0 and re.search(r'\b(?:University|College)\b', value, re.IGNORECASE):
                final_score = 0.0

        elif res.entity_type == "DATE" or res.entity_type == "DATE_TIME":
            ctx = _get_context(text, res.start, res.end).lower()
            if not any(kw in ctx for kw in ["dob", "birth", "born"]):
                final_score = 0.0
            else:
                res.entity_type = "DOB"
                final_score = 0.90
        elif res.entity_type == "LOCATION":
            # spaCy GPE/LOC is usually just a city/state, not a full physical address
            final_score = 0.0
        elif res.entity_type not in ["ADDRESS", "DOB", "COMPANY", "PERSON"]:
            # Reject PRODUCT, CARDINAL, PERCENT, etc.
            final_score = 0.0
                
        if final_score >= 0.80:
            validated_entities.append(DetectedEntity(
                type=res.entity_type,
                value=value,
                start=res.start,
                end=res.end,
                confidence=final_score,
                context=_get_context(text, res.start, res.end),
                recognizer="presidio"
            ))

    # 5. Overlap resolution
    resolved = _resolve_overlaps(validated_entities)

    # 6. Span verification
    verified = _verify_spans(text, resolved)
    verified.sort(key=lambda e: e.start)

    return verified
