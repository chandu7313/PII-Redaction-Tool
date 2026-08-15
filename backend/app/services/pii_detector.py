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


def _get_context(text: str, start: int, end: int, window: int = 40) -> str:
    ctx_start = max(0, start - window)
    ctx_end = min(len(text), end + window)
    ctx = text[ctx_start:ctx_end]
    # Don't cross paragraph boundaries
    if '\n\n' in ctx:
        # Find the paragraph containing the entity
        para_start = text.rfind('\n\n', ctx_start, start)
        if para_start != -1:
            ctx_start = para_start + 2
        para_end = text.find('\n\n', end, ctx_end)
        if para_end != -1:
            ctx_end = para_end
        ctx = text[ctx_start:ctx_end]
    return ctx


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

    result: list[DetectedEntity] = []

    for entity in sorted_entities:
        conflict = False
        for i, existing in enumerate(result):
            # Check for overlap or strict adjacency (no characters or only whitespace between them)
            # Two entities overlap/touch if entity.start <= existing.end + whitespace
            # Actually, just check if they intersect or touch
            is_overlap = max(entity.start, existing.start) < min(entity.end, existing.end)
            
            # Check adjacency
            is_adjacent = False
            if entity.start >= existing.end:
                between = " " # default to something safe
                # we don't have original text here, but we can assume if start == end they touch
                if entity.start == existing.end:
                    is_adjacent = True
            
            if is_overlap or is_adjacent:
                conflict = True
                # Resolve conflict
                existing_len = existing.end - existing.start
                entity_len = entity.end - entity.start
                
                # Priority: Structured types (SSN, PHONE, EMAIL, URL) > Pattern types (DOB, ADDRESS) > NLP types (PERSON, COMPANY)
                # We can approximate this by confidence and length
                
                # If they are different types, never merge them into the same replacement implicitly.
                # Just pick the winner.
                
                if entity.confidence > existing.confidence:
                    result[i] = entity
                elif entity.confidence == existing.confidence and entity_len > existing_len:
                    result[i] = entity
                break # We resolved against this existing entity, but wait, could it conflict with others? 
                      # For simplicity, since we sorted, it mainly conflicts with the latest ones.
                      
        if not conflict:
            result.append(entity)

    # Do a second pass to remove any duplicates or lingering overlaps just in case
    final_result = []
    for entity in result:
        conflict = False
        for i, existing in enumerate(final_result):
            if max(entity.start, existing.start) < min(entity.end, existing.end):
                conflict = True
                if entity.confidence > existing.confidence:
                    final_result[i] = entity
                elif entity.confidence == existing.confidence and (entity.end - entity.start) > (existing.end - existing.start):
                    final_result[i] = entity
                break
        if not conflict:
            final_result.append(entity)
            
    return final_result


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
    
    # Strip address suffixes from the PERSON match
    addr_suffix = re.search(r'\s+(?:Boulevard|Blvd\.?|Street|St\.?|Avenue|Ave\.?|Drive|Dr\.?|Lane|Ln\.?|Road|Rd\.?|Way|Court|Ct\.?|Circle|Cir\.?|Place|Pl\.?|Terrace|Ter\.?)$', value, re.IGNORECASE)
    if addr_suffix:
        value = value[:addr_suffix.start()]
        result.end = result.start + len(value)
        
    # Check tech-denylist (substring match)
    tech_denylist = ["gemini", "react", "node", "java", "python", "spring", "docker", "aws"]
    if any(tech in value.lower() for tech in tech_denylist):
        return 0.0
    
    # Reject common non-names that spaCy sometimes mislabels
    if value.lower() in ["email", "mobile", "phone", "github", "linkedin", "address", "date"]:
        return 0.0
    
    tokens = value.split()
    if len(tokens) < 2 or len(tokens) > 4:
        pass
        
    # Reject "Title Case:" labels (e.g. "Soft Skills:")
    ctx_right = text[result.end:min(len(text), result.end + 5)]
    if ctx_right.lstrip().startswith(':'):
        return 0.0
        
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

    # Trim leading non-company context words (verbs, prepositions, articles, etc.)
    # that spaCy's NER may have included in the ORG span.
    # Walk forward through words until we hit a capitalized word that is NOT
    # a common context word.
    _context_words = {
        "employed", "by", "at", "for", "with", "from", "of", "the", "a", "an",
        "vendor", "contract", "held", "consulting", "engagement", "working",
        "works", "worked", "joined", "joining", "hired", "founded",
        "managed", "managing", "led", "leading",
        "in", "to", "and", "or", "on", "as",
    }
    tokens = value.split()
    trim_count = 0
    for token in tokens:
        # If it's a lowercase word or a common context word (case-insensitive), trim it
        if token.lower() in _context_words or (token[0].islower() if token else False):
            trim_count += 1
        else:
            break

    if trim_count > 0 and trim_count < len(tokens):
        # Recalculate span start
        trimmed_text = " ".join(tokens[trim_count:])
        new_start = result.start + value.index(tokens[trim_count])
        result.start = new_start
        value = text[result.start:result.end]

    return result.score


