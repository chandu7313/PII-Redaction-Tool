"""
FastAPI Application — PII Redaction Tool.

Main entry point. Configures CORS, mounts API routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import redaction

app = FastAPI(
    title="PII Redaction Tool API",
    description="Detect and redact personally identifiable information from DOCX documents",
    version="1.0.0",
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(redaction.router)


@app.get("/")
async def root():
    return {
        "service": "PII Redaction Tool API",
        "version": "1.0.0",
        "status": "operational",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
