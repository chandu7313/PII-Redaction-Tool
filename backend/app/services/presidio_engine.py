"""
Microsoft Presidio Analyzer Engine.

Configures and initializes the Presidio AnalyzerEngine with spaCy (en_core_web_sm).
Registers custom PatternRecognizers for specific entity types (Email, Indian Phone,
SSN, Credit Card, IP Address, Company, Address, DOB, URL).
"""

from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
import re


def _create_custom_recognizer(entity_type: str, name: str, patterns: list[tuple[str, float]], context: list[str] = None) -> PatternRecognizer:
    presidio_patterns = [
        Pattern(name=f"{name}_{i}", regex=regex, score=score)
        for i, (regex, score) in enumerate(patterns)
    ]
    return PatternRecognizer(
        supported_entity=entity_type,
        name=name,
        patterns=presidio_patterns,
        context=context,
    )


import os
import urllib.request
import tarfile

def _ensure_spacy_model():
    model_dir = "/tmp/en_core_web_sm"
    model_name_in_tar = "en_core_web_sm-3.8.0/en_core_web_sm/en_core_web_sm-3.8.0"
    if not os.path.exists(model_dir):
        tar_path = "/tmp/model.tar.gz"
        url = "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0.tar.gz"
        urllib.request.urlretrieve(url, tar_path)
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path="/tmp")
        # Move it to expected dir
        os.rename(os.path.join("/tmp", model_name_in_tar), model_dir)
    return model_dir

