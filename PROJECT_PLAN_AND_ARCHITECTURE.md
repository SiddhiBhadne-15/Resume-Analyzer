# Project Plan and Architecture

## 1. Goal and scope

Build an explainable analyzer that accepts a resume and a target job description, estimates ATS readability, measures content alignment, exposes gaps, and suggests ethical improvements. It does not automatically rewrite or fabricate credentials.

## 2. User workflow

1. Upload PDF/DOCX/DOC resume.
2. Paste a job description, upload PDF/DOCX/DOC/TXT, or combine both.
3. Select transformer or lightweight mode.
4. Run analysis.
5. Review overall and component scores.
6. Inspect matched/missing skills, keyword table, ATS findings, and action plan.
7. Download text or JSON results.

## 3. Logical architecture

```text
Streamlit UI
   │
   ├── Input validation
   ▼
Document Parser ── PDF: PyPDF2
   │              DOCX: python-docx
   │              DOC: antiword
   ▼
Text normalization / spaCy tokenization
   │
   ├── ATS rules
   ├── Skill taxonomy + alias matcher
   ├── Keyword extractor
   └── HF MiniLM embeddings (TF-IDF fallback)
   ▼
Weighted scoring and recommendations
   ▼
Dashboard + TXT/JSON exports
```

## 4. Modules

| Module | Responsibility |
|---|---|
| `app.py` | input controls, validation, dashboard, downloads |
| `parser.py` | safe in-memory extraction and actionable errors |
| `nlp.py` | normalization, aliases, skill and keyword extraction |
| `semantic.py` | transformer mean pooling and TF-IDF fallback |
| `analyzer.py` | component scores, weighted result, recommendations |
| `reporting.py` | machine- and human-readable exports |
| `skills.json` | maintainable domain taxonomy |

## 5. NLP pipeline

- Normalize case, dashes, whitespace, and punctuation while retaining technical symbols (`C++`, `C#`).
- Extract known multiword skills using boundary-aware matching.
- Canonicalize aliases such as Amazon Web Services → AWS.
- Use spaCy tokenization/lemmatization when `en_core_web_sm` is present; use a blank pipeline or regex otherwise.
- Rank job-description unigrams/bigrams by frequency and known-skill status.
- Embed both documents with Hugging Face MiniLM, attention-mask mean pooling, and cosine similarity.
- Preserve full-document use for rule/keyword layers; transformer representation is capped at 512 tokens.

## 6. Scoring logic

- **ATS compatibility (25%)**: parseability 20, contact 20, sections 25, formatting 20, content quality 15.
- **Keyword coverage (30%)**: fraction of top job terms present in the resume.
- **Skill alignment (30%)**: weighted overlap; mandatory cues 1.5×, normal 1.0×, preferred 0.7×.
- **Semantic similarity (15%)**: embedding cosine similarity, bounded to 0–100.

Weights belong in configuration in a future iteration and should be validated using labeled data rather than presented as universal.

## 7. Data model and optional database

The reference app is stateless and needs no database. A production history feature can use PostgreSQL:

- `users(id, email_hash, created_at, consent_version)`
- `analyses(id, user_id, created_at, overall_score, ats_score, keyword_score, skill_score, semantic_score, model_version)`
- `analysis_items(id, analysis_id, kind, normalized_term, status, weight)`
- `documents(id, analysis_id, type, object_key, encrypted, expires_at)`

Do not save raw documents by default. If storage is enabled, obtain explicit consent, encrypt in transit/at rest, use expiring object keys, isolate tenants, and offer immediate deletion.

## 8. API design (production option)

- `POST /v1/analyses` multipart resume + JD/file/text + options
- `GET /v1/analyses/{id}` result status and scores
- `DELETE /v1/analyses/{id}` hard-delete analysis and documents
- `GET /v1/taxonomies/{name}` taxonomy version

Use OAuth/OIDC, request IDs, upload limits, MIME/magic-byte checks, asynchronous workers, rate limits, and response schemas. Never include extracted resume text in ordinary logs.

## 9. Delivery plan

| Sprint | Output |
|---|---|
| 1 | requirements, UI wireframe, parsers, sample documents |
| 2 | ATS rules, skills taxonomy, keyword extraction, tests |
| 3 | transformer similarity, fallback, dashboard, exports |
| 4 | evaluation, accessibility, security hardening, deployment |

## 10. Testing and evaluation

- Unit tests for parsers, boundaries, aliases, ranges, mandatory/preferred weighting.
- Integration tests with text PDFs, multi-column DOCX, empty/corrupt/encrypted files, and long JDs.
- Create a consented, de-identified benchmark across job families.
- Human annotators label skills and relevance; report precision, recall, F1, score correlation, and subgroup error analysis.
- Load-test concurrent model inference and measure cold-start latency.

## 11. Deployment

Containerize on Python 3.11. Host via Streamlit Cloud for demonstration or behind a FastAPI service and worker queue for production. Cache the approved model during image build, run without root privileges, scan dependencies, enforce 10 MB uploads, terminate long parses, and configure health checks. Add CI for lint/test/build and a staging environment.

## 12. Risks and controls

- **False precision:** show component evidence and disclaimer.
- **Bias:** do not infer age, gender, ethnicity, disability, or personality; evaluate across groups.
- **Prompt manipulation:** uploaded text is data only; no autonomous actions.
- **Malicious files:** size/type checks, patched libraries, sandbox parsing, malware scan.
- **Privacy:** memory-first processing, minimal logs, explicit retention controls.
- **Keyword stuffing:** recommend natural, truthful evidence rather than repetition.
