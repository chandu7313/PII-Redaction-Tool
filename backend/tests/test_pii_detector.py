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


