from src.analyzer import analyze_resume, ats_compatibility
from src.nlp import extract_skills

RESUME = """Jane Doe | jane@example.com | +91 9876543210
SUMMARY
Python developer and data analyst.
SKILLS
Python, SQL, pandas, AWS, Docker, Git
EXPERIENCE
Developed APIs and improved processing speed by 35%. Led 4 projects.
EDUCATION
B.Tech Computer Science
PROJECTS
Built a machine learning classifier with scikit-learn.
"""
JD = "We require Python, SQL, AWS, Docker, Kubernetes, machine learning and communication skills. Experience with REST API is preferred."

def test_skill_extraction_aliases():
    values = extract_skills("Amazon Web Services, React.js and PostgreSQL")
    flattened = {x for group in values.values() for x in group}
    assert {"aws", "react", "postgresql"}.issubset(flattened)

def test_ats_score_range():
    score = ats_compatibility(RESUME, "pdf").score
    assert 0 <= score <= 100

def test_analysis_finds_gap_and_match():
    result = analyze_resume(RESUME, JD, use_transformer=False)
    assert "python" in result["matched_skills"]
    assert "kubernetes" in result["missing_skills"]
    assert 0 <= result["overall_score"] <= 100
