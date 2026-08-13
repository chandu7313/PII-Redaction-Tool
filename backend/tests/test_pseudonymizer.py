"""
Tests for Pseudonymization Service.
"""

import pytest
from app.services.pseudonymizer import Pseudonymizer


@pytest.fixture
def pseudonymizer():
    return Pseudonymizer(seed=42)


class TestPersonReplacement:
    def test_two_word_name(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("PERSON", "John Doe")
        parts = result.split()
        assert len(parts) == 2
        assert result != "John Doe"

    def test_three_word_name(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("PERSON", "John A. Smith")
        assert result != "John A. Smith"
        assert len(result) > 3

    def test_consistency(self, pseudonymizer):
        r1 = pseudonymizer.generate_replacement("PERSON", "John Doe")
        r2 = pseudonymizer.generate_replacement("PERSON", "John Doe")
        assert r1 == r2


class TestEmailReplacement:
    def test_generates_valid_email(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("EMAIL", "john@example.com")
        assert "@" in result
        assert "." in result.split("@")[1]
        assert result != "john@example.com"


class TestPhoneReplacement:
    def test_parenthesized_format(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("PHONE", "(555) 867-5309")
        assert result.startswith("(")
        assert result != "(555) 867-5309"

    def test_dashed_format(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("PHONE", "555-867-5309")
        assert "-" in result

    def test_international_format(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("PHONE", "+1-800-555-0199")
        assert result.startswith("+")


class TestSSNReplacement:
    def test_dashed_ssn(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("SSN", "123-45-6789")
        assert len(result) == 11
        assert result.count("-") == 2
        assert result != "123-45-6789"

    def test_plain_ssn(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("SSN", "123456789")
        assert "-" not in result
        assert len(result) == 9


class TestCreditCardReplacement:
    def test_dashed_card(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("CREDIT_CARD", "4111-1111-1111-1111")
        assert result.count("-") == 3

    def test_spaced_card(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("CREDIT_CARD", "4111 1111 1111 1111")
        assert " " in result


class TestDOBReplacement:
    def test_us_format(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("DOB", "03/15/1990")
        assert "/" in result
        assert len(result) == 10

    def test_iso_format(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("DOB", "1990-03-15")
        assert "-" in result
        assert result[:4].isdigit()

    def test_written_format(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("DOB", "January 15, 1990")
        assert any(month in result for month in [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])


class TestIPReplacement:
    def test_ipv4(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("IP_ADDRESS", "192.168.1.1")
        parts = result.split(".")
        assert len(parts) == 4

    def test_ipv6(self, pseudonymizer):
        result = pseudonymizer.generate_replacement(
            "IP_ADDRESS", "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        )
        assert ":" in result


