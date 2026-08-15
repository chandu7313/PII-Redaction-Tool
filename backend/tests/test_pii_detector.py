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
        assert ssns[0].confidence >= 0.90  # Context boost applied


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
        text = "Contact: John Doe"
        entities = detect_pii(text)
        persons = [e for e in entities if e.type == "PERSON"]
        assert len(persons) >= 1


class TestCompanyDetection:
    def test_company_with_inc(self):
        text = "Working at Acme Corporation Inc."
        entities = detect_pii(text)
        companies = [e for e in entities if e.type == "COMPANY"]
        assert len(companies) >= 1

    def test_company_with_llc(self):
        text = "Filed by Smith & Associates LLC"
        entities = detect_pii(text)
        companies = [e for e in entities if e.type == "COMPANY"]
        assert len(companies) >= 1


class TestOverlapResolution:
    def test_no_duplicate_overlaps(self):
        text = "Dr. John Smith's SSN is 123-45-6789 and email is john@test.com"
        entities = detect_pii(text)
        # Ensure no two entities overlap
        for i in range(len(entities) - 1):
            for j in range(i + 1, len(entities)):
                assert (
                    entities[i].end <= entities[j].start
                    or entities[j].end <= entities[i].start
                ), f"Overlap: {entities[i]} and {entities[j]}"


class TestEdgeCases:
    def test_empty_string(self):
        entities = detect_pii("")
        assert entities == []

    def test_no_pii(self):
        text = "The quick brown fox jumps over the lazy dog."
        entities = detect_pii(text)
        # Should have very few or no entities
        assert all(e.confidence < 0.90 for e in entities)

    def test_multiple_types(self):
        text = (
            "Employee John Doe (john@acme.com, SSN 123-45-6789) "
            "works at Acme Corp. Phone: (555) 123-4567. "
            "DOB: 03/15/1990. IP: 10.0.0.1. "
            "CC: 4111-1111-1111-1111. "
            "Address: 123 Main Street, Anytown, CA 90210"
        )
        entities = detect_pii(text)
        types_found = {e.type for e in entities}
        # Should detect most types
        assert "EMAIL" in types_found
        assert "SSN" in types_found
        assert "PHONE" in types_found
        assert "IP_ADDRESS" in types_found


# ─────────────────────────────────────────────────────────
# Round 3 regression tests
# ─────────────────────────────────────────────────────────

class TestBugA_TableNameDetection:
    """Bug A: Both names in a two-row table must be detected, not just one."""

    def test_both_table_names_detected(self):
        # Simulates extracted table text: short lines with bare names
        text = (
            "Employee Records\n"
            "Kavya Nair\n"
            "Software Engineer\n"
            "Imran Qureshi\n"
            "Data Analyst\n"
        )
        entities = detect_pii(text)
        person_values = [e.value for e in entities if e.type == "PERSON"]
        assert "Kavya Nair" in person_values, (
            f"Kavya Nair not detected. Found: {person_values}"
        )
        assert "Imran Qureshi" in person_values, (
            f"Imran Qureshi not detected. Found: {person_values}"
        )


class TestBugB_ExtensionPhone:
    """Bug B: Landline phone with extension must be fully detected."""

    def test_landline_with_extension(self):
        text = "Office phone: 080-2345-6789 ext. 214"
        entities = detect_pii(text)
        phones = [e for e in entities if e.type == "PHONE"]
        assert len(phones) >= 1, f"No phone detected in: {text}"
        # The match must include the extension part
        matched = phones[0].value
        assert "ext" in matched.lower(), (
            f"Extension not included in match: '{matched}'"
        )
        assert "214" in matched, (
            f"Extension digits not included in match: '{matched}'"
        )

    def test_landline_with_x_extension(self):
        text = "Tel: 044-2567-8901 x 100"
        entities = detect_pii(text)
        phones = [e for e in entities if e.type == "PHONE"]
        assert len(phones) >= 1


class TestBugC_CompanySpanBoundary:
    """Bug C: Company spans must not include leading verbs/prepositions."""

    def test_employed_by_prefix(self):
        text = "Employed by Acme Technologies Pvt Ltd for 5 years."
        entities = detect_pii(text)
        companies = [e for e in entities if e.type == "COMPANY"]
        assert len(companies) >= 1
        company_val = companies[0].value
        assert "Employed" not in company_val, (
            f"Leading context leaked into company span: '{company_val}'"
        )
        assert "Acme" in company_val

    def test_vendor_contract_prefix(self):
        text = "Vendor contract held with Sethand Associates LLP since 2020."
        entities = detect_pii(text)
        companies = [e for e in entities if e.type == "COMPANY"]
        assert len(companies) >= 1
        company_val = companies[0].value
        assert "Vendor" not in company_val
        assert "contract" not in company_val
        assert "Sethand" in company_val

    def test_consulting_engagement_prefix(self):
        text = "Consulting engagement with Northfield Labs Inc began in Q3."
        entities = detect_pii(text)
        companies = [e for e in entities if e.type == "COMPANY"]
        assert len(companies) >= 1
        company_val = companies[0].value
        assert "Consulting" not in company_val
        assert "Northfield" in company_val


class TestBugD_FullAddressDetection:
    """Bug D: Full international addresses must be captured as one span."""

    def test_uk_address_full_capture(self):
        text = "Address: 221B Baker Street, London, NW1 6XE, United Kingdom"
        entities = detect_pii(text)
        addresses = [e for e in entities if e.type == "ADDRESS"]
        assert len(addresses) >= 1
        addr = addresses[0].value
        assert "221B" in addr, f"House number leaked: '{addr}'"
        assert "Baker Street" in addr, f"Street name not captured: '{addr}'"
        assert "NW1 6XE" in addr, f"Postal code not captured: '{addr}'"


class TestBugE_OrdinalDOBDetection:
    """Bug E: Ordinal-prefixed dates must be fully captured as one span."""

    def test_ordinal_dob_14th(self):
        text = "Date of birth: 14th March 1994"
        entities = detect_pii(text)
        dobs = [e for e in entities if e.type == "DOB"]
        assert len(dobs) == 1, f"Expected 1 DOB, got {len(dobs)}: {[e.value for e in dobs]}"
        assert dobs[0].value == "14th March 1994"

    def test_ordinal_dob_3rd(self):
        text = "Born on 3rd Nov 2001 in Mumbai."
        entities = detect_pii(text)
        dobs = [e for e in entities if e.type == "DOB"]
        assert len(dobs) == 1
        assert dobs[0].value == "3rd Nov 2001"

    def test_numeric_dob_unchanged(self):
        text = "DOB: 07/22/1988"
        entities = detect_pii(text)
        dobs = [e for e in entities if e.type == "DOB"]
        assert len(dobs) == 1
        assert dobs[0].value == "07/22/1988"
