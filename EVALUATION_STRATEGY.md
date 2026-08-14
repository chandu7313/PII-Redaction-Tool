# Evaluation Strategy & Metrics Framework
**System:** Enterprise PII Detection & Pseudonymization Pipeline
**Author:** Candidate (Targeting Senior/Lead Engineering Role)

---

## 1. Executive Summary
The primary objective of the PII Redaction pipeline is to achieve a delicate balance between **strict regulatory compliance** (requiring near-perfect Recall) and **document utility** (requiring high Precision). Over-redacting destroys the analytical value of documents, while under-redacting risks data breaches. 

To evaluate this system, we employ a rigorous, multi-tiered evaluation strategy that measures not just standard classification metrics (Precision, Recall, F1), but also **contextual awareness**, **adversarial robustness**, and **pseudonymization determinism**.

---

## 2. Core Evaluation Metrics

For a production-grade PII pipeline, standard accuracy is insufficient due to severe class imbalance (PII represents <5% of document text). We evaluate using token-level and entity-level metrics.

### 2.1 Entity-Level Metrics
* **Recall (Sensitivity):** $\frac{\text{True Positives}}{\text{True Positives} + \text{False Negatives}}$
  * *Business Impact:* The most critical metric. A false negative (missed PII) is a compliance violation. The system is tuned to favor Recall over Precision in ambiguous cases.
* **Precision (Positive Predictive Value):** $\frac{\text{True Positives}}{\text{True Positives} + \text{False Positives}}$
  * *Business Impact:* Prevents destruction of document utility. False positives (e.g., redacting an invoice number as an SSN) frustrate users and break downstream analytics.
* **F1-Score (Macro & Micro):** The harmonic mean of Precision and Recall. We monitor Macro F1 to ensure rare PII classes (like Aadhaar numbers) perform as well as common ones (like Names).

### 2.2 System-Specific Metrics
* **Determinism Rate:** Measures the consistency of the pseudonymizer. If "Sarah Chen" appears 10 times across 3 documents, it must be replaced by the exact same synthetic name (e.g., "William Rodriguez") 100% of the time, guaranteeing referential integrity.
* **Overlap Resolution Accuracy:** The percentage of correctly resolved boundary collisions (e.g., an Address regex matching a street name, while spaCy NER matches the person's name inside the street).

---

## 3. The "Adversarial" Evaluation Dataset
Traditional NLP datasets (like CoNLL-2003) are insufficient for modern PII evaluation because they lack realistic business edge cases. We evaluate the pipeline against a custom **Adversarial Fixture Document** (`pii_test_document.docx`) engineered with "False-Positive Traps."

### 3.1 Known Traps Evaluated
The system is explicitly tested against its ability to **ignore**:
1. **Reference / Order Numbers:** e.g., "Invoice 445566" or "Case ID 342679081" (prevents SSN/Phone false positives).
2. **Amounts / Currencies:** e.g., "$4,539.14" or "₹25,000".
3. **Temporal Markers (Non-DOB):** e.g., "Meeting scheduled for 14 March 2026" (must not be flagged as a Date of Birth).
4. **Software Versions / SKUs:** e.g., "Software version 91.211.49.166" (must not be flagged as an IP Address).
5. **Section Headers:** e.g., "TECHNICAL SKILLS:" (prevents spaCy from hallucinating capitalization as a Person).

---

## 4. Evaluation Methodology

### 4.1 Hybrid Architecture Validation
The pipeline utilizes a hybrid approach: **Heuristic/Regex (Microsoft Presidio)** for structured data (Phones, IPs, SSNs) and **NLP (spaCy NER)** for unstructured data (Names, Organizations). 

Evaluation is conducted in two phases:
1. **Component-Level Evaluation:** Each recognizer (e.g., `AadhaarRecognizer`) is tested in isolation against positive and negative examples.
2. **Pipeline-Level Evaluation:** The `pii_detector.py` orchestrator is evaluated on its ability to merge, trim, and resolve overlaps between the components. 
   * *Example:* If Presidio detects a date `"07/04/2006"` but it lacks the contextual keywords (`dob`, `born`), the evaluation verifies that the contextual gating layer successfully drops the confidence score to `0.0`.

### 4.2 Automated Regression Suite (`pytest`)
To prevent model drift and logic regressions, we utilize a CI/CD-ready regression suite:
* **`test_resume_regression.py`**: An end-to-end integration test that processes a synthetic document and asserts that:
  1. No False-Positive traps were triggered.
  2. Document formatting, layout, and section headings remain entirely uncorrupted.
  3. Determinism guarantees are upheld across repeated entities.

---

## 5. Future Metric Enhancements (Roadmap)
For continuous improvement in a production environment, the following metrics will be integrated into the observability stack:
1. **Processing Latency (P50, P90, P99):** Measuring extraction and redaction time per MB of text to ensure SLA compliance for synchronous API requests.
2. **Human-in-the-loop (HITL) Correction Rate:** In a production UI, tracking the percentage of times a human reviewer overrides or reverts a redaction. This provides a live, continuously updating Precision/Recall feedback loop.
3. **Cross-Lingual Zero-Shot Evaluation:** Expanding the evaluation dataset to test the pipeline's robustness on code-mixed text (e.g., Hinglish) and non-Latin scripts.
