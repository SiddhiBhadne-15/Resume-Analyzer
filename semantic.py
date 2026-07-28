"""Semantic similarity with a Hugging Face transformer and a lightweight fallback."""
from __future__ import annotations

from functools import lru_cache


def lexical_similarity(left: str, right: str) -> float:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    if not left.strip() or not right.strip():
        return 0.0
    matrix = TfidfVectorizer(ngram_range=(1, 2), stop_words="english").fit_transform([left, right])
    return float(cosine_similarity(matrix[0:1], matrix[1:2])[0, 0])


@lru_cache(maxsize=1)
def _load_hf_model(model_name: str):
    import torch
    from transformers import AutoModel, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()
    return tokenizer, model, torch


def hf_similarity(left: str, right: str, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> tuple[float, str]:
    """Return cosine similarity and engine name. Falls back if model cannot load."""
    try:
        import torch.nn.functional as functional
        tokenizer, model, torch = _load_hf_model(model_name)

        def embed(text: str):
            encoded = tokenizer(text, padding=True, truncation=True, max_length=512, return_tensors="pt")
            with torch.no_grad():
                output = model(**encoded).last_hidden_state
            mask = encoded["attention_mask"].unsqueeze(-1).expand(output.size()).float()
            vector = (output * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
            return functional.normalize(vector, p=2, dim=1)

        score = float((embed(left) @ embed(right).T).item())
        return max(0.0, min(score, 1.0)), "Hugging Face MiniLM"
    except Exception:
        return lexical_similarity(left, right), "TF-IDF fallback"
