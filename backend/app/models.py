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


class RedactionStats(BaseModel):
    """Summary statistics for a redaction job."""
    total_entities: int
    entities_by_type: dict[str, int]
    avg_confidence: float
    processing_time_ms: float


class RedactionResult(BaseModel):
    """Complete result of PII detection on a document."""
    job_id: str
    filename: str
    original_text: str
    redacted_text: str
    entities: list[PIIEntity]
    stats: RedactionStats


class RedactionRequest(BaseModel):
    """Request to commit redactions with optional entity overrides."""
    job_id: str
    entities: list[PIIEntity]


class UploadResponse(BaseModel):
    """Response from document upload and PII detection."""
    job_id: str
    filename: str
    entities: list[PIIEntity]
    original_text: str
    redacted_text: str
    stats: RedactionStats


class DownloadResponse(BaseModel):
    """Metadata for a downloadable redacted document."""
    job_id: str
    filename: str
    download_url: str

