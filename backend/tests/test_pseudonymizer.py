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


