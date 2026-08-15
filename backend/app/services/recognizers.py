"""
Individual PII Recognizers.

Each recognizer is responsible for detecting one type of PII.
Recognizers are categorized into two tiers:

  STRUCTURED (Phase 1): Deterministic regex-based recognizers for
    Email, Phone, SSN, Credit Card, IP Address, URL.
    These produce "protected spans" that later recognizers must not overlap.

  CONTEXTUAL (Phase 2): Context-aware recognizers for
    Person, Company, Address, DOB.
    These require section context and respect protected spans.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DetectedEntity:
    """A single detected PII entity with full provenance."""
    type: str
    value: str
    start: int
    end: int
    confidence: float
    context: str = ""
    recognizer: str = ""


# ─────────────────────────────────────────────────────────
# Base class
# ─────────────────────────────────────────────────────────

class BaseRecognizer:
    """Base class for all PII recognizers."""
    entity_type: str = ""
    recognizer_name: str = ""

    def detect(
        self,
        text: str,
        *,
        protected_spans: Optional[list[tuple[int, int]]] = None,
        sections: Optional[list] = None,
    ) -> list[DetectedEntity]:
        raise NotImplementedError

    def _get_context(self, text: str, start: int, end: int, window: int = 80) -> str:
        ctx_start = max(0, start - window)
        ctx_end = min(len(text), end + window)
        return text[ctx_start:ctx_end]

    def _is_in_protected_span(
        self, start: int, end: int,
        protected_spans: Optional[list[tuple[int, int]]] = None,
    ) -> bool:
        """Check if a span overlaps with any protected span."""
        if not protected_spans:
            return False
        for ps, pe in protected_spans:
            if start < pe and end > ps:
                return True
        return False


# ─────────────────────────────────────────────────────────
# STRUCTURED RECOGNIZERS (Phase 1 — produce protected spans)
# ─────────────────────────────────────────────────────────

class EmailRecognizer(BaseRecognizer):
    entity_type = "EMAIL"
    recognizer_name = "email_regex"

    _pattern = re.compile(
        r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
    )

    def detect(self, text, *, protected_spans=None, sections=None):
        entities = []
        for m in self._pattern.finditer(text):
            entities.append(DetectedEntity(
                type=self.entity_type,
                value=m.group(),
                start=m.start(),
                end=m.end(),
                confidence=0.99,
                context=self._get_context(text, m.start(), m.end()),
                recognizer=self.recognizer_name,
            ))
        return entities


class PhoneRecognizer(BaseRecognizer):
    entity_type = "PHONE"
    recognizer_name = "phone_regex"

    _patterns = [
        # Indian mobile: +91-XXXXXXXXXX or +91 XXXXXXXXXX or 91-XXXXXXXXXX
        (re.compile(
            r'(?<!\d)(?:\+?91[\s\-.]?)?(?:\(?0?\)?[\s\-.]?)?[6-9]\d{9}'
            r'(?:\s*(?:ext\.?|x|extension)\s*\d{1,5})?(?!\d)'
        ), 0.90, "indian_phone"),
        # US: (555) 867-5309 or 555-867-5309 or +1-555-867-5309
        (re.compile(
            r'(?<!\d)(?:\+?1[\s\-.]?)?'
            r'\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}'
            r'(?:\s*(?:ext\.?|x|extension)\s*\d{1,5})?(?!\d)'
        ), 0.90, "us_phone"),
        # Indian landline: 080-2345-6789 or 044-2345-6789 (STD code + number)
        (re.compile(
            r'(?<!\d)0\d{2,4}[\s\-.]?\d{4}[\s\-.]?\d{4}'
            r'(?:\s*(?:ext\.?|x|extension)\s*\d{1,5})?(?!\d)'
        ), 0.88, "indian_landline"),
    ]

    # Context keywords that boost confidence
    _context_keywords = [
        "phone", "mobile", "cell", "tel", "telephone", "contact",
        "call", "fax", "reach", "dial", "whatsapp",
    ]

    def detect(self, text, *, protected_spans=None, sections=None):
        entities = []
        for pattern, base_conf, name in self._patterns:
            for m in pattern.finditer(text):
                value = m.group().strip()
                start, end = m.start(), m.end()

                if self._is_in_protected_span(start, end, protected_spans):
                    continue

                # Validate: must have enough digits
                digits = re.sub(r'\D', '', value)
                if len(digits) < 10 or len(digits) > 15:
                    continue

                # Context boost
                ctx = self._get_context(text, start, end, window=60).lower()
                conf = base_conf
                if any(kw in ctx for kw in self._context_keywords):
                    conf = min(conf + 0.08, 1.0)

                entities.append(DetectedEntity(
                    type=self.entity_type,
                    value=value,
                    start=start,
                    end=end,
                    confidence=round(conf, 2),
                    context=self._get_context(text, start, end),
                    recognizer=name,
                ))
        return entities


class SSNRecognizer(BaseRecognizer):
    entity_type = "SSN"
    recognizer_name = "ssn_regex"

    # Standard format: 123-45-6789
    _pattern_dashed = re.compile(
        r'\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b'
    )
    # Context-only format: 123456789
    _pattern_nodash = re.compile(
        r'\b(?!000|666|9\d{2})\d{3}(?!00)\d{2}(?!0000)\d{4}\b'
    )

    _context_keywords = [
        "ssn", "social security", "ss#", "ss #", "tax id",
        "taxpayer", "social security number",
    ]

    def detect(self, text, *, protected_spans=None, sections=None):
        entities = []

        # Dashed format — high confidence
        for m in self._pattern_dashed.finditer(text):
            if self._is_in_protected_span(m.start(), m.end(), protected_spans):
                continue
            ctx = self._get_context(text, m.start(), m.end(), window=60).lower()
            conf = 0.92
            if any(kw in ctx for kw in self._context_keywords):
                conf = 0.99
            entities.append(DetectedEntity(
                type=self.entity_type, value=m.group(),
                start=m.start(), end=m.end(), confidence=conf,
                context=self._get_context(text, m.start(), m.end()),
                recognizer=self.recognizer_name,
            ))

        # No-dash format — requires context
        for m in self._pattern_nodash.finditer(text):
            if self._is_in_protected_span(m.start(), m.end(), protected_spans):
                continue
            ctx = self._get_context(text, m.start(), m.end(), window=60).lower()
            if any(kw in ctx for kw in self._context_keywords):
                entities.append(DetectedEntity(
                    type=self.entity_type, value=m.group(),
                    start=m.start(), end=m.end(), confidence=0.85,
                    context=self._get_context(text, m.start(), m.end()),
                    recognizer=self.recognizer_name,
                ))

        return entities


class CreditCardRecognizer(BaseRecognizer):
    entity_type = "CREDIT_CARD"
    recognizer_name = "credit_card_regex"

    _patterns = [
        # Visa
        re.compile(r'\b4\d{3}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'),
        # Mastercard
        re.compile(r'\b5[1-5]\d{2}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'),
        # Amex
        re.compile(r'\b3[47]\d{2}[\s\-]?\d{6}[\s\-]?\d{5}\b'),
        # Discover
        re.compile(r'\b6(?:011|5\d{2})[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'),
        # Generic separated 16-digit
        re.compile(r'\b\d{4}[\s\-]\d{4}[\s\-]\d{4}[\s\-]\d{4}\b'),
    ]

    _context_keywords = [
        "card", "credit", "debit", "visa", "mastercard", "amex",
        "american express", "discover", "payment", "card number", "cc",
    ]

    @staticmethod
    def _luhn_check(number: str) -> bool:
        digits = [int(d) for d in number if d.isdigit()]
        if len(digits) < 13 or len(digits) > 19:
            return False
        checksum = 0
        for i, d in enumerate(reversed(digits)):
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d
        return checksum % 10 == 0

    def detect(self, text, *, protected_spans=None, sections=None):
        entities = []
        for pattern in self._patterns:
            for m in pattern.finditer(text):
                if self._is_in_protected_span(m.start(), m.end(), protected_spans):
                    continue

                value = m.group()
                clean = re.sub(r'[\s\-]', '', value)

                # Must pass Luhn
                if not self._luhn_check(clean):
                    continue

                ctx = self._get_context(text, m.start(), m.end(), window=60).lower()
                conf = 0.95
                if any(kw in ctx for kw in self._context_keywords):
                    conf = 0.99

                entities.append(DetectedEntity(
                    type=self.entity_type, value=value,
                    start=m.start(), end=m.end(), confidence=conf,
                    context=self._get_context(text, m.start(), m.end()),
                    recognizer=self.recognizer_name,
                ))
        return entities


class IPAddressRecognizer(BaseRecognizer):
    entity_type = "IP_ADDRESS"
    recognizer_name = "ip_regex"

    _ipv4 = re.compile(
        r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}'
        r'(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b'
    )
    _ipv6 = re.compile(
        r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
    )

    # Words that appear before version-like numbers (not IPs)
    _version_prefixes = re.compile(
        r'(?:version|v|ver|release|build|revision)\s*\.?\s*$',
        re.IGNORECASE,
    )

    def detect(self, text, *, protected_spans=None, sections=None):
        entities = []

        for m in self._ipv4.finditer(text):
            if self._is_in_protected_span(m.start(), m.end(), protected_spans):
                continue

            # Check: is this preceded by "version", "v", etc.?
            prefix = text[max(0, m.start() - 20):m.start()]
            if self._version_prefixes.search(prefix):
                continue

            # Check: is this inside a URL?
            line_start = text.rfind('\n', 0, m.start()) + 1
            line = text[line_start:m.end() + 20]
            if '://' in line and m.start() - line_start < len(line):
                continue

            entities.append(DetectedEntity(
                type=self.entity_type, value=m.group(),
                start=m.start(), end=m.end(), confidence=0.95,
                context=self._get_context(text, m.start(), m.end()),
                recognizer=self.recognizer_name,
            ))

        for m in self._ipv6.finditer(text):
            if self._is_in_protected_span(m.start(), m.end(), protected_spans):
                continue
            entities.append(DetectedEntity(
                type=self.entity_type, value=m.group(),
                start=m.start(), end=m.end(), confidence=0.93,
                context=self._get_context(text, m.start(), m.end()),
                recognizer=self.recognizer_name,
            ))

        return entities


class URLRecognizer(BaseRecognizer):
    """
    Detects URLs (including LinkedIn and GitHub).
    These are NOT treated as PII to redact — they produce protected spans
    so that other recognizers (PERSON, etc.) don't corrupt them.
    """
    entity_type = "URL"
    recognizer_name = "url_regex"

    _pattern = re.compile(
        r'(?:https?://|www\.)'
        r'[A-Za-z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+'
        r'|'
        r'(?:linkedin\.com|github\.com|gitlab\.com|bitbucket\.org)'
        r'[/A-Za-z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]*',
        re.IGNORECASE,
    )

    def detect(self, text, *, protected_spans=None, sections=None):
        entities = []
        for m in self._pattern.finditer(text):
            entities.append(DetectedEntity(
                type=self.entity_type, value=m.group(),
                start=m.start(), end=m.end(), confidence=0.99,
                context=self._get_context(text, m.start(), m.end()),
                recognizer=self.recognizer_name,
            ))
        return entities


# ─────────────────────────────────────────────────────────
# CONTEXTUAL RECOGNIZERS (Phase 2 — respect protected spans)
# ─────────────────────────────────────────────────────────

class PersonRecognizer(BaseRecognizer):
    """
    Context-aware person name recognizer.

    Detection strategies (in priority order):
    1. Explicit label: "Name: John Doe", "Contact: Jane Smith"
    2. Document header: first non-empty line (very likely the person's name)
    3. Title prefix: Mr./Mrs./Dr./Prof. + capitalized words

    Key safety measures:
    - Uses [ \\t]+ instead of \\s+ to prevent cross-line matches
    - Skips matches inside SKILLS, PROJECTS, EDUCATION, CERTIFICATIONS sections
    - Skips matches overlapping protected spans (emails, URLs, phones)
    """
    entity_type = "PERSON"
    recognizer_name = "person_context"

    # Explicit label patterns: "Name: Chandra Mohan Gadige"
    _label_patterns = [
        (re.compile(
            r'(?:^|(?<=\n))[ \t]*'
            r'(?:Full\s+Name|Name|Contact|Candidate|Customer|Employee|'
            r'Applicant|Client|Patient|Witness|Author|Sender|Recipient)'
            r'\s*[:]\s*'
            r'([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+){1,3})',
            re.MULTILINE,
        ), 0.97, "person_label"),
    ]

    # Title-prefixed: "Mr. John Doe"
    _title_pattern = re.compile(
        r'\b(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Prof\.?)'
        r'[ \t]+[A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+){1,2}\b'
    )

    # Sections where PERSON detection should be suppressed
    _suppressed_sections = {
        "SKILLS", "TECHNICAL_SKILLS", "PROJECTS", "TRAINING",
        "CERTIFICATIONS", "ACHIEVEMENTS", "EDUCATION",
    }

    def detect(self, text, *, protected_spans=None, sections=None):
        entities = []
        section_map = sections or []

        # Strategy 1: Explicit label patterns
        for pattern, conf, name in self._label_patterns:
            for m in pattern.finditer(text):
                value = m.group(1).strip()
                # The full match includes the label; we want just the name
                name_start = m.start(1)
                name_end = m.end(1)
                if self._is_in_protected_span(name_start, name_end, protected_spans):
                    continue
                entities.append(DetectedEntity(
                    type=self.entity_type, value=value,
                    start=name_start, end=name_end, confidence=conf,
                    context=self._get_context(text, name_start, name_end),
                    recognizer=name,
                ))

        # Strategy 2: Document header (first non-empty line)
        lines = text.split('\n')
        offset = 0
        for line in lines:
            stripped = line.strip()
            if stripped:
                # Check if first line looks like a person name
                # (2-4 capitalized words, no special chars, no colons)
                if re.match(
                    r'^[A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+){1,3}$', stripped
                ):
                    start = text.index(stripped, offset)
                    end = start + len(stripped)
                    if not self._is_in_protected_span(start, end, protected_spans):
                        # Don't duplicate if already found via label
                        if not any(e.start == start and e.end == end for e in entities):
                            entities.append(DetectedEntity(
                                type=self.entity_type, value=stripped,
                                start=start, end=end, confidence=0.95,
                                context=self._get_context(text, start, end),
                                recognizer="person_header",
                            ))
                break  # Only check the first non-empty line
            offset += len(line) + 1  # +1 for newline

        # Strategy 3: Title-prefixed names
        for m in self._title_pattern.finditer(text):
            start, end = m.start(), m.end()
            if self._is_in_protected_span(start, end, protected_spans):
                continue
            if self._is_in_suppressed_section(start, section_map):
                continue
            if not any(e.start == start and e.end == end for e in entities):
                entities.append(DetectedEntity(
                    type=self.entity_type, value=m.group(),
                    start=start, end=end, confidence=0.92,
                    context=self._get_context(text, start, end),
                    recognizer="person_title",
                ))

        # Strategy 4: Short-line name fallback (catches names in table cells
        # that spaCy NER misses). Only on short lines (≤60 chars), outside
        # suppressed sections, that look like bare "Firstname Lastname".
        _short_name_re = re.compile(
            r'^[ \t]*([A-Z][a-z]{1,15}(?:[ \t]+[A-Z][a-z]{1,15}){1,2})[ \t]*$',
            re.MULTILINE,
        )
        for m in _short_name_re.finditer(text):
            line_start = text.rfind('\n', 0, m.start()) + 1
            line_end = text.find('\n', m.end())
            if line_end == -1:
                line_end = len(text)
            line = text[line_start:line_end]
            if len(line.strip()) > 60:
                continue
            value = m.group(1).strip()
            start = m.start(1)
            end = m.end(1)
            if self._is_in_protected_span(start, end, protected_spans):
                continue
            if self._is_in_suppressed_section(start, section_map):
                continue
            # Don't duplicate if already found
            if any(e.start == start and e.end == end for e in entities):
                continue
            entities.append(DetectedEntity(
                type=self.entity_type, value=value,
                start=start, end=end, confidence=0.85,
                context=self._get_context(text, start, end),
                recognizer="person_short_line",
            ))

        return entities

    def _is_in_suppressed_section(self, pos: int, sections: list) -> bool:
        for section in sections:
            if section.start <= pos < section.end:
                if section.name in self._suppressed_sections:
                    return True
        return False


class CompanyRecognizer(BaseRecognizer):
    """
    Requires business suffix evidence (Pvt Ltd, Inc, Corp, etc.).
    Does NOT blindly classify every ORG/institution.
    """
    entity_type = "COMPANY"
    recognizer_name = "company_suffix"

    _pattern = re.compile(
        r'\b(?:[A-Z][A-Za-z&\'\-]*[ \t]*){1,5}'
        r'(?:Pvt\.?[ \t]+Ltd\.?|Private[ \t]+Limited|'
        r'Ltd\.?|Limited|LLP|L\.L\.P\.?|LLC|L\.L\.C\.?|'
        r'Inc\.?|Incorporated|'
        r'Corp\.?|Corporation|'
        r'Co\.?[ \t]+Ltd\.?|'
        r'Technologies|Solutions|Systems|'
        r'Industries|Enterprises|Services|'
        r'Group|Holdings|Partners|Associates)\b',
        re.MULTILINE,
    )

    def detect(self, text, *, protected_spans=None, sections=None):
        entities = []
        for m in self._pattern.finditer(text):
            if self._is_in_protected_span(m.start(), m.end(), protected_spans):
                continue
            entities.append(DetectedEntity(
                type=self.entity_type, value=m.group().strip(),
                start=m.start(), end=m.end(), confidence=0.90,
                context=self._get_context(text, m.start(), m.end()),
                recognizer=self.recognizer_name,
            ))
        return entities


class AddressRecognizer(BaseRecognizer):
    """
    Context-aware address detection.
    Requires structural signals (street type, ZIP/PIN code, etc.)
    or explicit label context.
    """
    entity_type = "ADDRESS"
    recognizer_name = "address_pattern"

    # Street address: "123 Main Street" or "221B Baker Street, London, NW1 6XE, United Kingdom"
    _street_pattern = re.compile(
        r'\b\d{1,5}[A-Za-z]?[ \t]+(?:[A-Z][a-z]+[ \t]*){1,4}'
        r'(?:Street|St\.?|Avenue|Ave\.?|Boulevard|Blvd\.?|Drive|Dr\.?|'
        r'Lane|Ln\.?|Road|Rd\.?|Way|Court|Ct\.?|Circle|Cir\.?|'
        r'Place|Pl\.?|Terrace|Ter\.?|Trail|Trl\.?|Parkway|Pkwy\.?)'
        r'(?:[ \t]*,?[ \t]*(?:Suite|Ste\.?|Apt\.?|Unit|#)[ \t]*\d+)?'
        # City/region: greedy, but skip UK postcodes (1-2 uppercase + digit)
        # and US state codes (exactly 2 uppercase followed by space + digits)
        r'(?:[ \t]*,[ \t]*(?![A-Z]{1,2}\d)(?![A-Z]{2}[ \t]+\d)(?:[A-Za-z][A-Za-z ]*[A-Za-z]))*'
        # UK postcode: NW1 6XE
        r'(?:[ \t]*,?[ \t]*[A-Z]{1,2}\d[A-Z\d]?[ \t]+\d[A-Z]{2})?'
        # US state + ZIP: IL 62704 or CA 90210-1234
        r'(?:[ \t]*,?[ \t]*[A-Z]{2}[ \t]+\d{5}(?:-\d{4})?)?'
        # Indian PIN: 560001
        r'(?:[ \t]*,?[ \t]*\d{6})?'
        # Country: United Kingdom
        r'(?:[ \t]*,[ \t]*[A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+)*)?',
        re.MULTILINE,
    )

    # PO Box
    _po_box = re.compile(
        r'\bP\.?O\.?[ \t]*Box[ \t]+\d+\b', re.IGNORECASE
    )

    # Indian PIN code with context
    _pin_pattern = re.compile(
        r'(?:PIN|Pincode|Postal[ \t]+Code|ZIP)[ \t]*[:.]?[ \t]*\d{6}\b',
        re.IGNORECASE,
    )

    # Labeled address blocks
    _label_pattern = re.compile(
        r'(?:Address|Mailing[ \t]+Address|Home[ \t]+Address|'
        r'Residence|Residential[ \t]+Address)'
        r'[ \t]*[:.][ \t]*'
        r'(.+?)(?=\n\n|\n[A-Z]|\Z)',
        re.IGNORECASE | re.DOTALL,
    )

    def detect(self, text, *, protected_spans=None, sections=None):
        entities = []

        for pattern in [self._street_pattern, self._po_box, self._pin_pattern]:
            for m in pattern.finditer(text):
                if self._is_in_protected_span(m.start(), m.end(), protected_spans):
                    continue
                entities.append(DetectedEntity(
                    type=self.entity_type, value=m.group().strip(),
                    start=m.start(), end=m.end(), confidence=0.88,
                    context=self._get_context(text, m.start(), m.end()),
                    recognizer=self.recognizer_name,
                ))

        # Labeled address blocks
        for m in self._label_pattern.finditer(text):
            addr = m.group(1).strip()
            if len(addr) < 10 or len(addr) > 300:
                continue
            addr_start = m.start(1)
            addr_end = m.end(1)
            if self._is_in_protected_span(addr_start, addr_end, protected_spans):
                continue
            entities.append(DetectedEntity(
                type=self.entity_type, value=addr,
                start=addr_start, end=addr_end, confidence=0.92,
                context=self._get_context(text, addr_start, addr_end),
                recognizer="address_label",
            ))

        return entities


class DOBRecognizer(BaseRecognizer):
    """
    Date of birth recognizer.
    Only detects dates that have explicit DOB context.
    Ordinary dates (project timelines, education dates) are NOT DOB.
    """
    entity_type = "DOB"
    recognizer_name = "dob_context"

    _date_patterns = [
        # MM/DD/YYYY or MM-DD-YYYY
        re.compile(
            r'\b(?:0[1-9]|1[0-2])[/\-](?:0[1-9]|[12]\d|3[01])[/\-](?:19|20)\d{2}\b'
        ),
        # YYYY-MM-DD
        re.compile(
            r'\b(?:19|20)\d{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])\b'
        ),
        # Month DD, YYYY (with optional ordinal suffix)
        re.compile(
            r'\b(?:January|February|March|April|May|June|July|August|'
            r'September|October|November|December)[ \t]+\d{1,2}(?:st|nd|rd|th)?,?[ \t]+(?:19|20)\d{2}\b',
            re.IGNORECASE,
        ),
        # DDth Month YYYY (ordinal day + month + year)
        re.compile(
            r'\b\d{1,2}(?:st|nd|rd|th)[ \t]+(?:January|February|March|April|May|June|July|August|'
            r'September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
            r',?[ \t]+(?:19|20)\d{2}\b',
            re.IGNORECASE,
        ),
        # DD Month YYYY (no ordinal)
        re.compile(
            r'\b\d{1,2}[ \t]+(?:January|February|March|April|May|June|July|August|'
            r'September|October|November|December),?[ \t]+(?:19|20)\d{2}\b',
            re.IGNORECASE,
        ),
    ]

    _context_keywords = [
        "dob", "d.o.b", "date of birth", "birth date", "birthdate",
        "born", "born on", "birthday",
    ]

    def detect(self, text, *, protected_spans=None, sections=None):
        entities = []

        for pattern in self._date_patterns:
            for m in pattern.finditer(text):
                if self._is_in_protected_span(m.start(), m.end(), protected_spans):
                    continue

                # REQUIRE DOB context — without it, skip
                ctx = self._get_context(text, m.start(), m.end(), window=80).lower()
                if not any(kw in ctx for kw in self._context_keywords):
                    continue

                entities.append(DetectedEntity(
                    type=self.entity_type, value=m.group(),
                    start=m.start(), end=m.end(), confidence=0.93,
                    context=self._get_context(text, m.start(), m.end()),
                    recognizer=self.recognizer_name,
                ))

        return entities
