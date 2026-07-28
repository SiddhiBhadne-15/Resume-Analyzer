"""NLP utilities: normalization, phrase matching and keyword extraction."""
from __future__ import annotations

import json
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

DEFAULT_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "is", "it", "of", "on", "or", "our", "that", "the", "this", "to", "we",
    "will", "with", "you", "your", "job", "role", "work", "team", "candidate", "required",
    "preferred", "responsibilities", "skills", "experience", "years", "using", "strong",
}

ALIASES = {
    "amazon web services": "aws", "google cloud platform": "gcp", "google cloud": "gcp",
    "microsoft azure": "azure", "nodejs": "node.js", "react.js": "react",
    "express.js": "express", "postgres": "postgresql", "sklearn": "scikit-learn",
    "natural language processing": "nlp", "continuous integration": "ci/cd",
    "continuous delivery": "ci/cd", "large language model": "llm",
    "large language models": "llm", "retrieval augmented generation": "rag",
    "restful api": "rest api", "golang": "go",
}


def normalize(text: str) -> str:
    text = text.lower().replace("–", "-").replace("—", "-")
    text = re.sub(r"[^a-z0-9+#./-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def canonical(term: str) -> str:
    value = normalize(term)
    return ALIASES.get(value, value)


@lru_cache(maxsize=1)
def load_skill_catalog() -> dict[str, list[str]]:
    path = Path(__file__).resolve().parents[1] / "config" / "skills.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def contains_phrase(text: str, phrase: str) -> bool:
    text_n = f" {normalize(text)} "
    phrase_n = normalize(phrase)
    return bool(re.search(r"(?<![a-z0-9+#])" + re.escape(phrase_n) + r"(?![a-z0-9+#])", text_n))


def extract_skills(text: str) -> dict[str, list[str]]:
    found: dict[str, set[str]] = {}
    for category, terms in load_skill_catalog().items():
        for term in sorted(terms, key=len, reverse=True):
            if contains_phrase(text, term):
                found.setdefault(category, set()).add(canonical(term))
    return {category: sorted(values) for category, values in found.items()}


def flatten_skills(skills: dict[str, list[str]]) -> set[str]:
    return {canonical(skill) for values in skills.values() for skill in values}


def extract_keywords(text: str, limit: int = 30) -> list[tuple[str, int]]:
    """Extract useful uni/bi-gram terms; uses spaCy if its model is installed."""
    normalized = normalize(text)
    tokens: list[str] = []
    try:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            nlp = spacy.blank("en")
        doc = nlp(normalized)
        tokens = [
            token.lemma_.lower() if token.lemma_ else token.text.lower()
            for token in doc
            if token.is_alpha and not token.is_stop and len(token.text) > 2
        ]
    except ImportError:
        tokens = re.findall(r"[a-z][a-z+#.-]{2,}", normalized)
    tokens = [t for t in tokens if t not in DEFAULT_STOPWORDS]
    counter = Counter(tokens)
    for left, right in zip(tokens, tokens[1:]):
        phrase = f"{left} {right}"
        if left not in DEFAULT_STOPWORDS and right not in DEFAULT_STOPWORDS:
            counter[phrase] += 1
    # Prioritize known skills while preserving frequency information.
    known = flatten_skills(extract_skills(text))
    ranked = sorted(counter.items(), key=lambda item: (canonical(item[0]) in known, item[1], len(item[0])), reverse=True)
    return ranked[:limit]
