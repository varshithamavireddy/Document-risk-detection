import html
import os
from pathlib import Path

import streamlit as st
from local_llm import GroqClient
from extractors import extract_document
from risk_engine import analyze_risks, answer_question

st.set_page_config(page_title="Document Risk Detection", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
:root { --navy:#111a37; --navy2:#1d2b55; --ink:#17233f; --muted:#75819a; --line:#e4eaf3; --paper:#f4f7fb; --purple:#5548ed; }
.stApp { background:var(--paper); color:var(--ink); }
.block-container { max-width:1500px; padding:1.25rem 2.3rem 3rem; }
[data-testid="stSidebar"] { background:#fff; border-right:1px solid var(--line); }
[data-testid="stSidebar"] > div:first-child { padding-top:1.5rem; }
.hero { background:linear-gradient(115deg,var(--navy),var(--navy2)); border-radius:24px; padding:32px 38px 28px; color:white; margin:0 0 20px; box-shadow:0 14px 34px #111a371c; }
.hero-top { display:flex; justify-content:space-between; align-items:flex-start; gap:20px; }
.hero h1 { font-size:34px; color:white; margin:0 0 7px; letter-spacing:-.8px; }
.hero p { color:#d0d9ed; font-size:16px; margin:0; }
.hero-tag { background:#1a806d35; color:#58e4bd; border:1px solid #37cca84d; padding:8px 14px; border-radius:20px; font-weight:700; white-space:nowrap; }
.metric-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:15px; margin-top:28px; }
.metric { background:#ffffff0d; border:1px solid #ffffff1a; border-radius:17px; padding:16px 19px; min-height:96px; }
.metric-label { color:#aab5cb; font-size:13px; font-weight:600; }
.metric-value { color:white; font-size:27px; font-weight:750; margin-top:6px; }
.metric-note { color:#9daac2; font-size:12px; margin-top:2px; }
.panel { background:white; border:1px solid var(--line); border-radius:22px; padding:20px 23px; margin:0 0 18px; box-shadow:0 5px 20px #1c2c4810; }
.panel-title { color:var(--ink); font-weight:750; font-size:18px; margin:0 0 4px; }
.panel-sub { color:var(--muted); font-size:13px; margin-bottom:14px; }
.risk-score { font-size:20px; font-weight:800; color:#18243f; }
.small-label { color:var(--muted); font-size:12px; }
[data-testid="stChatMessage"] { background:#fff !important; border:1px solid #e4eaf3 !important; border-radius:14px !important; color:#17233f !important; }
[data-testid="stChatMessage"] *, [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li, [data-testid="stChatMessage"] td, [data-testid="stChatMessage"] th { color:#17233f !important; }
[data-testid="stChatMessage"] table { color:#17233f !important; border-color:#d7dfeb !important; }
[data-testid="stChatInput"], [data-testid="stChatInput"] form, [data-testid="stChatInput"] > div { background:#fff !important; border:1px solid #cbd5e1 !important; border-radius:14px !important; }
[data-testid="stChatInput"] textarea { background:#fff !important; color:#17233f !important; -webkit-text-fill-color:#17233f !important; caret-color:#17233f !important; }
[data-testid="stChatInput"] textarea::placeholder { color:#66758d !important; opacity:1 !important; -webkit-text-fill-color:#66758d !important; }
[data-testid="stChatInput"] button { color:#fff !important; background:#5548ed !important; }
div[data-testid="stFileUploader"] { background:#fff; border:1px dashed #b8c4d9; border-radius:16px; padding:12px; }
.stButton > button[kind="primary"] { background:var(--purple); border-color:var(--purple); border-radius:10px; font-weight:700; }
.stButton > button { border-radius:10px; }
@media(max-width:900px) { .metric-grid {grid-template-columns:repeat(2,1fr)} .block-container {padding:1rem} .hero {padding:24px} }
</style>
""", unsafe_allow_html=True)

# Read the local key without placing it in the interface or source code.
env_file = Path(__file__).with_name(".env")
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip("\"'"))
api_key = os.getenv("GROQ_API_KEY", "").strip()

with st.sidebar:
    st.markdown("<div style='font-size:23px;font-weight:800;color:#17233f;padding:0 0 20px'>🛡️ RiskLens</div>", unsafe_allow_html=True)
    st.caption("DOCUMENT INTELLIGENCE")
    page = st.radio("Navigation", ["Overview", "Risk findings", "Document chat"], label_visibility="collapsed")
    st.divider()
    st.caption("MODEL SETTINGS")
    model = st.text_input("Groq model", value="openai/gpt-oss-20b")
    st.caption("Scores are screening indices, not validated probabilities.")
    st.divider()
    if api_key:
        st.success("Groq API connected")
    else:
        st.warning("Add GROQ_API_KEY to .env")

# Current session state
risks = st.session_state.get("risks", [])
doc_name = st.session_state.get("document_name", "No document uploaded")

st.markdown(f"""
<div class="hero"><div class="hero-top"><div><h1>Document Risk Detection</h1>
<p>Review documents, identify risks, and ask questions grounded in the source.</p></div>
<div class="hero-tag">{len(risks)} findings</div></div>
<div class="metric-grid">
<div class="metric"><div class="metric-label">DOCUMENT</div><div class="metric-value" style="font-size:18px">{html.escape(doc_name[:34])}</div><div class="metric-note">Current review</div></div>
<div class="metric"><div class="metric-label">TOTAL RISKS</div><div class="metric-value">{len(risks)}</div><div class="metric-note">Evidence-linked findings</div></div>
<div class="metric"><div class="metric-label">HIGH PRIORITY</div><div class="metric-value" style="color:#ff7186">{sum(1 for r in risks if r.get('score', 0) >= 70)}</div><div class="metric-note">Score 70% and above</div></div>
<div class="metric"><div class="metric-label">AVERAGE SCORE</div><div class="metric-value" style="color:#f8c84e">{round(sum(r.get('score',0) for r in risks)/len(risks)) if risks else 0}%</div><div class="metric-note">Rubric-based risk index</div></div>
</div></div>
""", unsafe_allow_html=True)

upload_col, action_col = st.columns([3, 1], vertical_alignment="bottom")
with upload_col:
    uploaded = st.file_uploader("Upload a document", type=["pdf", "docx", "xlsx", "pptx", "txt", "md", "csv", "json", "png", "jpg", "jpeg", "tif", "tiff"], label_visibility="visible")
if uploaded:
    try:
        extracted = extract_document(uploaded.name, uploaded.getvalue())
        if not extracted.strip():
            st.error("No readable text found. For scanned PDFs, OCR the pages first.")
            st.stop()
        if st.session_state.get("document_name") != uploaded.name:
            st.session_state.pop("risks", None)
            st.session_state.pop("chat", None)
        st.session_state["document_text"] = extracted[:300_000]
        st.session_state["document_name"] = uploaded.name
    except Exception as exc:
        st.error(f"Could not read this file: {exc}")

has_doc = bool(st.session_state.get("document_text"))
if has_doc:
    text = st.session_state["document_text"]
    with st.expander("Preview extracted document text"):
        st.text(text[:6_000] + ("\n… preview shortened" if len(text) > 6_000 else ""))
    with action_col:
        analyze = st.button("⚡ Analyze risks", type="primary", use_container_width=True, disabled=not api_key)
    if analyze:
        st.session_state.pop("risks", None)
        progress = st.progress(0, text="Starting risk analysis…")
        status = st.empty()
        def update_progress(done, total):
            progress.progress(done / total, text=f"Analyzed section {done} of {total}…")
        try:
            st.session_state["risks"] = analyze_risks(GroqClient(api_key), model, text, update_progress)
            progress.progress(1.0, text="Analysis complete")
            st.rerun()
        except Exception as exc:
            progress.empty()
            status.error(f"Risk analysis failed: {exc}")
elif not api_key:
    st.error("Add GROQ_API_KEY to C:\\Riskdetection\\.env and restart Streamlit.")

if page in ["Overview", "Risk findings"]:
    st.markdown('<div class="panel"><div class="panel-title">Risk findings</div><div class="panel-sub">Prioritized issues with source evidence and recommended mitigation.</div>', unsafe_allow_html=True)
    if not risks:
        st.info("Upload a document and select Analyze risks to populate findings.")
    else:
        tabs = st.tabs(["All risks", "High", "Moderate", "Low"])
        filters = [None, "High", "Moderate", "Low"]
        for tab, level in zip(tabs, filters):
            with tab:
                filtered = [r for r in risks if level is None or r.get("level") == level]
                query = st.text_input("Search risks", key=f"risk-search-{level or 'all'}", placeholder="Search by title or category")
                if query:
                    filtered = [r for r in filtered if query.lower() in (r.get("title", "") + " " + r.get("category", "")).lower()]
                for i, risk in enumerate(filtered, 1):
                    with st.expander(f"{risk.get('title','Risk finding')}  ·  {risk.get('score',0)}%  ·  {risk.get('level','Review')}", expanded=False):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.write(f"**{risk.get('category','General')}** · Confidence: {risk.get('confidence','medium')}")
                            st.write(risk.get("description", ""))
                        with c2:
                            st.metric("Risk score", f"{risk.get('score',0)}%")
                        st.info("Evidence: " + risk.get("evidence", "No evidence excerpt returned."))
                        st.caption(f"Impact {risk.get('impact',1)}/5 · Likelihood {risk.get('likelihood',1)}/5 · Control gap {risk.get('control_gap',1)}/5")
                        st.markdown("**Mitigations**")
                        for action in risk.get("mitigations", []):
                            st.markdown(f"- {action}")
    st.markdown("</div>", unsafe_allow_html=True)

if page == "Document chat":
    st.markdown('<div class="panel"><div class="panel-title">Ask about this document</div><div class="panel-sub">Answers use retrieved passages from the current upload.</div>', unsafe_allow_html=True)
    if not has_doc:
        st.info("Upload a document first.")
    elif not api_key:
        st.warning("Add GROQ_API_KEY to .env before starting chat.")
    else:
        for msg in st.session_state.get("chat", []):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        question = st.chat_input("Ask about risk, evidence, or mitigation…")
        if question:
            st.session_state.setdefault("chat", []).append({"role":"user", "content":question})
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                with st.spinner("Searching document passages…"):
                    try:
                        answer = answer_question(GroqClient(api_key), model, st.session_state["document_text"], question)
                        st.markdown(answer)
                        st.session_state["chat"].append({"role":"assistant", "content":answer})
                    except Exception as exc:
                        st.error(f"Could not answer: {exc}")
    st.markdown("</div>", unsafe_allow_html=True)
