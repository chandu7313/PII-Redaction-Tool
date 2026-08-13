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


class TestPhoneDetection:
    def test_parenthesized_phone(self):
        text = "Call (555) 867-5309 for info."
        entities = detect_pii(text)
        phones = [e for e in entities if e.type == "PHONE"]
        assert len(phones) >= 1

    def test_dashed_phone(self):
        text = "Phone: 555-123-4567"
        entities = detect_pii(text)
        phones = [e for e in entities if e.type == "PHONE"]
        assert len(phones) >= 1

    def test_international_phone(self):
        text = "Reach us at +1-800-555-0199."
        entities = detect_pii(text)
        phones = [e for e in entities if e.type == "PHONE"]
        assert len(phones) >= 1


class TestCreditCardDetection:
    def test_visa(self):
        text = "Card: 4111-1111-1111-1111"
        entities = detect_pii(text)
        cards = [e for e in entities if e.type == "CREDIT_CARD"]
        assert len(cards) >= 1

    def test_mastercard_with_spaces(self):
        text = "Payment card 5500 0000 0000 0004"
        entities = detect_pii(text)
        cards = [e for e in entities if e.type == "CREDIT_CARD"]
        assert len(cards) >= 1


class TestIPAddressDetection:
    def test_ipv4(self):
        text = "Server IP: 192.168.1.100"
        entities = detect_pii(text)
        ips = [e for e in entities if e.type == "IP_ADDRESS"]
        assert len(ips) == 1
        assert ips[0].value == "192.168.1.100"

    def test_ipv4_boundary(self):
        text = "Access from 255.255.255.255 detected."
        entities = detect_pii(text)
        ips = [e for e in entities if e.type == "IP_ADDRESS"]
        assert len(ips) == 1


class TestDOBDetection:
    def test_us_format(self):
        text = "Date of birth: 03/15/1990"
        entities = detect_pii(text)
        dobs = [e for e in entities if e.type == "DOB"]
        assert len(dobs) == 1

    def test_iso_format(self):
        text = "Born: 1985-07-22"
        entities = detect_pii(text)
        dobs = [e for e in entities if e.type == "DOB"]
        assert len(dobs) == 1

    def test_written_format(self):
        text = "Birthday is January 15, 1990."
        entities = detect_pii(text)
        dobs = [e for e in entities if e.type == "DOB"]
        assert len(dobs) == 1


class TestAddressDetection:
    def test_street_address(self):
        text = "Located at 1234 Elm Street, Springfield, IL 62704"
        entities = detect_pii(text)
        addresses = [e for e in entities if e.type == "ADDRESS"]
        assert len(addresses) >= 1

    def test_po_box(self):
        text = "Mail to P.O. Box 1234"
        entities = detect_pii(text)
        addresses = [e for e in entities if e.type == "ADDRESS"]
        assert len(addresses) == 1


class TestPersonDetection:
    def test_titled_name(self):
        text = "Dr. Jane Smith reviewed the case."
        entities = detect_pii(text)
        persons = [e for e in entities if e.type == "PERSON"]
        assert len(persons) >= 1

    def test_two_word_name(self):
        text = "Contact person is John Doe."
        entities = detect_pii(text)
        persons = [e for e in entities if e.type == "PERSON"]
        assert len(persons) >= 1


