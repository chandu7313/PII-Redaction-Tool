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


