/**
 * API client for the PII Redaction Tool backend.
 */

import type { UploadResponse, RedactResponse, PIIEntity } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

/**
 * Upload a DOCX file for PII detection.
 */
export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(error.detail || `Upload failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Commit redactions and generate the redacted DOCX.
 */
export async function commitRedactions(
  jobId: string,
  entities: PIIEntity[],
): Promise<RedactResponse> {
  const response = await fetch(`${API_BASE}/redact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_id: jobId, entities }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Redaction failed' }));
    throw new Error(error.detail || `Redaction failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Download the redacted DOCX file.
 */
export async function downloadRedacted(jobId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/download/${jobId}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Download failed' }));
    throw new Error(error.detail || `Download failed: ${response.statusText}`);
  }

  // Get filename from Content-Disposition header
  const disposition = response.headers.get('Content-Disposition');
  const filenameMatch = disposition?.match(/filename="(.+)"/);
  const filename = filenameMatch ? filenameMatch[1] : 'redacted_document.docx';

  // Create download link
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
