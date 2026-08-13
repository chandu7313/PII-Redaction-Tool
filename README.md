# PII Redaction Tool

A full-stack application that detects personally identifiable information (PII) in DOCX documents, replaces it with realistic synthetic alternatives, and produces redacted documents.

## Architecture

```
Frontend (React + TypeScript + Tailwind CSS)
    │
    │ HTTP (Vite proxy → localhost:8000)
    ▼
Backend (Python + FastAPI)
    │
    ├── PII Detection (Regex + Context-Aware Scoring)
    ├── Pseudonymization (Faker-based synthetic data)
    └── DOCX Processing (python-docx)
```

## PII Types Detected

- Full names
- Email addresses
- Phone numbers
- Company names
- Physical/mailing addresses
- Social Security Numbers (SSNs)
- Credit card numbers
- Dates of birth
- IP addresses

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install

# Run the dev server (proxies API calls to backend)
npm run dev
```

### Running Tests

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── models.py            # Pydantic models
│   │   ├── routers/
│   │   │   └── redaction.py     # API endpoints
│   │   └── services/
│   │       ├── pii_detector.py  # PII detection engine
│   │       ├── pseudonymizer.py # Synthetic data generation
│   │       └── docx_processor.py # DOCX read/write
│   ├── tests/
│   │   ├── test_pii_detector.py
│   │   └── test_pseudonymizer.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Page components
│   │   ├── services/            # API client
│   │   ├── App.tsx              # Router setup
│   │   └── index.css            # Global styles
│   ├── tailwind.config.js
│   ├── package.json
│   └── index.html
└── README.md
```

## Design

The UI follows a **"Classified Evidence"** aesthetic inspired by intelligence dossiers:
- Brutalist typography with Courier Prime and IBM Plex Serif
- Manila paper textures with noise overlays
- Stamp-style buttons with rubber stamp interactions
- Zero border-radius throughout
- Confidence meters with tick-mark bars

Design source: Google Stitch Project #13449614587817439069
