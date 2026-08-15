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


class TestCompanyReplacement:
    def test_generates_company(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("COMPANY", "Acme Corp.")
        assert result != "Acme Corp."
        assert len(result) > 0


class TestAddressReplacement:
    def test_street_address(self, pseudonymizer):
        result = pseudonymizer.generate_replacement(
            "ADDRESS", "123 Main Street, Springfield, IL 62704"
        )
        assert result != "123 Main Street, Springfield, IL 62704"
        assert len(result) > 0

    def test_po_box(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("ADDRESS", "P.O. Box 1234")
        assert "P.O. Box" in result


class TestSessionReset:
    def test_reset_clears_cache(self, pseudonymizer):
        r1 = pseudonymizer.generate_replacement("PERSON", "Test Name")
        pseudonymizer.reset()
        # After reset, a new name may be generated (depending on Faker state)
        # But at minimum, the cache should be cleared
        assert len(pseudonymizer._cache) == 0


# ─────────────────────────────────────────────────────────
# Round 3 regression tests
# ─────────────────────────────────────────────────────────

class TestBugE_OrdinalDOBReplacement:
    """Bug E: Ordinal DOB replacement must produce a coherent ordinal date."""

    def test_ordinal_dob_14th(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("DOB", "14th March 1994")
        # Must contain an ordinal suffix and be a single coherent date
        assert any(s in result for s in ["st", "nd", "rd", "th"]), (
            f"No ordinal suffix in DOB replacement: '{result}'"
        )
        # Must NOT contain the original "14th" or "March" or "1994"
        assert "14th" not in result
        assert "March" not in result
        assert "1994" not in result

    def test_ordinal_dob_3rd_short_month(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("DOB", "3rd Nov 2001")
        assert any(s in result for s in ["st", "nd", "rd", "th"])
        assert "3rd" not in result
        assert "2001" not in result

    def test_numeric_dob_no_ordinal(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("DOB", "07/22/1988")
        assert "/" in result
        assert len(result) == 10  # MM/DD/YYYY


class TestBugF_IPAddressRFC5737:
    """Bug F: Public IPs must use RFC 5737 TEST-NET ranges; private IPs must stay private."""

    _rfc5737_prefixes = ("192.0.2.", "198.51.100.", "203.0.113.")

    def test_public_ip_uses_test_net(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("IP_ADDRESS", "8.8.8.8")
        assert any(result.startswith(p) for p in self._rfc5737_prefixes), (
            f"Public IP replacement not in TEST-NET range: '{result}'"
        )

    def test_public_ip_another(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("IP_ADDRESS", "175.109.153.17")
        assert any(result.startswith(p) for p in self._rfc5737_prefixes), (
            f"Public IP replacement not in TEST-NET range: '{result}'"
        )

    def test_private_10x_stays_private(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("IP_ADDRESS", "10.0.4.19")
        assert result.startswith("10."), (
            f"10.x.x.x private IP replaced with non-10.x: '{result}'"
        )

    def test_private_172x_stays_private(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("IP_ADDRESS", "172.16.0.1")
        assert result.startswith("172."), (
            f"172.16.x.x private IP replaced with non-172.x: '{result}'"
        )
        second_octet = int(result.split('.')[1])
        assert 16 <= second_octet <= 31, (
            f"172.x.x.x second octet out of private range: {second_octet}"
        )

    def test_private_192168_stays_private(self, pseudonymizer):
        result = pseudonymizer.generate_replacement("IP_ADDRESS", "192.168.1.100")
        assert result.startswith("192.168."), (
            f"192.168.x.x private IP replaced with non-192.168.x: '{result}'"
        )
