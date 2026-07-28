from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analyzer import analyze_resume
from src.parser import DocumentParseError, parse_document
from src.reporting import as_json, as_text

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")
st.markdown("""
<style>
.block-container{max-width:1180px;padding-top:2rem}.score-card{border:1px solid #dce3ed;border-radius:14px;padding:1rem;background:#f8fafc}
.small-note{color:#64748b;font-size:.88rem}.stProgress>div>div>div>div{background-color:#2563eb}
</style>""", unsafe_allow_html=True)

st.title("📄 AI Resume Analyzer")
st.caption("ATS compatibility • Keyword gaps • Skill alignment • Semantic matching")

with st.sidebar:
    st.header("Analysis settings")
    use_transformer = st.toggle("Hugging Face semantic model", value=True, help="Downloads MiniLM on first use; falls back to TF-IDF if unavailable.")
    st.info("Your files are processed in memory. This sample app does not intentionally store uploaded documents.")
    st.markdown("**Best results**\n- Use a text-based PDF or DOCX\n- Paste the complete job description\n- Keep standard resume headings")

left, right = st.columns(2, gap="large")
with left:
    st.subheader("1. Upload resume")
    resume_file = st.file_uploader("Resume file", type=["pdf", "docx", "doc"], help="PDF, DOCX, or legacy DOC")
    if resume_file:
        st.success(f"Selected: {resume_file.name}")

with right:
    st.subheader("2. Add job description")
    jd_mode = st.radio("Input method", ["Paste text", "Upload file", "Combine both"], horizontal=True)
    pasted_jd = ""
    jd_file = None
    if jd_mode in {"Paste text", "Combine both"}:
        pasted_jd = st.text_area("Paste job description", height=190, placeholder="Paste responsibilities, required skills, and qualifications...")
    if jd_mode in {"Upload file", "Combine both"}:
        jd_file = st.file_uploader("Job-description file", type=["pdf", "docx", "doc", "txt"], key="jd_file")

analyze = st.button("Analyze resume", type="primary", use_container_width=True)
if analyze:
    if not resume_file:
        st.error("Upload a resume before analyzing.")
        st.stop()
    if not pasted_jd.strip() and not jd_file:
        st.error("Paste or upload a job description before analyzing.")
        st.stop()
    try:
        with st.spinner("Extracting text and comparing the documents..."):
            resume = parse_document(resume_file, resume_file.name)
            jd_parts = [pasted_jd.strip()] if pasted_jd.strip() else []
            if jd_file:
                parsed_jd = parse_document(jd_file, jd_file.name)
                jd_parts.append(parsed_jd.text)
            jd_text = "\n\n".join(jd_parts)
            result = analyze_resume(resume.text, jd_text, resume.file_type, use_transformer)
            st.session_state["analysis_result"] = result
            st.session_state["resume_preview"] = resume.text
            st.session_state["jd_preview"] = jd_text
            st.session_state["parse_warnings"] = resume.warnings or []
    except DocumentParseError as exc:
        st.error(str(exc))
        st.stop()
    except Exception as exc:
        st.error(f"Analysis failed: {exc}")
        st.stop()

if "analysis_result" in st.session_state:
    result = st.session_state["analysis_result"]
    st.divider()
    st.subheader("Analysis dashboard")
    if st.session_state.get("parse_warnings"):
        for warning in st.session_state["parse_warnings"]:
            st.warning(warning)

    cols = st.columns(5)
    metrics = [
        ("Overall match", result["overall_score"]), ("ATS", result["ats"]["score"]),
        ("Keywords", result["keyword_score"]), ("Skills", result["skill_score"]),
        ("Semantic", result["semantic_score"]),
    ]
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, f"{value}/100")
        col.progress(value / 100)
    st.caption(f"Semantic engine: {result['semantic_engine']} · Overall = 25% ATS + 30% keywords + 30% skills + 15% semantic similarity")

    overview, skills, keywords, ats_tab, actions = st.tabs(["Overview", "Skill alignment", "Keyword gaps", "ATS checks", "Action plan"])
    with overview:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Matched skills")
            st.write(", ".join(result["matched_skills"]) or "No catalogued skills matched.")
        with c2:
            st.markdown("#### Potential gaps")
            st.write(", ".join(result["missing_skills"]) or "No catalogued skill gaps detected.")
        chart = pd.DataFrame({"Area": [m[0] for m in metrics[1:]], "Score": [m[1] for m in metrics[1:]]}).set_index("Area")
        st.bar_chart(chart, color="#2563eb")
    with skills:
        all_skills = sorted(set(result["matched_skills"]) | set(result["missing_skills"]))
        rows = [{"Skill": s, "Status": "Matched" if s in result["matched_skills"] else "Gap", "In resume": s in result["matched_skills"]} for s in all_skills]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption("A gap means the term was detected in the job description but not the resume. Add it only if truthful.")
    with keywords:
        frame = pd.DataFrame(result["keywords"])
        if not frame.empty:
            frame["status"] = frame["present"].map({True: "Present", False: "Missing"})
            st.dataframe(frame[["keyword", "job_frequency", "status"]], use_container_width=True, hide_index=True)
    with ats_tab:
        details = result["ats"]
        component_data = pd.DataFrame([
            {"Check": "Parseability", "Points": details["parseability"], "Maximum": 20},
            {"Check": "Contact information", "Points": details["contact_information"], "Maximum": 20},
            {"Check": "Standard sections", "Points": details["standard_sections"], "Maximum": 25},
            {"Check": "Formatting safety", "Points": details["formatting_safety"], "Maximum": 20},
            {"Check": "Content quality", "Points": details["content_quality"], "Maximum": 15},
        ])
        st.dataframe(component_data, use_container_width=True, hide_index=True)
        for finding in details["findings"]:
            st.warning(finding)
    with actions:
        for index, item in enumerate(result["recommendations"], 1):
            st.markdown(f"**{index}.** {item}")

    with st.expander("Extracted text preview"):
        p1, p2 = st.columns(2)
        p1.text_area("Resume", st.session_state["resume_preview"][:6000], height=260, disabled=True)
        p2.text_area("Job description", st.session_state["jd_preview"][:6000], height=260, disabled=True)

    d1, d2 = st.columns(2)
    d1.download_button("Download text report", as_text(result), "resume_analysis.txt", "text/plain", use_container_width=True)
    d2.download_button("Download JSON data", as_json(result), "resume_analysis.json", "application/json", use_container_width=True)
    st.info(result["disclaimer"])
