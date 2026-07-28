# AI Resume Analyzer

A privacy-conscious Streamlit application that compares a PDF/DOCX/DOC resume with a pasted or uploaded job description. It reports ATS compatibility, keyword gaps, skill alignment, semantic similarity, and prioritized improvements.

## Features

- Resume input: PDF, DOCX, and legacy DOC (DOC requires `antiword`)
- Job-description input: pasted text, PDF, DOCX, DOC, TXT, or paste + file combined
- ATS checks: parseability, contact details, standard sections, formatting risk, achievement quality
- Skill matching: configurable category catalog, phrase boundaries, alias normalization
- Keyword coverage: frequency-ranked terms and missing terminology
- Semantic matching: Hugging Face `sentence-transformers/all-MiniLM-L6-v2`
- Automatic TF-IDF fallback when the transformer cannot load
- Downloadable text and JSON reports
- No database or deliberate document persistence in the reference implementation

## Quick start

```bash
cd ai-resume-analyzer
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
pip install -r requirements.txt
# Optional but improves spaCy keyword extraction:
python -m spacy download en_core_web_sm
streamlit run app.py
```

Open `http://localhost:8501`. The Hugging Face model is downloaded and cached on first semantic analysis. Turn off **Hugging Face semantic model** in the sidebar for an offline/lightweight run.

## Docker

```bash
docker build -t ai-resume-analyzer .
docker run --rm -p 8501:8501 ai-resume-analyzer
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Project structure

```text
app.py                   Streamlit interface
src/parser.py            PDF, DOCX, DOC, TXT extraction
src/nlp.py               normalization, skills, keywords
src/semantic.py          HF embeddings + TF-IDF fallback
src/analyzer.py          ATS and match scoring
src/reporting.py         downloadable output
config/skills.json       editable skill taxonomy
tests/                    unit tests
docs/                     plan, specification, report, presentation
```

## Scoring model

`Overall = 25% ATS + 30% keyword coverage + 30% skill alignment + 15% semantic similarity`

ATS is a 100-point heuristic: parseability 20, contact information 20, standard sections 25, formatting safety 20, and content quality 15. Required skills receive weight 1.5, ordinary skills 1.0, and preferred skills 0.7 when cue wording appears near the term.

Scores are explainable guidance—not predictions of decisions by a particular ATS or employer. Users should never add keywords or skills they cannot substantiate.

## Deployment

Deploy to Streamlit Community Cloud, Render, Azure App Service, AWS App Runner/ECS, or any Docker host. For production: pin dependency hashes, scan uploads, cap size/time, avoid logs containing document text, add authentication, publish retention policy, and monitor model drift.

## Known limitations

- Scanned PDFs require OCR before upload.
- Legacy DOC depends on the external `antiword` utility; DOCX is preferred.
- Keyword/skill catalogs require maintenance for specialized industries.
- Transformer input is truncated to 512 tokens; the lexical and explicit skill layers still use the full documents.
- Multi-column and graphical resumes may extract in the wrong reading order.

## License

Educational reference project. Add your preferred open-source license before public distribution.
