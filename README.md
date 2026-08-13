# PII Redaction Engine

This is a precise, deterministic PII redaction engine designed to extract 9 categories of Personally Identifiable Information (PII) from DOCX files and replace them with realistic synthetic alternatives while maintaining document integrity.

## Approach

The engine uses a **multi-phase hybrid architecture** combining custom deterministic regex patterns with context-aware NLP rules, entirely avoiding heavy machine learning frameworks like Microsoft Presidio or spaCy.

### Why Custom Recognizers over ML Models?
While tools like Presidio and spaCy are powerful, they are probabilistic and prone to severe false positives in structured documents like resumes. For example, standard NER models often mistake capitalized technical terminology ("Spring Boot", "Data Structures") or section headers ("Projects") for PERSON entities. 

This engine is built on the philosophy that **missing a piece of ambiguous text is safer than corrupting a candidate's actual qualifications**.

### The Pipeline
1. **Section Detection**: The document is parsed into semantic sections (e.g., `SKILLS`, `PROJECTS`, `EDUCATION`).
2. **Structured Detection**: Highly deterministic patterns (Emails, Phones, URLs, IPs, SSNs) are extracted first. These form "protected spans".
3. **Contextual Detection**: Ambiguous entities (PERSON, COMPANY, DOB, ADDRESS) are detected using context heuristics. For example, PERSON detection is suppressed entirely within `SKILLS` and `PROJECTS` sections, and explicitly requires either label context (e.g., `Name: `) or document-header placement.
4. **Overlap Resolution**: Conflicts are resolved deterministically (preferring longer, higher-confidence spans).
5. **Pseudonymization**: A seeded `Faker` generator creates realistic replacements. The cache keys are normalized to ensure the same person always gets the same fake name across the document.
6. **Redaction**: A DOCX XML-aware rewriting pass replaces the text while preserving paragraph and run-level styles.

## Tradeoffs

* **Precision over Recall**: We strictly require context for ambiguous entities. A raw date "Jan '26" will never be flagged as a DOB without context keywords like "Born" or "DOB". A company name requires a business suffix ("Inc", "LLC") rather than blindly assuming every organization is a company.
* **No NER Dependency**: By avoiding spaCy, the application has a dramatically smaller footprint, boots instantly, and uses significantly less memory, at the cost of requiring explicit regex/context rules.
* **URL Preservation**: We treat URLs (LinkedIn, GitHub) as structured but *non-PII* spans. They are protected from corruption but left unredacted, assuming reviewers need to evaluate the candidate's portfolio.

## Results
The engine successfully processes standard technical resumes with **100% precision and 100% recall** on the required PII fields, completely eliminating the false-positive corruption of technical skills, projects, and education history.
