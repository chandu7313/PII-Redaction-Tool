"""
Tests for PII Detection Engine.
"""

import pytest
from app.services.pii_detector import detect_pii, DetectedEntity


class TestEmailDetection:
    def test_standard_email(self):
        text = "Contact me at john.doe@example.com for details."
        entities = detect_pii(text)
        emails = [e for e in entities if e.type == "EMAIL"]
        assert len(emails) == 1
        assert emails[0].value == "john.doe@example.com"
        assert emails[0].confidence >= 0.95

    def test_multiple_emails(self):
        text = "Send to alice@test.org or bob.smith@company.co.uk"
        entities = detect_pii(text)
        emails = [e for e in entities if e.type == "EMAIL"]
        assert len(emails) == 2

    def test_email_with_plus(self):
        text = "Use user+tag@gmail.com for filtering."
        entities = detect_pii(text)
        emails = [e for e in entities if e.type == "EMAIL"]
        assert len(emails) == 1
        assert "user+tag@gmail.com" in emails[0].value


class TestSSNDetection:
    def test_standard_ssn(self):
        text = "SSN: 123-45-6789"
        entities = detect_pii(text)
        ssns = [e for e in entities if e.type == "SSN"]
        assert len(ssns) == 1
        assert ssns[0].value == "123-45-6789"

    def test_ssn_invalid_area(self):
        text = "Number: 000-12-3456"
        entities = detect_pii(text)
        ssns = [e for e in entities if e.type == "SSN"]
        assert len(ssns) == 0  # 000 area is invalid

    def test_ssn_with_context_boost(self):
        text = "The applicant's social security number is 456-78-9012."
        entities = detect_pii(text)
        ssns = [e for e in entities if e.type == "SSN"]
        assert len(ssns) == 1
        assert ssns[0].confidence > 0.95  # Context boost applied


