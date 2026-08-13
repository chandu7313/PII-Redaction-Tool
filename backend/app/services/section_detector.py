"""
Document Section Detector.

Identifies structural sections in documents (resumes, reports, etc.)
to provide context for PII detection. For example, text inside a
TECHNICAL SKILLS section should not be treated as person names.
"""

import re
from dataclasses import dataclass


@dataclass
class Section:
    """A document section with name and character span."""
    name: str
    start: int
    end: int


# Common section heading patterns (case-insensitive).
# These are normalized to canonical names for downstream use.
_SECTION_MAPPINGS: dict[str, str] = {
    # Contact / Header
    "contact": "CONTACT",
    "contact information": "CONTACT",
    "contact details": "CONTACT",
    "personal information": "CONTACT",
    "personal details": "CONTACT",

    # Summary
    "summary": "SUMMARY",
    "professional summary": "SUMMARY",
    "profile": "SUMMARY",
    "objective": "SUMMARY",
    "career objective": "SUMMARY",
    "about me": "SUMMARY",
    "about": "SUMMARY",

    # Skills
    "skills": "SKILLS",
    "technical skills": "SKILLS",
    "technologies": "SKILLS",
    "tech stack": "SKILLS",
    "core competencies": "SKILLS",
    "competencies": "SKILLS",
    "tools": "SKILLS",
    "tools & technologies": "SKILLS",

    # Experience
    "experience": "EXPERIENCE",
    "work experience": "EXPERIENCE",
    "professional experience": "EXPERIENCE",
    "employment history": "EXPERIENCE",
    "work history": "EXPERIENCE",

    # Projects
    "projects": "PROJECTS",
    "personal projects": "PROJECTS",
    "academic projects": "PROJECTS",
    "key projects": "PROJECTS",

    # Education
    "education": "EDUCATION",
    "academic background": "EDUCATION",
    "qualifications": "EDUCATION",
    "academic qualifications": "EDUCATION",

    # Training
    "training": "TRAINING",
    "courses": "TRAINING",
    "professional development": "TRAINING",

    # Certifications
    "certifications": "CERTIFICATIONS",
    "certificates": "CERTIFICATIONS",
    "professional certifications": "CERTIFICATIONS",
    "licenses": "CERTIFICATIONS",

    # Achievements
    "achievements": "ACHIEVEMENTS",
    "awards": "ACHIEVEMENTS",
    "honors": "ACHIEVEMENTS",
    "accomplishments": "ACHIEVEMENTS",

    # Publications / Research
    "publications": "PUBLICATIONS",
    "research": "PUBLICATIONS",

    # References
    "references": "REFERENCES",
}

# Pattern to detect section headings:
# - Line that is ALL CAPS or Title Case
# - May have trailing colon
# - Typically short (under 60 chars)
_HEADING_PATTERN = re.compile(
    r'^[ \t]*([A-Z][A-Z &/\-]+[A-Z])[ \t]*:?[ \t]*$',
    re.MULTILINE,
)


def detect_sections(text: str) -> list[Section]:
    """
    Detect document sections by looking for heading lines.

    Returns a list of Section objects covering the full text.
    The first section (before any heading) is labeled "HEADER".
    Unrecognized headings retain their original text as the name.
    """
    sections: list[Section] = []
    headings: list[tuple[str, int, int]] = []  # (name, line_start, line_end)

    for m in _HEADING_PATTERN.finditer(text):
        raw = m.group(1).strip()
        normalized = _SECTION_MAPPINGS.get(raw.lower(), raw.upper())
        headings.append((normalized, m.start(), m.end()))

    if not headings:
        # No headings found — treat entire text as BODY
        return [Section(name="BODY", start=0, end=len(text))]

    # First section: everything before the first heading
    if headings[0][1] > 0:
        sections.append(Section(
            name="HEADER",
            start=0,
            end=headings[0][1],
        ))

    # Middle sections
    for i, (name, h_start, h_end) in enumerate(headings):
        next_start = headings[i + 1][1] if i + 1 < len(headings) else len(text)
        sections.append(Section(
            name=name,
            start=h_start,
            end=next_start,
        ))

    return sections


def get_section_at(sections: list[Section], pos: int) -> str:
    """Get the section name at a given character position."""
    for section in sections:
        if section.start <= pos < section.end:
            return section.name
    return "BODY"