def get_analyzer_engine() -> AnalyzerEngine:
    """Initialize and return a configured Presidio AnalyzerEngine."""
    model_path = _ensure_spacy_model()
    
    # Configure spaCy NLP engine
    configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": model_path}],
    }
    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_engine = provider.create_engine()
    
    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        supported_languages=["en"],
    )
    
    # 1. EMAIL
    email_rec = _create_custom_recognizer(
        "EMAIL", "email_regex",
        [(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b', 0.99)]
    )
    
    # 2. PHONE (Indian mobile + US + Indian landline + International)
    phone_rec = _create_custom_recognizer(
        "PHONE", "phone_regex",
        [
            (r'(?<!\d)(?:\+?91[\s\-.]?)?(?:\(?0?\)?[\s\-.]?)?[6-9]\d{9}(?:\s*(?:ext\.?|x|extension)\s*\d{1,5})?(?!\d)', 0.90),
            (r'(?<!\d)(?:\+?1[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}(?:\s*(?:ext\.?|x|extension)\s*\d{1,5})?(?!\d)', 0.90),
            (r'(?<!\d)0\d{2,4}[\s\-.]?\d{4}[\s\-.]?\d{4}(?:\s*(?:ext\.?|x|extension)\s*\d{1,5})?(?!\d)', 0.88),
            (r'\b(?:\+?\d{1,3}\.)?\d{3,5}\.\d{4,5}\b', 0.85),
        ],
        context=["phone", "mobile", "cell", "tel", "telephone", "contact", "call", "whatsapp"]
    )
    
    # 3. SSN & NATIONAL_ID
    ssn_rec = _create_custom_recognizer(
        "SSN", "ssn_regex",
        [
            (r'\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b', 0.92),
            (r'\b(?!000|666|9\d{2})\d{3}(?!00)\d{2}(?!0000)\d{4}\b', 0.50),
            (r'\b\d{4}\s\d{4}\s\d{4}\b', 0.95), # Aadhaar
        ],
        context=["ssn", "social security", "ss#", "tax id", "aadhaar", "national id"]
    )
    
    # 4. CREDIT CARD (Simplified patterns; Luhn validation happens later)
    cc_rec = _create_custom_recognizer(
        "CREDIT_CARD", "credit_card_regex",
        [
            (r'\b4\d{3}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b', 0.85),
            (r'\b5[1-5]\d{2}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b', 0.85),
            (r'\b3[47]\d{2}[\s\-]?\d{6}[\s\-]?\d{5}\b', 0.85),
            (r'\b6(?:011|5\d{2})[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b', 0.85),
            (r'\b\d{4}[\s\-]\d{4}[\s\-]\d{4}[\s\-]\d{4}\b', 0.80),
        ],
        context=["card", "credit", "visa", "mastercard", "amex", "payment"]
    )
    
    # 5. IP ADDRESS
    ip_rec = _create_custom_recognizer(
        "IP_ADDRESS", "ip_regex",
        [
            (r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b', 0.95),
            (r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b', 0.93),
        ]
    )
    
    # 6. URL (Protection only)
    url_rec = _create_custom_recognizer(
        "URL", "url_regex",
        [
            (r'(?:https?://|www\.)[A-Za-z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+'
             r'|(?:linkedin\.com|github\.com|gitlab\.com|bitbucket\.org)[/A-Za-z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]*', 0.99)
        ]
    )
    
    # 7. COMPANY
    company_rec = _create_custom_recognizer(
        "COMPANY", "company_suffix",
        [
            (r'\b(?:[A-Z][A-Za-z&\'\-]*[ \t]*){1,5}'
             r'(?:Pvt\.?[ \t]+Ltd\.?|Private[ \t]+Limited|'
             r'Ltd\.?|Limited|LLP|L\.L\.P\.?|LLC|L\.L\.C\.?|'
             r'Inc\.?|Incorporated|Corp\.?|Corporation|'
             r'Co\.?[ \t]+Ltd\.?|Technologies|Solutions|Systems|'
             r'Industries|Enterprises|Services|Group|Holdings|Partners|Associates)\b', 0.90)
        ]
    )
    
    # 8. ADDRESS (Simplified; labeled addresses handled in context validator)
    address_rec = _create_custom_recognizer(
        "ADDRESS", "address_pattern",
        [
            (r'\b\d{1,5}[A-Za-z]?[ \t]+(?:[A-Z][a-z]+[ \t]*){1,4}'
             r'(?:Street|St\.?|Avenue|Ave\.?|Boulevard|Blvd\.?|Drive|Dr\.?|'
             r'Lane|Ln\.?|Road|Rd\.?|Way|Court|Ct\.?|Circle|Cir\.?|'
             r'Place|Pl\.?|Terrace|Ter\.?|Trail|Trl\.?|Parkway|Pkwy\.?)'
             r'(?:[ \t]*,?[ \t]*(?:Suite|Ste\.?|Apt\.?|Unit|#)[ \t]*\d+)?'
             r'(?:[ \t]*,[ \t]*(?![A-Z]{1,2}\d)(?![A-Z]{2}[ \t]+\d)(?:[A-Za-z][A-Za-z ]*[A-Za-z]))*'
             r'(?:[ \t]*,?[ \t]*[A-Z]{1,2}\d[A-Z\d]?[ \t]+\d[A-Z]{2})?'
             r'(?:[ \t]*,?[ \t]*[A-Z]{2}[ \t]+\d{5}(?:-\d{4})?)?'
             r'(?:[ \t]*,?[ \t]*\d{6})?'
             r'(?:[ \t]*,[ \t]*[A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+)*)?', 0.88),
            (r'\bP\.?O\.?[ \t]*Box[ \t]+\d+(?:[ \t]*,[ \t]*[A-Za-z][A-Za-z \t]*)*', 0.88),
        ]
    )
    
    # 9. DOB (Requires context)
    dob_rec = _create_custom_recognizer(
        "DOB", "dob_context",
        [
            (r'\b(?:0[1-9]|1[0-2])[/\-](?:0[1-9]|[12]\d|3[01])[/\-](?:19|20)\d{2}\b', 0.50),
            (r'\b(?:19|20)\d{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])\b', 0.50),
            (r'\b\d{1,2}(?:st|nd|rd|th)[ \t]+(?:January|February|March|April|May|June|July|August|'
             r'September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
             r',?[ \t]+(?:19|20)\d{2}\b', 0.50),
        ],
        context=["dob", "birth", "born", "birthday"]
    )
    
    # Register all custom recognizers
    analyzer.registry.add_recognizer(email_rec)
    analyzer.registry.add_recognizer(phone_rec)
    analyzer.registry.add_recognizer(ssn_rec)
    analyzer.registry.add_recognizer(cc_rec)
    analyzer.registry.add_recognizer(ip_rec)
    analyzer.registry.add_recognizer(url_rec)
    analyzer.registry.add_recognizer(company_rec)
    analyzer.registry.add_recognizer(address_rec)
    analyzer.registry.add_recognizer(dob_rec)
    
    return analyzer

# Singleton instance
_analyzer = None

def analyze(text: str) -> list:
    """Run Presidio Analyzer on text and return RecognizerResult objects."""
    global _analyzer
    if _analyzer is None:
        _analyzer = get_analyzer_engine()
        
    return _analyzer.analyze(text=text, language='en', return_decision_process=True)
