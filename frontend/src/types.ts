/**
 * TypeScript types matching the backend Pydantic models.
 */

export interface PIIEntity {
  id: number;
  type: string;
  original: string;
  replacement: string;
  confidence: number;
  start: number;
  end: number;
  context?: string;
}

export interface RedactionStats {
  total_entities: number;
  entities_by_type: Record<string, number>;
  avg_confidence: number;
  processing_time_ms: number;
}

export interface UploadResponse {
  job_id: string;
  filename: string;
  entities: PIIEntity[];
  original_text: string;
  redacted_text: string;
  stats: RedactionStats;
}

export interface RedactResponse {
  job_id: string;
  status: string;
  redacted_text: string;
  original_text: string;
  entities: PIIEntity[];
  stats: RedactionStats;
}

export type PIIType =
  | 'PERSON'
  | 'EMAIL'
  | 'PHONE'
  | 'SSN'
  | 'CREDIT_CARD'
  | 'DOB'
  | 'IP_ADDRESS'
  | 'COMPANY'
  | 'ADDRESS';

export const PII_TYPE_LABELS: Record<PIIType, string> = {
  PERSON: 'Person',
  EMAIL: 'Email',
  PHONE: 'Phone',
  SSN: 'SSN',
  CREDIT_CARD: 'Credit Card',
  DOB: 'Date of Birth',
  IP_ADDRESS: 'IP Address',
  COMPANY: 'Company',
  ADDRESS: 'Address',
};

export const ALL_PII_TYPES: PIIType[] = [
  'PERSON', 'EMAIL', 'PHONE', 'SSN', 'CREDIT_CARD',
  'DOB', 'IP_ADDRESS', 'COMPANY', 'ADDRESS',
];
