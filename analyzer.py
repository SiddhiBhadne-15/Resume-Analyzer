"""Scoring engine for ATS compatibility and resume/job alignment."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from .nlp import canonical, extract_keywords, extract_skills, flatten_skills, normalize
from .semantic import hf_similarity

SECTION_PATTERNS = {
    "summary": r"\b(summary|profile|objective|about me)\b",
    "experience": r"\b(experience|employment|work history|professional experience)\b",
    "education": r"\b(education|academic|qualifications)\b",
    "skills": r"\b(skills|technical skills|competencies|technologies)\b",
    "projects": r"\b(projects|portfolio|personal projects)\b",
}
ACTION_VERBS = {
    "achieved", "built", "created", "delivered", "designed", "developed", "drove", "implemented",
    "improved", "increased", "launched", "led", "managed", "optimized", "reduced", "saved", "scaled",
}


@dataclass
class ATSDetails:
    parseability: int
    contact_information: int
    standard_sections: int
    formatting_safety: int
    content_quality: int
    score: int
    findings: list[str]


def ats_compatibility(text: str, file_type: str = "pdf") -> ATSDetails:
    lower = text.lower()
    findings: list[str] = []
    words = re.findall(r"\b\w+\b", text)

    parseability = 20 if len(words) >= 120 else (12 if len(words) >= 50 else 5)
    if parseability < 20:
        findings.append("Resume text is unusually short or was not fully extracted.")

    email = bool(re.search(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", text))
    phone = bool(re.search(r"(?:\+?\d[\d ()-]{7,}\d)", text))
    contact = (10 if email else 0) + (10 if phone else 0)
    if not email: findings.append("Add a professional email address in plain text.")
    if not phone: findings.append("Add a phone number in plain text.")

    present_sections = [name for name, pattern in SECTION_PATTERNS.items() if re.search(pattern, lower)]
    sections = min(25, len(present_sections) * 5)
    missing_core = {"experience", "education", "skills"} - set(present_sections)
    if missing_core:
        findings.append("Use standard headings for: " + ", ".join(sorted(missing_core)) + ".")

    formatting = 20
    if file_type == "doc":
        formatting -= 5
        findings.append("Prefer DOCX or text-based PDF over legacy DOC.")
    if "|" in text and text.count("|") > 15:
        formatting -= 5
        findings.append("Heavy table usage may confuse some ATS parsers.")
    if len(re.findall(r"[^\x00-\x7F]", text)) > max(20, len(text) * 0.02):
        formatting -= 3
        findings.append("Limit decorative symbols and non-standard characters.")

    action_count = sum(len(re.findall(rf"\b{verb}\b", lower)) for verb in ACTION_VERBS)
    quantified = len(re.findall(r"(?:\b\d+(?:\.\d+)?%|[$₹€£]\s?\d+|\b\d+\+?\s*(?:users|clients|projects|hours|days|months|years))", lower))
    quality = min(15, 4 + min(action_count, 6) + min(quantified * 2, 5))
    if action_count < 3: findings.append("Start more achievement bullets with strong action verbs.")
    if quantified < 2: findings.append("Quantify impact with percentages, scale, time, or cost metrics.")

    score = max(0, min(100, parseability + contact + sections + formatting + quality))
    return ATSDetails(parseability, contact, sections, formatting, quality, score, findings)


def _required_weight(keyword: str, jd: str) -> float:
    # Keywords near mandatory language receive higher weight.
    pattern = rf"(?:required|must have|minimum|essential)[^.\n]{{0,100}}\b{re.escape(keyword)}\b"
    preferred = rf"(?:preferred|nice to have|bonus)[^.\n]{{0,100}}\b{re.escape(keyword)}\b"
    if re.search(pattern, normalize(jd)): return 1.5
    if re.search(preferred, normalize(jd)): return 0.7
    return 1.0


def analyze_resume(resume_text: str, jd_text: str, file_type: str = "pdf", use_transformer: bool = True) -> dict:
    ats = ats_compatibility(resume_text, file_type)
    resume_skills_by_group = extract_skills(resume_text)
    jd_skills_by_group = extract_skills(jd_text)
    resume_skills = flatten_skills(resume_skills_by_group)
    jd_skills = flatten_skills(jd_skills_by_group)
    matched_skills = sorted(resume_skills & jd_skills)
    missing_skills = sorted(jd_skills - resume_skills)

    weighted_total = sum(_required_weight(skill, jd_text) for skill in jd_skills)
    weighted_match = sum(_required_weight(skill, jd_text) for skill in matched_skills)
    skill_score = round(100 * weighted_match / weighted_total) if weighted_total else 0

    jd_keywords = extract_keywords(jd_text, 35)
    resume_normalized = normalize(resume_text)
    keyword_rows = []
    for keyword, frequency in jd_keywords:
        key = canonical(keyword)
        present = key in resume_skills or re.search(rf"(?<!\w){re.escape(normalize(keyword))}(?!\w)", resume_normalized) is not None
        keyword_rows.append({"keyword": keyword, "job_frequency": frequency, "present": present})
    keyword_score = round(100 * sum(row["present"] for row in keyword_rows) / len(keyword_rows)) if keyword_rows else 0

    if use_transformer:
        semantic_value, semantic_engine = hf_similarity(resume_text, jd_text)
    else:
        from .semantic import lexical_similarity
        semantic_value, semantic_engine = lexical_similarity(resume_text, jd_text), "TF-IDF"
    semantic_score = round(semantic_value * 100)

    overall = round(ats.score * 0.25 + keyword_score * 0.30 + skill_score * 0.30 + semantic_score * 0.15)
    recommendations = list(ats.findings)
    if missing_skills:
        recommendations.append("Address genuine skill gaps: " + ", ".join(missing_skills[:8]) + ".")
    if keyword_score < 70:
        recommendations.append("Mirror relevant job-description terminology naturally in your summary and achievements.")
    if semantic_score < 55:
        recommendations.append("Tailor the summary and recent experience toward the target role's main responsibilities.")
    recommendations.append("Never add a skill you cannot demonstrate in an interview or project.")

    return {
        "overall_score": overall,
        "ats": asdict(ats),
        "keyword_score": keyword_score,
        "skill_score": skill_score,
        "semantic_score": semantic_score,
        "semantic_engine": semantic_engine,
        "resume_skills": resume_skills_by_group,
        "job_skills": jd_skills_by_group,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "keywords": keyword_rows,
        "recommendations": list(dict.fromkeys(recommendations)),
        "disclaimer": "Scores are guidance, not predictions of recruiter or ATS decisions."
    }