def _validate_address_candidate(text: str, result: RecognizerResult) -> float:
    # Reject if it starts mid-word or follows a heading numbering pattern
    if result.start > 0:
        prev_char = text[result.start - 1]
        if prev_char in ['.', '#']:
            return 0.0
            
    # Check if it starts exactly at a line beginning that looks like a heading (e.g. "1.7 ")
    ctx_left = text[max(0, result.start - 10):result.start]
    if re.search(r'(?:^|\n)\d+\.\d+\s*$', ctx_left):
        return 0.0
        
    return result.score
    
    
def _validate_ip_candidate(text: str, result: RecognizerResult) -> float:
    ctx_left = text[max(0, result.start - 20):result.start].lower()
    if re.search(r'\b(?:version|v|build)\s*$', ctx_left):
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
            
        final_score = res.score
        if res.entity_type == "IP_ADDRESS":
            final_score = _validate_ip_candidate(text, res)
            
        if final_score < 0.85:
            continue
            
        validated_entities.append(DetectedEntity(
            type=res.entity_type,
            value=text[res.start:res.end],
            start=res.start,
            end=res.end,
            confidence=final_score,
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
            if not any(re.search(rf'\b{kw}\b', ctx) for kw in ["dob", "d.o.b", "birth", "born", "birthday", "birthdate"]):
                final_score = 0.0
            else:
                res.entity_type = "DOB"
                final_score = 0.90
        elif res.entity_type == "ADDRESS":
            final_score = _validate_address_candidate(text, res)
        elif res.entity_type == "IP_ADDRESS":
            final_score = _validate_ip_candidate(text, res)
        elif res.entity_type == "LOCATION":
            # spaCy GPE/LOC is usually just a city/state, not a full physical address
            final_score = 0.0
        elif res.entity_type not in ["ADDRESS", "DOB", "COMPANY", "PERSON", "IP_ADDRESS", "SSN", "PHONE", "EMAIL", "CREDIT_CARD", "URL"]:
            # Reject PRODUCT, CARDINAL, PERCENT, etc.
            final_score = 0.0
                
        # Update value in case res.start or res.end were modified by validation
        value = text[res.start:res.end]
        
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

    # 4b. Bug A fallback: detect names on short lines that spaCy NER missed.
    # This catches bare "Firstname Lastname" patterns on lines ≤60 chars
    # (typical of table cells) outside suppressed sections.
    _short_name_re = re.compile(
        r'^[ \t]*([A-Z][a-z]{1,15}(?:[ \t]+[A-Z][a-z]{1,15}){1,2})[ \t]*$',
        re.MULTILINE,
    )
    for m in _short_name_re.finditer(text):
        value = m.group(1).strip()
        start = m.start(1)
        end = m.end(1)
        # Check line length
        line_start = text.rfind('\n', 0, m.start()) + 1
        line_end = text.find('\n', m.end())
        if line_end == -1:
            line_end = len(text)
        line = text[line_start:line_end]
        if len(line.strip()) > 60:
            continue
        if _is_in_protected_span(start, end, protected_spans):
            continue
        if _is_in_suppressed_section(start, sections):
            continue
        # Don't duplicate if already found
        if any(e.start == start and e.end == end for e in validated_entities):
            continue
        validated_entities.append(DetectedEntity(
            type="PERSON",
            value=value,
            start=start,
            end=end,
            confidence=0.85,
            context=_get_context(text, start, end),
            recognizer="person_short_line"
        ))

    # 4c. Bug E: extend DOB spans backward to include ordinal day prefix.
    # If a DOB like "March 1994" was detected by spaCy but the original text
    # has "14th March 1994", extend the span to cover the ordinal.
    _ordinal_prefix = re.compile(r'\d{1,2}(?:st|nd|rd|th)\s+$', re.IGNORECASE)
    for entity in validated_entities:
        if entity.type == "DOB":
            prefix_region = text[max(0, entity.start - 10):entity.start]
            om = _ordinal_prefix.search(prefix_region)
            if om:
                entity.start = entity.start - (len(prefix_region) - om.start())
                entity.value = text[entity.start:entity.end]

    # 5. Overlap resolution
    resolved = _resolve_overlaps(validated_entities)

    # 6. Span verification
    verified = _verify_spans(text, resolved)
    verified.sort(key=lambda e: e.start)

    return verified
