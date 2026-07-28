"""Downloadable plain-text/JSON report helpers."""
from __future__ import annotations
import json
from datetime import datetime


def as_json(result: dict) -> str:
    return json.dumps(result, indent=2, ensure_ascii=False)


def as_text(result: dict) -> str:
    lines = [
        "AI RESUME ANALYZER REPORT",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", "",
        f"Overall match: {result['overall_score']}/100",
        f"ATS compatibility: {result['ats']['score']}/100",
        f"Keyword coverage: {result['keyword_score']}/100",
        f"Skill alignment: {result['skill_score']}/100",
        f"Semantic similarity: {result['semantic_score']}/100 ({result['semantic_engine']})", "",
        "MATCHED SKILLS", ", ".join(result['matched_skills']) or "None detected", "",
        "POSSIBLE SKILL GAPS", ", ".join(result['missing_skills']) or "None detected", "",
        "RECOMMENDATIONS",
    ]
    lines.extend(f"- {item}" for item in result["recommendations"])
    lines += ["", result["disclaimer"]]
    return "\n".join(lines)
