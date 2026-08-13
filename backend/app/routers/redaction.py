"""
API Router for document redaction operations.

Endpoints:
- POST /api/upload     — Upload a DOCX file and detect PII
- POST /api/redact     — Commit redactions and generate redacted DOCX
- GET  /api/download/{job_id} — Download the redacted DOCX
"""

import uuid
import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response

from ..models import (
    PIIEntity,
    RedactionStats,
    UploadResponse,
    RedactionRequest,
)
from ..services.pii_detector import detect_pii
from ..services.pseudonymizer import Pseudonymizer
from ..services.docx_processor import (
    extract_text,
    create_redacted_docx,
    create_comparison_text,
)

router = APIRouter(prefix="/api", tags=["redaction"])

# In-memory storage for job data (production would use a database/object store)
_jobs: dict[str, dict] = {}


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a DOCX document for PII detection.

    Extracts text, detects PII entities, generates synthetic replacements,
    and returns the complete analysis.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.docx'):
        raise HTTPException(
            status_code=400,
            detail="Only .docx files are supported"
        )

    # Read file
    file_bytes = await file.read()
    if len(file_bytes) > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 50MB limit"
        )

    start_time = time.time()

    # Extract text
    try:
        original_text = extract_text(file_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse DOCX file: {str(e)}"
        )

    if not original_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Document contains no extractable text"
        )

    # Detect PII
    detected = detect_pii(original_text)

    # Generate synthetic replacements
    pseudonymizer = Pseudonymizer(seed=42)
    entities: list[PIIEntity] = []

    for i, entity in enumerate(detected):
        replacement = pseudonymizer.generate_replacement(
            entity.type, entity.value
        )
        entities.append(PIIEntity(
            id=i + 1,
            type=entity.type,
            original=entity.value,
            replacement=replacement,
            confidence=entity.confidence,
            start=entity.start,
            end=entity.end,
            context=entity.context,
        ))

    # Create redacted text preview
    redacted_text = create_comparison_text(original_text, entities)

    # Calculate stats
    processing_time = (time.time() - start_time) * 1000
    entities_by_type: dict[str, int] = {}
    for e in entities:
        entities_by_type[e.type] = entities_by_type.get(e.type, 0) + 1

    avg_confidence = (
        sum(e.confidence for e in entities) / len(entities)
        if entities else 0.0
    )

    stats = RedactionStats(
        total_entities=len(entities),
        entities_by_type=entities_by_type,
        avg_confidence=round(avg_confidence, 2),
        processing_time_ms=round(processing_time, 2),
    )

    # Store job data
    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {
        "filename": file.filename,
        "file_bytes": file_bytes,
        "original_text": original_text,
        "redacted_text": redacted_text,
        "entities": entities,
        "stats": stats,
    }

    return UploadResponse(
        job_id=job_id,
        filename=file.filename,
        entities=entities,
        original_text=original_text,
        redacted_text=redacted_text,
        stats=stats,
    )


@router.post("/redact")
async def commit_redactions(request: RedactionRequest):
    """
    Commit redactions with (optionally modified) entity list.

    Creates the final redacted DOCX file ready for download.
    """
    job = _jobs.get(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Update entities (user may have edited replacements)
    job["entities"] = request.entities

    # Regenerate redacted text
    job["redacted_text"] = create_comparison_text(
        job["original_text"], request.entities
    )

    # Create redacted DOCX
    try:
        redacted_bytes = create_redacted_docx(
            job["file_bytes"], request.entities
        )
        job["redacted_bytes"] = redacted_bytes
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create redacted document: {str(e)}"
        )

    return {
        "job_id": request.job_id,
        "status": "redacted",
        "redacted_text": job["redacted_text"],
        "original_text": job["original_text"],
        "entities": [e.model_dump() for e in request.entities],
        "stats": job["stats"].model_dump(),
    }


@router.get("/download/{job_id}")
async def download_redacted(job_id: str):
    """
    Download the redacted DOCX file.
    """
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    redacted_bytes = job.get("redacted_bytes")
    if not redacted_bytes:
        raise HTTPException(
            status_code=400,
            detail="Redactions have not been committed yet"
        )

    # Generate filename
    original_name = job["filename"].rsplit('.', 1)[0]
    redacted_filename = f"{original_name}_REDACTED.docx"

    return Response(
        content=redacted_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{redacted_filename}"'
        },
    )
