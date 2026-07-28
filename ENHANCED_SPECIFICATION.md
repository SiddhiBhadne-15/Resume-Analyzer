# Enhanced Product Specification

## Personas

- **Applicant:** wants a transparent checklist before applying.
- **Career counselor:** compares iterations and explains skill gaps.
- **Administrator:** maintains taxonomies, models, security, and retention.

## Functional requirements

- FR-1: Accept PDF, DOCX, DOC resume up to the configured limit.
- FR-2: Accept JD as pasted text, uploaded PDF/DOCX/DOC/TXT, or both.
- FR-3: Reject empty, unsupported, encrypted, corrupt, or non-text documents with actionable errors.
- FR-4: Display ATS score and component-level evidence.
- FR-5: Display matched and potentially missing skills by normalized term.
- FR-6: Display ranked JD keywords and resume presence.
- FR-7: Compute semantic similarity with a transformer and safe fallback.
- FR-8: Produce prioritized, truthful recommendations.
- FR-9: Export text and JSON reports.
- FR-10: Never claim that a score guarantees selection.

## Non-functional requirements

- Typical lexical analysis under 3 seconds after extraction; transformer cold start separately reported.
- Keyboard-usable, responsive, color not the sole status indicator.
- No raw-document persistence by default.
- Deterministic rules for equal inputs and recorded model/taxonomy versions in production.
- Structured errors without stack traces or leaked document content.

## User stories and acceptance criteria

1. **As an applicant, I can paste a JD.** Given a valid resume and pasted JD, analysis displays five scores and evidence.
2. **As an applicant, I can upload a JD.** PDF/DOCX/DOC/TXT content is extracted and analyzed.
3. **As an applicant, I can combine sources.** Both input texts are concatenated exactly once.
4. **As an applicant, I see limitations.** A scanned PDF gives OCR guidance rather than a misleading score.
5. **As a counselor, I can export results.** TXT and valid JSON contain the displayed scores and gaps.
6. **As a privacy-conscious user, I understand processing.** The UI states the storage behavior and disclaimer.

## Recommended model strategy

- Default: `sentence-transformers/all-MiniLM-L6-v2`, small and suitable for semantic similarity.
- Lightweight/offline: word/bigram TF-IDF cosine similarity.
- Better long-document roadmap: segment by resume section and JD responsibility, embed chunks, aggregate top-k alignments.
- Skill NER roadmap: occupation-specific spaCy/HF token classifier evaluated against a labeled taxonomy.
- OCR roadmap: Tesseract or managed document AI behind consent and security controls.

## Future backlog

- Section-aware alignment and evidence snippets
- Resume rewrite suggestions with before/after diff and factuality confirmation
- Multilingual pipeline and locale-aware phone/contact parsing
- ESCO/O*NET skill taxonomy and occupation mapping
- Multiple-resume comparison against one vacancy
- Recruiter mode only after legal, fairness, and governance review
- PDF report generation, authenticated history, expiring storage

## Definition of done

Code runs from documented setup, supported files produce results, unit tests pass, errors are actionable, output evidence matches scoring data, privacy/disclaimer text is visible, dependencies are pinned to compatible ranges, and documentation covers deployment and limitations.
