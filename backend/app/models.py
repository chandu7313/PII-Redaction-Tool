"""
Pydantic models for PII Redaction Tool.
"""

from pydantic import BaseModel
from typing import Optional


class PIIEntity(BaseModel):
    """A single detected PII entity."""
    id: int
    type: str  # PERSON, EMAIL, PHONE, SSN, CREDIT_CARD, DOB, IP_ADDRESS, COMPANY, ADDRESS
    original: str
    replacement: str
    confidence: float  # 0.0 - 1.0
    start: int  # character offset in text
    end: int  # character offset in text
    context: Optional[str] = None  # surrounding text for review


