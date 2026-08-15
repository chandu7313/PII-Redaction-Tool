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

        # Extract extension suffix if present
        ext_match = re.search(r'\s*(ext\.?|x|extension)\s*(\d{1,5})$', original, re.IGNORECASE)
        ext_suffix = ""
        base = original
        if ext_match:
            base = original[:ext_match.start()]
            ext_label = ext_match.group(1)
            ext_suffix = f" {ext_label} {random.randint(100, 999)}"

        # Generate base phone number
        if base.startswith('+91'):
            result = f"+91-9{n3()}{n3()}{n3()}"
        elif base.startswith('+'):
            result = f"+1-{n3()}-{n3()}-{n4()}"
        elif '(' in base:
            result = f"({n3()}) {n3()}-{n4()}"
        elif '.' in base:
            result = f"{n3()}.{n3()}.{n4()}"
        elif re.match(r'^0\d{2,4}[\s\-]', base):
            # Indian landline: 0XX-XXXX-XXXX
            result = f"0{d()}{d()}-{n4()}-{n4()}"
        else:
            result = f"{n3()}-{n3()}-{n4()}"

        return result + ext_suffix

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
        # Short month names for abbreviated formats
        short_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        def _ordinal(n: int) -> str:
            """Return day with ordinal suffix: 1st, 2nd, 3rd, 4th..."""
            if 11 <= n <= 13:
                return f"{n}th"
            return f"{n}{['th','st','nd','rd'][n % 10] if n % 10 < 4 else 'th'}"

        if re.match(r'\d{4}-\d{2}-\d{2}', original):
            return f"{y:04d}-{m:02d}-{d:02d}"
        elif re.match(r'\d{2}/\d{2}/\d{4}', original):
            return f"{m:02d}/{d:02d}/{y:04d}"
        elif re.match(r'\d{2}-\d{2}-\d{4}', original):
            return f"{m:02d}-{d:02d}-{y:04d}"
        elif re.match(r'\d{1,2}(?:st|nd|rd|th)\s+[A-Za-z]+', original, re.IGNORECASE):
            # Ordinal day + month: "14th March 1994" or "3rd Nov 2001"
            # Check if short month name was used
            month_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b', original)
            if month_match and len(month_match.group(1)) <= 3:
                return f"{_ordinal(d)} {short_months[m-1]} {y:04d}"
            return f"{_ordinal(d)} {months[m-1]} {y:04d}"
        elif re.match(r'[A-Za-z]+\s+\d', original):
            return f"{months[m-1]} {d:02d}, {y:04d}"
        elif re.match(r'\d{1,2}\s+[A-Za-z]+', original):
            return f"{d:02d} {months[m-1]} {y:04d}"
        else:
            return f"{m:02d}/{d:02d}/{y:04d}"

    def _gen_ip(self, original: str) -> str:
        if ':' in original:
            return ":".join(f"{random.randint(0, 65535):x}" for _ in range(8))

        # Parse original octets to determine if private or public
        octets = original.split('.')
        if len(octets) == 4:
            try:
                o1, o2 = int(octets[0]), int(octets[1])
            except ValueError:
                o1, o2 = 0, 0

            # Check RFC 1918 private ranges
            is_private = (
                o1 == 10  # 10.0.0.0/8
                or (o1 == 172 and 16 <= o2 <= 31)  # 172.16.0.0/12
                or (o1 == 192 and o2 == 168)  # 192.168.0.0/16
            )

            if is_private:
                # Generate replacement in the SAME private range
                if o1 == 10:
                    return f"10.{random.randint(0,255)}.{random.randint(0,254)}.{random.randint(1,254)}"
                elif o1 == 172:
                    return f"172.{random.randint(16,31)}.{random.randint(0,254)}.{random.randint(1,254)}"
                else:
                    return f"192.168.{random.randint(0,254)}.{random.randint(1,254)}"

        # Public IP → RFC 5737 TEST-NET ranges
        # 192.0.2.0/24 (TEST-NET-1), 198.51.100.0/24 (TEST-NET-2), 203.0.113.0/24 (TEST-NET-3)
        test_nets = [
            ("192.0.2", ),
            ("198.51.100", ),
            ("203.0.113", ),
        ]
        prefix = random.choice(test_nets)[0]
        return f"{prefix}.{random.randint(1, 254)}"

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
