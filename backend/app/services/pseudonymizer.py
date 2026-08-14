"""
Pseudonymization Service.

Generates realistic synthetic replacements for detected PII entities.
Maintains consistency: the same original value always maps to the same replacement
within a single redaction session.
"""

from faker import Faker
import random
import re
from typing import Optional

fake = Faker()
Faker.seed(0)


class Pseudonymizer:
    """
    Generates consistent synthetic replacements for PII entities.

    Uses a cache to ensure the same original value always gets
    the same replacement within a session.
    """

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
        self._cache: dict[str, str] = {}
        self._type_counters: dict[str, int] = {}

    def _get_counter(self, entity_type: str) -> int:
        """Get and increment counter for entity type."""
        count = self._type_counters.get(entity_type, 0) + 1
        self._type_counters[entity_type] = count
        return count

    def generate_replacement(self, entity_type: str, original: str) -> str:
        """
        Generate a synthetic replacement for a PII entity.

        Args:
            entity_type: The type of PII (PERSON, EMAIL, PHONE, etc.)
            original: The original PII value

        Returns:
            A realistic synthetic replacement string
        """
        # Normalize cache key for consistency
        cache_key = f"{entity_type}:{original.strip().lower()}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        replacement = self._generate(entity_type, original)
        self._cache[cache_key] = replacement
        return replacement

    def _generate(self, entity_type: str, original: str) -> str:
        """Generate a new synthetic value based on entity type."""
        generators = {
            "PERSON": self._gen_person,
            "EMAIL": self._gen_email,
            "PHONE": self._gen_phone,
            "SSN": self._gen_ssn,
            "CREDIT_CARD": self._gen_credit_card,
            "DOB": self._gen_dob,
            "IP_ADDRESS": self._gen_ip,
            "COMPANY": self._gen_company,
            "ADDRESS": self._gen_address,
            "URL": self._gen_url,
        }

        generator = generators.get(entity_type)
        if generator:
            return generator(original)

        # Fallback: generic placeholder
        counter = self._get_counter(entity_type)
        return f"[{entity_type}_{counter}]"

    def _gen_person(self, original: str) -> str:
        """Generate a synthetic person name."""
        parts = original.split()
        if len(parts) >= 3:
            return f"{fake.first_name()} {fake.first_name()[0]}. {fake.last_name()}"
        elif len(parts) == 2:
            return f"{fake.first_name()} {fake.last_name()}"
        else:
            return fake.first_name()

    def _gen_email(self, original: str) -> str:
        """Generate a synthetic email address."""
        return fake.email()

    def _gen_phone(self, original: str) -> str:
        """Generate a synthetic phone number matching the original format."""
        # Detect format
        if original.startswith('+91'):
            return f"+91-{fake.numerify('##########')}"
        elif original.startswith('+'):
            return f"+1-{fake.numerify('###')}-{fake.numerify('###')}-{fake.numerify('####')}"
        elif '(' in original:
            return f"({fake.numerify('###')}) {fake.numerify('###')}-{fake.numerify('####')}"
        elif '.' in original:
            return f"{fake.numerify('###')}.{fake.numerify('###')}.{fake.numerify('####')}"
        else:
            return f"{fake.numerify('###')}-{fake.numerify('###')}-{fake.numerify('####')}"

    def _gen_ssn(self, original: str) -> str:
        """Generate a synthetic SSN or National ID."""
        if len(original.replace(' ', '').replace('-', '')) == 12:
            # Aadhaar style
            return f"{fake.numerify('####')} {fake.numerify('####')} {fake.numerify('####')}"
        if '-' in original:
            return fake.ssn()
        else:
            return fake.ssn().replace('-', '')

    def _gen_credit_card(self, original: str) -> str:
        """Generate a synthetic credit card number matching format."""
        number = fake.credit_card_number(card_type='visa16')
        # Match original formatting
        clean_original = re.sub(r'[\s\-]', '', original)
        if '-' in original:
            return f"{number[:4]}-{number[4:8]}-{number[8:12]}-{number[12:16]}"
        elif ' ' in original:
            return f"{number[:4]} {number[4:8]} {number[8:12]} {number[12:16]}"
        return number

    def _gen_dob(self, original: str) -> str:
        """Generate a synthetic date of birth matching format."""
        dob = fake.date_of_birth(minimum_age=18, maximum_age=90)

        # Detect format
        if re.match(r'\d{4}-\d{2}-\d{2}', original):
            return dob.strftime('%Y-%m-%d')
        elif re.match(r'\d{2}/\d{2}/\d{4}', original):
            return dob.strftime('%m/%d/%Y')
        elif re.match(r'\d{2}-\d{2}-\d{4}', original):
            return dob.strftime('%m-%d-%Y')
        elif re.match(r'[A-Za-z]+\s+\d', original):
            return dob.strftime('%B %d, %Y')
        elif re.match(r'\d{1,2}\s+[A-Za-z]+', original):
            return dob.strftime('%d %B %Y')
        else:
            return dob.strftime('%m/%d/%Y')

    def _gen_ip(self, original: str) -> str:
        """Generate a synthetic IP address."""
        if ':' in original:
            # IPv6
            return fake.ipv6()
        return fake.ipv4()

    def _gen_company(self, original: str) -> str:
        """Generate a synthetic company name."""
        return fake.company()

    def _gen_address(self, original: str) -> str:
        """Generate a synthetic address."""
        if re.match(r'P\.?O\.?\s*Box', original, re.IGNORECASE):
            return f"P.O. Box {random.randint(100, 9999)}"
            
        orig_lower = original.lower()
        if 'india' in orig_lower or 'bengaluru' in orig_lower or re.search(r'\b\d{6}\b', original):
            # Generate Indian style fake address
            city = fake.city()
            state = fake.state()
            pin = fake.numerify('######')
            street = fake.street_name()
            bldg = random.randint(1, 999)
            return f"{bldg} {street}, {city}, {state} {pin}, India"
            
        if 'uk' in orig_lower or 'united kingdom' in orig_lower or 'london' in orig_lower or re.search(r'\b[A-Z]{1,2}\d[A-Z\d]? \d[A-Z]{2}\b', original, re.IGNORECASE):
            # Generate UK style fake address
            city = fake.city()
            street = fake.street_name()
            bldg = random.randint(1, 999)
            postcode = fake.postcode()
            return f"{bldg} {street}, {city}, {postcode}, United Kingdom"
            
        return fake.address().replace('\n', ', ')

    def _gen_url(self, original: str) -> str:
        """Generate a synthetic URL by replacing the username/path segment."""
        # Split by / to find the last path segment (which is usually the username for github/linkedin)
        parts = original.rstrip('/').split('/')
        
        # Don't modify the domain itself (e.g. "github.com") if there's no path
        if len(parts) <= 1 or (len(parts) == 3 and parts[0].startswith('http')):
            return original
            
        fake_username = fake.user_name()
        # Replace the last segment with a fake username
        parts[-1] = fake_username
        
        return "/".join(parts)

    def reset(self):
        """Clear the cache and counters for a new session."""
        self._cache.clear()
        self._type_counters.clear()
