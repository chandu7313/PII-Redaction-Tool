"""
Pseudonymization Service.

Generates realistic synthetic replacements for detected PII entities.
Maintains consistency: the same original value always maps to the same replacement
within a single redaction session.
"""

import random
import re
from typing import Optional


class Pseudonymizer:
    """
    Generates consistent synthetic replacements for PII entities.

    Uses a cache to ensure the same original value always gets
    the same replacement within a session.
    """

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
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
        first = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Charles", "Joseph", "Thomas", "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen"]
        last = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
        parts = original.split()
        if len(parts) >= 3:
            return f"{random.choice(first)} {chr(random.randint(65, 90))}. {random.choice(last)}"
        elif len(parts) == 2:
            return f"{random.choice(first)} {random.choice(last)}"
        else:
            return random.choice(first)

    def _gen_email(self, original: str) -> str:
        names = ["alex", "taylor", "jordan", "casey", "morgan", "riley", "sam", "jamie"]
        domains = ["example.com", "test.org", "sample.net", "demo.io"]
        return f"{random.choice(names)}{random.randint(10,999)}@{random.choice(domains)}"

    def _gen_phone(self, original: str) -> str:
        d = lambda: str(random.randint(0, 9))
        n3 = lambda: "".join(d() for _ in range(3))
        n4 = lambda: "".join(d() for _ in range(4))
        
        if original.startswith('+91'):
            return f"+91-9{n3()}{n3()}{n3()}"
        elif original.startswith('+'):
            return f"+1-{n3()}-{n3()}-{n4()}"
        elif '(' in original:
            return f"({n3()}) {n3()}-{n4()}"
        elif '.' in original:
            return f"{n3()}.{n3()}.{n4()}"
        else:
            return f"{n3()}-{n3()}-{n4()}"

    def _gen_ssn(self, original: str) -> str:
        d = lambda: str(random.randint(0, 9))
        n4 = lambda: "".join(d() for _ in range(4))
        
        if len(original.replace(' ', '').replace('-', '')) == 12:
            return f"{n4()} {n4()} {n4()}"
        if '-' in original:
            return f"{d()}{d()}{d()}-{d()}{d()}-{n4()}"
        else:
            return f"{d()}{d()}{d()}{d()}{d()}{n4()}"

    def _gen_credit_card(self, original: str) -> str:
        d = lambda: str(random.randint(0, 9))
        n4 = lambda: "".join(d() for _ in range(4))
        number = f"4{n4()[1:]}{n4()}{n4()}{n4()}"
        
        if '-' in original:
            return f"{number[:4]}-{number[4:8]}-{number[8:12]}-{number[12:16]}"
        elif ' ' in original:
            return f"{number[:4]} {number[4:8]} {number[8:12]} {number[12:16]}"
        return number

    def _gen_dob(self, original: str) -> str:
        y = random.randint(1950, 2005)
        m = random.randint(1, 12)
        d = random.randint(1, 28)
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        
        if re.match(r'\d{4}-\d{2}-\d{2}', original):
            return f"{y:04d}-{m:02d}-{d:02d}"
        elif re.match(r'\d{2}/\d{2}/\d{4}', original):
            return f"{m:02d}/{d:02d}/{y:04d}"
        elif re.match(r'\d{2}-\d{2}-\d{4}', original):
            return f"{m:02d}-{d:02d}-{y:04d}"
        elif re.match(r'[A-Za-z]+\s+\d', original):
            return f"{months[m-1]} {d:02d}, {y:04d}"
        elif re.match(r'\d{1,2}\s+[A-Za-z]+', original):
            return f"{d:02d} {months[m-1]} {y:04d}"
        else:
            return f"{m:02d}/{d:02d}/{y:04d}"

    def _gen_ip(self, original: str) -> str:
        if ':' in original:
            return ":".join(f"{random.randint(0, 65535):x}" for _ in range(8))
        return ".".join(str(random.randint(1, 254)) for _ in range(4))

    def _gen_company(self, original: str) -> str:
        prefixes = ["Acme", "Globex", "Initech", "Soylent", "Massive", "Apex", "Zenith", "Quantum"]
        suffixes = ["Corp", "Inc", "LLC", "Ltd", "Solutions", "Technologies", "Enterprises"]
        return f"{random.choice(prefixes)} {random.choice(suffixes)}"

    def _gen_address(self, original: str) -> str:
        if re.match(r'P\.?O\.?\s*Box', original, re.IGNORECASE):
            return f"P.O. Box {random.randint(100, 9999)}"
            
        orig_lower = original.lower()
        if 'india' in orig_lower or 'bengaluru' in orig_lower or re.search(r'\b\d{6}\b', original):
            return f"{random.randint(1, 999)} Main Street, Bangalore, Karnataka {random.randint(500000, 599999)}, India"
            
        if 'uk' in orig_lower or 'united kingdom' in orig_lower or 'london' in orig_lower or re.search(r'\b[A-Z]{1,2}\d[A-Z\d]? \d[A-Z]{2}\b', original, re.IGNORECASE):
            return f"{random.randint(1, 999)} High Street, London, SW1A 1AA, United Kingdom"
            
        return f"{random.randint(1, 999)} Maple Ave, Springfield, IL {random.randint(10000, 99999)}"

    def _gen_url(self, original: str) -> str:
        parts = original.rstrip('/').split('/')
        if len(parts) <= 1 or (len(parts) == 3 and parts[0].startswith('http')):
            return original
        parts[-1] = f"user{random.randint(1000, 9999)}"
        return "/".join(parts)

    def reset(self):
        """Clear the cache and counters for a new session."""
        self._cache.clear()
        self._type_counters.clear()
