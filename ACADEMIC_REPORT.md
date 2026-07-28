# AI Resume Analyzer — Academic Project Report

## 1. Introduction

Recruitment platforms commonly use automated systems to store, search, and rank application information. Applicants often lack visibility into whether a resume can be parsed and whether it uses language aligned with a vacancy. This project develops an explainable decision-support prototype rather than attempting to reverse engineer a proprietary ATS.

## 2. Problem statement

Given a resume and job description, extract their text and provide: (1) ATS-oriented compatibility feedback, (2) missing job keywords, (3) matched and missing skills, (4) semantic alignment, and (5) prioritized improvements. Inputs must support both uploaded files and pasted JD text.

## 3. Objectives

- Parse common resume and JD formats.
- Identify standard resume structure and contact information.
- Normalize aliases and match technical/soft skills.
- combine lexical matching with transformer semantics.
- Present explainable sub-scores and ethical recommendations.
- Maintain a modular, testable, deployable Python codebase.

## 4. Literature and technical background

Traditional information retrieval represents documents by term frequency and inverse document frequency. Cosine similarity measures directional similarity between vectors. Transformer encoders create contextual token representations and can provide stronger semantic matching than exact overlap. ATS products vary widely, so universal compatibility cannot be measured directly; transparent heuristics are more defensible for an educational tool.

## 5. Requirements and feasibility

The implementation uses Python, Streamlit, PyPDF2, python-docx, spaCy, scikit-learn, PyTorch, and Hugging Face Transformers. These are open-source and run on a normal laptop. MiniLM offers a practical accuracy/latency compromise. Legacy DOC needs `antiword`; scanned PDFs remain outside the MVP unless OCR is added.

## 6. System design

The presentation layer validates inputs and displays results. The ingestion layer extracts text. The NLP layer normalizes text, extracts skills and keywords, and computes semantic vectors. The scoring layer combines ATS, keyword, skill, and semantic components. The reporting layer exports TXT and JSON. The skills taxonomy remains external JSON for maintainability.

## 7. Methodology

ATS compatibility totals 100 points across parseability (20), contact information (20), standard sections (25), formatting safety (20), and achievement content (15). Job skills found near mandatory cues receive a 1.5 weight; ordinary and preferred terms receive 1.0 and 0.7. Keyword coverage measures presence among ranked JD terms. Semantic similarity uses attention-mask mean pooling of MiniLM hidden states and cosine similarity. The final score weights ATS 25%, keywords 30%, skills 30%, and semantics 15%.

## 8. Implementation

`parser.py` reads supported files in memory and includes table text from DOCX. `nlp.py` performs phrase-boundary matching and canonicalizes aliases. `semantic.py` loads and caches the Hugging Face model, with TF-IDF fallback. `analyzer.py` calculates scores and recommendations. `app.py` implements the Streamlit dashboard and input modes.

## 9. Testing

Unit tests verify TXT/DOCX extraction, table handling, skill aliases, score ranges, matched terms, and missing terms. Further validation should use de-identified resumes from multiple job families with independent human labels. Suitable metrics include skill extraction precision/recall/F1, correlation with human relevance judgments, subgroup error rates, latency, and failure rate.

## 10. Results and discussion

The prototype produces traceable components rather than a single opaque verdict. Exact matching explains concrete gaps, while semantic similarity captures broader topical overlap. The fallback improves availability. Limitations include finite taxonomy coverage, 512-token transformer truncation, extraction order in complex layouts, lack of OCR, and absence of evidence that the heuristic predicts any employer decision.

## 11. Security, privacy, and ethics

Resume data is sensitive. The reference app does not intentionally persist documents. Production systems should scan uploads, verify MIME signatures, sandbox parsing, encrypt data, define short retention, and support deletion. The system must not infer protected characteristics or personality. Recommendations explicitly prohibit adding skills the applicant cannot demonstrate. Scores require a disclaimer and should not become an automated hiring gate.

## 12. Conclusion

The project demonstrates how document processing, classical NLP, taxonomy matching, and transformer embeddings can support explainable resume tailoring. Its modular architecture is suitable for academic demonstration and extension. Future work should prioritize labeled evaluation, section-aware embeddings, OCR, multilingual support, and fairness governance over merely adding a larger model.

## References

1. Hugging Face Transformers documentation, https://huggingface.co/docs/transformers/
2. spaCy usage documentation, https://spacy.io/usage
3. Streamlit documentation, https://docs.streamlit.io/
4. PyPDF2 documentation, https://pypdf2.readthedocs.io/
5. Sentence-Transformers model card: all-MiniLM-L6-v2, https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
