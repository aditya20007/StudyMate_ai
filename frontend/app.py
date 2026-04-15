# ============================================================
# frontend/app.py — StudyMate AI · Complete Streamlit Frontend
# ============================================================

import streamlit as st
import requests
import json
import os
import time
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
# Read backend URL from Streamlit secrets (deployed) or environment variable (local)
# In Streamlit Cloud: set FRONTEND_BACKEND_URL in app Settings → Secrets
# Locally: set in .env or just uses localhost default
BACKEND_URL = "http://127.0.0.1:8000"
# Strip trailing slash to avoid double-slash URLs
BACKEND_URL = BACKEND_URL.rstrip("/")

BACKEND_URL ="https://studymate-ai-0zvn.onrender.com/"

st.set_page_config(
    page_title="StudyMate AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": "https://github.com/studymate-ai",
        "About": "StudyMate AI v1.0.0 — AI-Powered Learning Assistant",
    },
)

# ─────────────────────────────────────────────
# Global CSS — Dark Academic Theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: #e8e6df;
}
.main { background: #0e0e13; }
section[data-testid="stSidebar"] {
    background: #13131a;
    border-right: 1px solid #1f1f2e;
}

/* ── Hero Header ── */
.hero {
    background: linear-gradient(135deg, #13131a 0%, #1a1428 40%, #0e1f3a 100%);
    border: 1px solid #2a2a42;
    border-radius: 20px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
.hero h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 3rem;
    font-weight: 400;
    color: #f0ede6;
    margin: 0 0 0.5rem 0;
    line-height: 1.1;
}
.hero h1 span { color: #818cf8; font-style: italic; }
.hero p {
    color: #8b8aa0;
    font-size: 1.05rem;
    margin: 0;
    font-weight: 300;
}

/* ── Sidebar Nav ── */
.nav-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #4b4b6a;
    padding: 1rem 0 0.4rem 0;
}
.status-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 500;
    margin-bottom: 0.3rem;
}
.chip-online { background: rgba(52,211,153,0.12); color: #34d399; border: 1px solid rgba(52,211,153,0.2); }
.chip-offline { background: rgba(248,113,113,0.12); color: #f87171; border: 1px solid rgba(248,113,113,0.2); }
.chip-warn { background: rgba(251,191,36,0.12); color: #fbbf24; border: 1px solid rgba(251,191,36,0.2); }

/* ── Cards ── */
.card {
    background: #13131a;
    border: 1px solid #1f1f2e;
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s;
}
.card:hover { border-color: #3d3d5c; }
.card-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.1rem;
    color: #c8c6d9;
    margin: 0 0 0.5rem 0;
}

/* ── Source Badges ── */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    margin-right: 6px;
}
.badge-pdf { background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.25); }
.badge-youtube { background: rgba(239,68,68,0.2); color: #ff6b6b; border: 1px solid rgba(239,68,68,0.3); }
.badge-text { background: rgba(52,211,153,0.12); color: #34d399; border: 1px solid rgba(52,211,153,0.2); }

/* ── Answer Box ── */
.answer-box {
    background: linear-gradient(135deg, #13131a, #15152a);
    border: 1px solid #2a2a42;
    border-left: 3px solid #818cf8;
    border-radius: 0 12px 12px 0;
    padding: 1.5rem 1.8rem;
    margin: 1rem 0;
    line-height: 1.8;
    font-size: 0.97rem;
}

/* ── Source Ref ── */
.source-ref {
    background: #0e0e13;
    border: 1px solid #1f1f2e;
    border-radius: 10px;
    padding: 0.9rem 1.2rem;
    margin-bottom: 0.6rem;
    font-size: 0.85rem;
}
.source-ref .excerpt {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #6b6b8a;
    margin-top: 0.4rem;
    line-height: 1.5;
}
.score-bar {
    height: 3px;
    border-radius: 2px;
    background: linear-gradient(90deg, #818cf8, #6366f1);
    margin-top: 6px;
}

/* ── Quiz Cards ── */
.quiz-q {
    background: #13131a;
    border: 1px solid #1f1f2e;
    border-radius: 12px;
    padding: 1.3rem 1.5rem;
    margin-bottom: 1.2rem;
}
.quiz-q .q-num {
    font-size: 0.72rem;
    color: #818cf8;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.quiz-q .q-text {
    font-size: 1rem;
    color: #d4d2e8;
    font-weight: 500;
    margin: 0.4rem 0 0.8rem 0;
}
.result-correct {
    background: rgba(52,211,153,0.08);
    border: 1px solid rgba(52,211,153,0.25);
    border-radius: 8px;
    padding: 0.6rem 1rem;
    color: #34d399;
    font-size: 0.88rem;
    margin-top: 0.5rem;
}
.result-wrong {
    background: rgba(248,113,113,0.08);
    border: 1px solid rgba(248,113,113,0.25);
    border-radius: 8px;
    padding: 0.6rem 1rem;
    color: #f87171;
    font-size: 0.88rem;
    margin-top: 0.5rem;
}

/* ── Score Ring ── */
.score-display {
    text-align: center;
    padding: 2rem;
    background: #13131a;
    border: 1px solid #1f1f2e;
    border-radius: 16px;
    margin: 1.5rem 0;
}
.score-display .big-score {
    font-family: 'DM Serif Display', serif;
    font-size: 4rem;
    color: #818cf8;
    line-height: 1;
}
.score-display .score-label { color: #6b6b8a; font-size: 0.9rem; margin-top: 0.3rem; }

/* ── Metrics Row ── */
.metric-row { display: flex; gap: 1rem; margin: 1rem 0; }
.metric-box {
    flex: 1;
    background: #13131a;
    border: 1px solid #1f1f2e;
    border-radius: 10px;
    padding: 0.9rem 1rem;
    text-align: center;
}
.metric-box .val {
    font-family: 'DM Serif Display', serif;
    font-size: 1.6rem;
    color: #818cf8;
}
.metric-box .lbl { font-size: 0.72rem; color: #6b6b8a; margin-top: 2px; }

/* ── Streamlit overrides ── */
div[data-testid="stTabs"] button {
    color: #8b8aa0 !important;
    font-weight: 500;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #818cf8 !important;
    border-bottom: 2px solid #818cf8 !important;
}
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #4f46e5);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 500;
    font-family: 'DM Sans', sans-serif;
    padding: 0.5rem 1.5rem;
    transition: opacity 0.2s;
    width: 100%;
}
.stButton > button:hover { opacity: 0.88; }
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #13131a !important;
    border: 1px solid #2a2a42 !important;
    color: #e8e6df !important;
    border-radius: 8px !important;
}
.stSelectbox > div > div {
    background: #13131a !important;
    border: 1px solid #2a2a42 !important;
    color: #e8e6df !important;
}
.stFileUploader {
    background: #13131a;
    border: 2px dashed #2a2a42;
    border-radius: 10px;
    padding: 1rem;
}
div[data-testid="stExpander"] {
    background: #13131a;
    border: 1px solid #1f1f2e;
    border-radius: 10px;
}
.stAlert { border-radius: 10px; }
.stSpinner > div { border-top-color: #818cf8 !important; }
hr { border-color: #1f1f2e; }

/* ── Study Plan ── */
.plan-day {
    background: #13131a;
    border: 1px solid #1f1f2e;
    border-left: 3px solid #818cf8;
    border-radius: 0 10px 10px 0;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
}

/* ── History row ── */
.hist-row {
    background: #13131a;
    border: 1px solid #1f1f2e;
    border-radius: 10px;
    padding: 0.9rem 1.2rem;
    margin-bottom: 0.5rem;
    cursor: pointer;
}
.hist-row:hover { border-color: #3d3d5c; }
.hist-type {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #6b6b8a;
}

/* ── Scrollable container ── */
.scroll-box {
    max-height: 420px;
    overflow-y: auto;
    padding-right: 0.5rem;
}

/* ── Latency pill ── */
.latency-pill {
    display: inline-block;
    background: rgba(129,140,248,0.1);
    border: 1px solid rgba(129,140,248,0.2);
    color: #818cf8;
    font-size: 0.72rem;
    padding: 2px 10px;
    border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# API Helpers
# ═══════════════════════════════════════════════

def api_post(endpoint: str, data: dict = None, files: dict = None, timeout: int = 120) -> dict:
    """POST to backend, return {success, data} or {success, error}."""
    try:
        url = f"{BACKEND_URL}{endpoint}"
        if files:
            resp = requests.post(url, data=data or {}, files=files, timeout=timeout)
        else:
            resp = requests.post(url, json=data or {}, timeout=timeout)

        if resp.status_code == 200:
            return {"success": True, "data": resp.json()}

        try:
            detail = resp.json().get("detail", f"HTTP {resp.status_code}")
        except Exception:
            detail = f"HTTP {resp.status_code}"
        return {"success": False, "error": detail}

    except requests.ConnectionError:
        return {
            "success": False,
            "error": "❌ Cannot connect to backend. Make sure it's running:\n`python -m backend.main`",
        }
    except requests.Timeout:
        return {"success": False, "error": "Request timed out. Large files may take longer."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def api_get(endpoint: str, params: dict = None, timeout: int = 30) -> dict:
    try:
        resp = requests.get(f"{BACKEND_URL}{endpoint}", params=params or {}, timeout=timeout)
        if resp.status_code == 200:
            return {"success": True, "data": resp.json()}
        else:
            return {"success": False, "error": resp.text}
    except Exception as e:
        return {"success": False, "error": str(e)}
        try:
            detail = resp.json().get("detail", f"HTTP {resp.status_code}")
        except Exception:
            detail = f"HTTP {resp.status_code}"
        return {"success": False, "error": detail}
    except requests.ConnectionError:
        return {"success": False, "error": "Backend offline"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@st.cache_data(ttl=10)
def fetch_documents() -> list:
    """Fetch document list (cached 10s)."""
    result = api_get("/documents", {"user_id": 1})
    return result["data"] if result["success"] else []


@st.cache_data(ttl=30)
def fetch_health() -> dict:
    """Fetch backend health (cached 30s)."""
    result = api_get("/health")
    return result["data"] if result["success"] else {}


def build_doc_selector(docs: list, label: str = "Select Document") -> Optional[int]:
    """Render a document selectbox and return the selected doc ID."""
    if not docs:
        st.warning("No documents found. Upload content first → **📤 Upload Content**")
        return None
    options = {f"{d['title']}  [{d['source_type'].upper()}]": d["id"] for d in docs}
    selected = st.selectbox(label, list(options.keys()))
    return options[selected]


def badge(source_type: str) -> str:
    cls = f"badge-{source_type}"
    icons = {"pdf": "📄", "youtube": "▶", "text": "📝"}
    label = {"pdf": "PDF", "youtube": "YouTube", "text": "Text"}
    return f'<span class="badge {cls}">{icons.get(source_type,"")} {label.get(source_type, source_type.upper())}</span>'


def metric_html(value, label: str) -> str:
    return f"""<div class="metric-box"><div class="val">{value}</div><div class="lbl">{label}</div></div>"""


# ═══════════════════════════════════════════════
# Sidebar
# ═══════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="padding:1rem 0 0.5rem 0;">
        <span style="font-family:'DM Serif Display',serif; font-size:1.4rem; color:#f0ede6;">
            🎓 StudyMate <span style="color:#818cf8; font-style:italic;">AI</span>
        </span>
        <div style="font-size:0.75rem; color:#4b4b6a; margin-top:2px;">v1.0.0 · Your Learning Companion</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Navigation
    st.markdown('<div class="nav-label">Navigation</div>', unsafe_allow_html=True)

    nav_options = {
        "📤  Upload Content": "upload",
        "💬  Ask Questions": "qa",
        "📋  Summarize": "summarize",
        "🧪  Quiz Me": "quiz",
        "📅  Study Plan": "study_plan",
        "🔊  Text-to-Speech": "tts",
        "📜  Query History": "history",
        "📊  Dashboard": "dashboard",
    }

    page_label = st.radio(
        "nav",
        list(nav_options.keys()),
        label_visibility="collapsed",
    )
    page = nav_options[page_label]

    st.divider()

    # ── Backend Status
    st.markdown('<div class="nav-label">System Status</div>', unsafe_allow_html=True)

    fetch_health.clear()        # ← add this line
    fetch_documents.clear()
    health = fetch_health()
    if health:
        st.markdown('<span class="status-chip chip-online">🟢 Backend Online</span>', unsafe_allow_html=True)

        openai_ok = health.get("groq_configured", False)
        if openai_ok:
            st.markdown('<span class="status-chip chip-online">✓ Groq AI Ready</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-chip chip-warn">⚠ Groq Key Not Set</span>', unsafe_allow_html=True)
            st.caption("Add GROQ_API_KEY to .env")

        vec_count = health.get("vector_store_docs", 0)
        st.markdown(f'<span class="status-chip chip-online">📦 {vec_count:,} vectors</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-chip chip-offline">🔴 Backend Offline</span>', unsafe_allow_html=True)
        st.caption("Run: `python -m backend.main`")

    st.divider()

    # ── Quick doc count
    docs_sidebar = fetch_documents()
    st.markdown(f'<div class="nav-label">Library: {len(docs_sidebar)} document(s)</div>', unsafe_allow_html=True)

    for d in docs_sidebar[:5]:
        st.markdown(
            f'{badge(d["source_type"])} <span style="font-size:0.8rem;color:#a0a0c0;">{d["title"][:30]}{"…" if len(d["title"])>30 else ""}</span>',
            unsafe_allow_html=True,
        )
    if len(docs_sidebar) > 5:
        st.caption(f"...and {len(docs_sidebar)-5} more")

    st.divider()
    st.caption("Built with FastAPI · FAISS · sentence-transformers · Groq · gTTS")


# ═══════════════════════════════════════════════
# Hero Header
# ═══════════════════════════════════════════════

st.markdown("""
<div class="hero">
    <h1>Study<span>Mate</span> AI</h1>
    <p>Upload PDFs · YouTube videos · Text notes → Ask questions · Summarize · Quiz yourself · Listen</p>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# PAGE: UPLOAD CONTENT
# ═══════════════════════════════════════════════════════════════════

if page == "upload":
    st.markdown("## 📤 Upload Study Materials")
    st.caption("Add content to your knowledge base. All sources are chunked, embedded, and indexed for RAG retrieval.")

    tab_pdf, tab_yt, tab_txt = st.tabs(["📄  PDF Document", "▶  YouTube Video", "📝  Text / Notes"])

    # ── PDF ──────────────────────────────────────
    with tab_pdf:
        st.markdown("#### Upload a PDF")
        st.caption("Supports text-based PDFs. Scanned/image PDFs are not supported.")

        uploaded = st.file_uploader(
            "Drop your PDF here",
            type=["pdf"],
            help="Max 50MB. Text-based PDFs only.",
        )

        if uploaded:
            size_kb = len(uploaded.getvalue()) / 1024
            st.markdown(f"""
            <div class="card">
                <div class="card-title">{uploaded.name}</div>
                <div style="color:#6b6b8a; font-size:0.85rem;">{size_kb:.1f} KB · PDF</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🚀  Process & Index PDF", key="pdf_go"):
                with st.spinner("Extracting text · Chunking · Generating embeddings…"):
                    t0 = time.time()
                    result = api_post(
                        "/upload/pdf",
                        data={"user_id": "1"},
                        files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
                        timeout=180,
                    )
                elapsed = int((time.time() - t0) * 1000)

                if result["success"]:
                    d = result["data"]
                    st.success(f"✅ Successfully indexed **{d['title']}**")
                    st.markdown(f"""
                    <div class="metric-row">
                        {metric_html(d['num_chunks'], 'Chunks Created')}
                        {metric_html(f"{d['word_count']:,}", 'Words Extracted')}
                        {metric_html(d['document_id'], 'Document ID')}
                        {metric_html(f"{elapsed}ms", 'Processing Time')}
                    </div>
                    """, unsafe_allow_html=True)
                    st.cache_data.clear()
                else:
                    st.error(f"**Upload failed:** {result['error']}")

    # ── YouTube ───────────────────────────────────
    with tab_yt:
        st.markdown("#### Add a YouTube Video")
        st.caption("Fetches transcript automatically. Falls back to Whisper if no captions available.")

        yt_url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        )
        yt_title_override = st.text_input("Custom title (optional — auto-detected if blank)")

        col_a, col_b = st.columns([1, 3])
        with col_a:
            use_mmr = st.checkbox("Use MMR retrieval", value=True, help="Maximal Marginal Relevance — reduces redundant chunks")

        if st.button("▶  Fetch Transcript & Index", key="yt_go"):
            if not yt_url.strip():
                st.error("Please enter a YouTube URL.")
            elif "youtube.com" not in yt_url and "youtu.be" not in yt_url:
                st.error("That doesn't look like a valid YouTube URL.")
            else:
                with st.spinner("Fetching transcript… (may take up to 60s for long videos)"):
                    t0 = time.time()
                    result = api_post("/upload/youtube", {
                        "url": yt_url.strip(),
                        "title": yt_title_override.strip() or None,
                        "user_id": 1,
                    }, timeout=180)
                elapsed = int((time.time() - t0) * 1000)

                if result["success"]:
                    d = result["data"]
                    st.success(f"✅ Indexed **{d['title']}**")
                    st.markdown(f"""
                    <div class="metric-row">
                        {metric_html(d['num_chunks'], 'Chunks')}
                        {metric_html(f"{d['word_count']:,}", 'Words')}
                        {metric_html(d['document_id'], 'Doc ID')}
                        {metric_html(f"{elapsed}ms", 'Time')}
                    </div>
                    """, unsafe_allow_html=True)
                    st.cache_data.clear()
                else:
                    st.error(f"**Failed:** {result['error']}")
                    with st.expander("Troubleshooting tips"):
                        st.markdown("""
                        - Make sure the video has **English captions** (auto-generated is fine)
                        - Age-restricted or private videos cannot be accessed
                        - Very new videos may not have transcripts yet
                        - Try a shorter video first to verify setup
                        """)

    # ── Text ─────────────────────────────────────
    with tab_txt:
        st.markdown("#### Add Text / Notes")
        st.caption("Paste lecture notes, book excerpts, articles, or any plain text.")

        txt_title = st.text_input("Title *", placeholder="Introduction to Machine Learning — Chapter 3")
        txt_content = st.text_area(
            "Content *",
            height=280,
            placeholder="Paste your text, notes, or any content here…\n\nThe system will chunk and index it for Q&A and summarization.",
        )

        word_count_live = len(txt_content.split()) if txt_content.strip() else 0
        st.caption(f"Word count: {word_count_live:,}")

        if st.button("📝  Index Notes", key="txt_go"):
            if not txt_title.strip():
                st.error("Please provide a title.")
            elif word_count_live < 20:
                st.error("Content is too short. Please provide at least 20 words.")
            else:
                with st.spinner("Chunking and embedding your notes…"):
                    result = api_post("/upload/text", {
                        "title": txt_title.strip(),
                        "content": txt_content.strip(),
                        "user_id": 1,
                    })

                if result["success"]:
                    d = result["data"]
                    st.success(f"✅ Indexed **{d['title']}**")
                    st.markdown(f"""
                    <div class="metric-row">
                        {metric_html(d['num_chunks'], 'Chunks')}
                        {metric_html(f"{d['word_count']:,}", 'Words')}
                        {metric_html(d['document_id'], 'Doc ID')}
                    </div>
                    """, unsafe_allow_html=True)
                    st.cache_data.clear()
                else:
                    st.error(f"**Failed:** {result['error']}")

    # ── Knowledge Base Overview ───────────────────
    st.divider()
    st.markdown("### 📚 Your Knowledge Base")

    docs = fetch_documents()
    if not docs:
        st.markdown("""
        <div class="card" style="text-align:center; padding:2.5rem;">
            <div style="font-size:2rem; margin-bottom:0.5rem;">📭</div>
            <div style="color:#6b6b8a;">No documents yet. Use the tabs above to add content.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for doc in docs:
            with st.expander(
                f"{doc['title']}",
                expanded=False,
            ):
                st.markdown(
                    f"{badge(doc['source_type'])} &nbsp; Document ID: **{doc['id']}**",
                    unsafe_allow_html=True,
                )
                st.markdown(f"""
                <div class="metric-row">
                    {metric_html(doc['num_chunks'], 'Chunks')}
                    {metric_html(f"{doc['word_count']:,}", 'Words')}
                    {metric_html('✓' if doc['is_indexed'] else '✗', 'Indexed')}
                </div>
                """, unsafe_allow_html=True)
                st.caption(f"Added: {doc['created_at'][:10] if doc['created_at'] else 'N/A'}")


# ═══════════════════════════════════════════════════════════════════
# PAGE: Q&A
# ═══════════════════════════════════════════════════════════════════

elif page == "qa":
    st.markdown("## 💬 Ask Questions")
    st.caption("Retrieval-Augmented Generation — your question is matched to the most relevant content chunks, then answered by the LLM.")

    docs = fetch_documents()

    col_q, col_opts = st.columns([3, 2])

    with col_q:
        question = st.text_input(
            "Your question",
            placeholder="What are the key differences between supervised and unsupervised learning?",
        )

    with col_opts:
        scope_options = {"🌐 All Documents": None}
        for d in docs:
            scope_options[f"{d['title'][:35]}… [{d['source_type'].upper()}]" if len(d['title'])>35 else f"{d['title']} [{d['source_type'].upper()}]"] = d["id"]

        selected_scope_label = st.selectbox("Search scope", list(scope_options.keys()))
        selected_doc_id = scope_options[selected_scope_label]

    top_k = st.slider("Number of context chunks to retrieve", 2, 10, 5, help="More chunks = more context but slower")

    if st.button("🔍  Get Answer", key="qa_go"):
        if not question.strip():
            st.error("Please enter a question.")
        elif not docs:
            st.warning("No documents in your library yet. Upload something first!")
        else:
            with st.spinner("Retrieving relevant chunks · Generating answer…"):
                t0 = time.time()
                result = api_post("/query", {
                    "question": question.strip(),
                    "document_id": selected_doc_id,
                    "user_id": 1,
                    "top_k": top_k,
                })

            if result["success"]:
                data = result["data"]

                st.markdown(f"""
                <div class="answer-box">
                    {data['answer'].replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)

                st.markdown(
                    f'<span class="latency-pill">⏱ {data["latency_ms"]}ms</span>',
                    unsafe_allow_html=True,
                )

                # Sources
                if data.get("sources"):
                    st.markdown(f"#### 📎 {len(data['sources'])} Source References")
                    for i, src in enumerate(data["sources"], 1):
                        score_pct = min(100, int(src["relevance_score"] * 100))
                        st.markdown(f"""
                        <div class="source-ref">
                            <strong>{i}. {src['document_title']}</strong>
                            {badge(src['source_type'])}
                            <span style="color:#6b6b8a; font-size:0.78rem;">Chunk #{src['chunk_index']} · Score: {src['relevance_score']:.3f}</span>
                            <div class="score-bar" style="width:{score_pct}%;"></div>
                            <div class="excerpt">{src['excerpt'][:250]}{"…" if len(src['excerpt'])>250 else ""}</div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.error(f"**Error:** {result['error']}")

    # ── ELI5 Concept Explainer (bonus feature)
    st.divider()
    st.markdown("#### 🧠 ELI5 Concept Explainer")
    st.caption("Paste a concept from your materials and get a simple, analogy-driven explanation.")

    concept_input = st.text_input("Concept to explain", placeholder="e.g. gradient descent, entropy, backpropagation")
    context_input = st.text_area("Paste relevant context (optional)", height=100, placeholder="Paste a paragraph from your study material for more accurate explanation…")

    if st.button("💡 Explain Simply", key="eli5_go"):
        if not concept_input.strip():
            st.error("Please enter a concept.")
        else:
            with st.spinner("Crafting a simple explanation…"):
                result = api_post("/query", {
                    "question": f"Explain {concept_input} in simple terms with an analogy. Use this context: {context_input}",
                    "user_id": 1,
                    "top_k": 3,
                })
            if result["success"]:
                st.markdown(f"""
                <div class="answer-box">
                    <strong>💡 {concept_input}</strong><br><br>
                    {result['data']['answer'].replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error(result["error"])


# ═══════════════════════════════════════════════════════════════════
# PAGE: SUMMARIZE
# ═══════════════════════════════════════════════════════════════════

elif page == "summarize":
    st.markdown("## 📋 Document Summarizer")
    st.caption("Generate concise, structured summaries of any indexed document using AI.")

    docs = fetch_documents()
    doc_id = build_doc_selector(docs)

    if doc_id:
        style_col, btn_col = st.columns([2, 1])

        with style_col:
            style = st.radio(
                "Summary style",
                ["bullets", "short", "detailed"],
                horizontal=True,
                captions=[
                    "Key bullet points",
                    "2–3 sentence overview",
                    "Full structured breakdown",
                ],
            )

        if st.button("✨  Generate Summary", key="sum_go"):
            with st.spinner(f"Generating {style} summary with AI…"):
                t0 = time.time()
                result = api_post("/summarize", {
                    "document_id": doc_id,
                    "style": style,
                    "user_id": 1,
                })
                elapsed = int((time.time() - t0) * 1000)

            if result["success"]:
                data = result["data"]

                # Store summary in session for TTS
                st.session_state["last_summary"] = data["summary"]
                st.session_state["last_summary_doc_id"] = doc_id

                st.markdown(f"""
                <div style="display:flex; align-items:center; gap:0.8rem; margin-bottom:1rem;">
                    <span style="font-family:'DM Serif Display',serif; font-size:1.3rem; color:#d4d2e8;">{data['title']}</span>
                    {badge(next((d['source_type'] for d in docs if d['id']==doc_id), 'text'))}
                    <span class="latency-pill">{elapsed}ms</span>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(data["summary"])

                st.markdown(f"""
                <div class="metric-row">
                    {metric_html(data['word_count'], 'Summary Words')}
                    {metric_html(style.capitalize(), 'Style')}
                </div>
                """, unsafe_allow_html=True)

            else:
                st.error(f"**Error:** {result['error']}")

        # ── TTS for summary
        if "last_summary" in st.session_state and st.session_state.get("last_summary_doc_id") == doc_id:
            st.divider()
            st.markdown("#### 🔊 Listen to Summary")

            tts_lang = st.selectbox(
                "Language",
                ["en", "hi", "fr", "de", "es", "pt", "ja", "zh"],
                format_func=lambda x: {
                    "en": "🇬🇧 English", "hi": "🇮🇳 Hindi", "fr": "🇫🇷 French",
                    "de": "🇩🇪 German", "es": "🇪🇸 Spanish", "pt": "🇵🇹 Portuguese",
                    "ja": "🇯🇵 Japanese", "zh": "🇨🇳 Chinese",
                }.get(x, x),
            )

            if st.button("🎙️  Generate Audio", key="sum_tts"):
                with st.spinner("Converting summary to speech…"):
                    tts_result = api_post("/tts", {
                        "text": st.session_state["last_summary"],
                        "language": tts_lang,
                        "document_id": doc_id,
                    })
                if tts_result["success"]:
                    audio_url = BACKEND_URL + tts_result["data"]["audio_url"]
                    st.audio(audio_url, format="audio/mp3")
                    st.success("Audio ready! Press play above.")
                else:
                    st.error(f"TTS error: {tts_result['error']}")


# ═══════════════════════════════════════════════════════════════════
# PAGE: QUIZ
# ═══════════════════════════════════════════════════════════════════

elif page == "quiz":
    st.markdown("## 🧪 Quiz Generator")
    st.caption("Test your understanding with AI-generated multiple choice questions.")

    docs = fetch_documents()
    doc_id = build_doc_selector(docs)

    if doc_id:
        col1, col2, col3 = st.columns(3)
        num_q = col1.slider("Questions", 3, 10, 5)
        difficulty = col2.select_slider("Difficulty", ["easy", "medium", "hard"], value="medium")
        col3.markdown("<br>", unsafe_allow_html=True)

        if st.button("🎯  Generate Quiz", key="quiz_go"):
            with st.spinner(f"Crafting {num_q} {difficulty} questions…"):
                result = api_post("/quiz", {
                    "document_id": doc_id,
                    "num_questions": num_q,
                    "difficulty": difficulty,
                    "user_id": 1,
                })

            if result["success"]:
                data = result["data"]
                st.session_state["quiz_data"] = data
                st.session_state["quiz_answers"] = {}
                st.session_state["quiz_submitted"] = False
                st.session_state["quiz_doc_id"] = doc_id
            else:
                st.error(f"**Error:** {result['error']}")
                st.info("Make sure your GROQ_API_KEY is set in `.env`")

        # ── Render Quiz
        if st.session_state.get("quiz_data") and st.session_state.get("quiz_doc_id") == doc_id:
            data = st.session_state["quiz_data"]
            submitted = st.session_state.get("quiz_submitted", False)

            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:0.8rem; margin:1rem 0;">
                <span style="font-family:'DM Serif Display',serif; font-size:1.2rem;">📝 {data['title']}</span>
                <span class="badge badge-pdf">{data['num_questions']} Questions</span>
                <span class="badge badge-text">{difficulty.capitalize()}</span>
            </div>
            """, unsafe_allow_html=True)

            for q in data["questions"]:
                qn = q["question_number"]
                user_ans = st.session_state["quiz_answers"].get(qn)
                correct = q["correct_answer"]

                option_texts = [f"{opt['label']}.  {opt['text']}" for opt in q["options"]]

                st.markdown(f"""
                <div class="quiz-q">
                    <div class="q-num">Question {qn} of {data['num_questions']}</div>
                    <div class="q-text">{q['question']}</div>
                </div>
                """, unsafe_allow_html=True)

                default_idx = None
                if user_ans:
                    for i, opt in enumerate(option_texts):
                        if opt.startswith(user_ans):
                            default_idx = i
                            break

                if not submitted:
                    choice = st.radio(
                        f"q{qn}",
                        option_texts,
                        index=default_idx,
                        key=f"radio_{qn}",
                        label_visibility="collapsed",
                    )
                    if choice:
                        st.session_state["quiz_answers"][qn] = choice[0]
                else:
                    # Show results
                    for opt_text in option_texts:
                        opt_label = opt_text[0]
                        is_correct_opt = opt_label == correct
                        is_user_choice = opt_label == user_ans

                        if is_correct_opt:
                            st.markdown(f"✅ **{opt_text}**")
                        elif is_user_choice and not is_correct_opt:
                            st.markdown(f"❌ ~~{opt_text}~~")
                        else:
                            st.markdown(f"&nbsp;&nbsp;&nbsp;{opt_text}")

                    verdict = user_ans == correct
                    if verdict:
                        st.markdown('<div class="result-correct">✓ Correct!</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="result-wrong">✗ Correct answer: <strong>{correct}</strong></div>', unsafe_allow_html=True)

                    with st.expander("📖 Explanation"):
                        st.write(q.get("explanation", "No explanation provided."))

                st.markdown("<br>", unsafe_allow_html=True)

            if not submitted:
                if st.button("✅  Submit Quiz", key="quiz_submit"):
                    st.session_state["quiz_submitted"] = True
                    st.rerun()
            else:
                # ── Score Report
                questions = data["questions"]
                score = sum(
                    1 for q in questions
                    if st.session_state["quiz_answers"].get(q["question_number"]) == q["correct_answer"]
                )
                pct = int(score / len(questions) * 100)

                emoji = "🎉" if pct >= 80 else "👍" if pct >= 60 else "📚"
                msg = "Excellent mastery!" if pct >= 80 else "Good effort — review missed topics." if pct >= 60 else "Keep studying — you'll get there!"

                st.markdown(f"""
                <div class="score-display">
                    <div class="big-score">{pct}%</div>
                    <div style="font-size:1.1rem; color:#c8c6d9; margin-top:0.3rem;">{emoji} {score}/{len(questions)} correct</div>
                    <div class="score-label">{msg}</div>
                </div>
                """, unsafe_allow_html=True)

                if pct >= 80:
                    st.balloons()

                if st.button("🔄  Retake Quiz", key="retake"):
                    st.session_state.pop("quiz_data", None)
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════
# PAGE: STUDY PLAN  ⭐ My Addition
# ═══════════════════════════════════════════════════════════════════

elif page == "study_plan":
    st.markdown("## 📅 AI Study Plan Generator")
    st.markdown("""
    <div class="card">
        <div style="font-size:0.9rem; color:#8b8aa0; line-height:1.7;">
            ⭐ <strong style="color:#818cf8;">Unique Feature</strong> — StudyMate AI analyzes your document and generates a 
            personalized <strong>3-day study plan</strong> with daily goals, focus areas, review strategies, and self-testing tips. 
            Great for exam preparation.
        </div>
    </div>
    """, unsafe_allow_html=True)

    docs = fetch_documents()
    doc_id = build_doc_selector(docs)

    if doc_id:
        selected_doc = next((d for d in docs if d["id"] == doc_id), None)

        col_a, col_b = st.columns(2)
        with col_a:
            exam_date = st.date_input("Exam/deadline date (optional)")
        with col_b:
            daily_hours = st.slider("Daily study hours available", 1, 8, 2)

        if st.button("🗓️  Generate My Study Plan", key="plan_go"):
            with st.spinner("Analyzing content · Building personalized plan…"):
                result = api_get("/study-plan", {"document_id": doc_id, "user_id": 1})

            if result["success"]:
                data = result["data"]

                st.markdown(f"""
                <div style="font-family:'DM Serif Display',serif; font-size:1.4rem; color:#d4d2e8; margin-bottom:1rem;">
                    📅 Study Plan: {data['title']}
                </div>
                """, unsafe_allow_html=True)

                plan_text = data.get("study_plan", "")
                st.markdown(plan_text)

                # TTS option for the plan
                st.divider()
                if st.button("🔊 Listen to Study Plan"):
                    with st.spinner("Generating audio…"):
                        tts_result = api_post("/tts", {
                            "text": plan_text[:3000],
                            "language": "en",
                        })
                    if tts_result["success"]:
                        audio_url = BACKEND_URL + tts_result["data"]["audio_url"]
                        st.audio(audio_url, format="audio/mp3")
            else:
                st.error(f"**Error:** {result.get('error', 'Unknown error')}")
                st.info("Make sure your GROQ_API_KEY is configured in `.env`")


# ═══════════════════════════════════════════════════════════════════
# PAGE: TEXT-TO-SPEECH
# ═══════════════════════════════════════════════════════════════════

elif page == "tts":
    st.markdown("## 🔊 Text-to-Speech")
    st.caption("Convert any text to speech. Useful for listening to summaries while commuting or exercising.")

    lang_map = {
        "🇬🇧 English": "en",
        "🇮🇳 Hindi": "hi",
        "🇫🇷 French": "fr",
        "🇩🇪 German": "de",
        "🇪🇸 Spanish": "es",
        "🇵🇹 Portuguese": "pt",
        "🇯🇵 Japanese": "ja",
        "🇨🇳 Chinese (Mandarin)": "zh",
        "🇰🇷 Korean": "ko",
        "🇮🇹 Italian": "it",
        "🇷🇺 Russian": "ru",
        "🇸🇦 Arabic": "ar",
    }

    tts_text = st.text_area(
        "Text to convert",
        height=220,
        placeholder="Paste any text here — a summary, a paragraph from your notes, or anything you want to hear read aloud…",
        max_chars=5000,
    )

    char_count = len(tts_text)
    st.caption(f"{char_count}/5000 characters")

    col1, col2 = st.columns(2)
    with col1:
        lang_label = st.selectbox("Language", list(lang_map.keys()))
        lang_code = lang_map[lang_label]
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info(f"Selected: `{lang_code}` · ~{char_count//5} seconds of audio")

    if st.button("🎙️  Generate Audio", key="tts_go"):
        if not tts_text.strip():
            st.error("Please enter some text.")
        elif char_count < 10:
            st.error("Text is too short — enter at least 10 characters.")
        else:
            with st.spinner("Generating audio with gTTS…"):
                result = api_post("/tts", {
                    "text": tts_text.strip(),
                    "language": lang_code,
                })

            if result["success"]:
                audio_url = BACKEND_URL + result["data"]["audio_url"]
                st.markdown("#### 🎵 Audio Ready")
                st.audio(audio_url, format="audio/mp3")
                st.success("✅ Audio generated! Press play above.")
                st.caption(f"File: `{result['data']['audio_file_path'].split('/')[-1]}`")
            else:
                st.error(f"**TTS Error:** {result['error']}")
                if "internet" in result["error"].lower() or "connect" in result["error"].lower():
                    st.warning("gTTS requires an internet connection to Google's API.")


# ═══════════════════════════════════════════════════════════════════
# PAGE: QUERY HISTORY
# ═══════════════════════════════════════════════════════════════════

elif page == "history":
    st.markdown("## 📜 Query History")
    st.caption("All your past questions, summaries, and quiz sessions.")

    result = api_get("/history", {"user_id": 1, "limit": 50})

    if result["success"] and result["data"]:
        history = result["data"]

        # Filter controls
        type_filter = st.multiselect(
            "Filter by type",
            ["qa", "summarize", "quiz"],
            default=["qa", "summarize", "quiz"],
        )

        filtered = [h for h in history if h["query_type"] in type_filter]

        st.caption(f"Showing {len(filtered)} of {len(history)} entries")

        type_icons = {"qa": "💬", "summarize": "📋", "quiz": "🧪"}

        for h in filtered:
            icon = type_icons.get(h["query_type"], "❓")
            query_preview = h["query_text"][:70] + "…" if len(h["query_text"]) > 70 else h["query_text"]

            with st.expander(f"{icon} {query_preview}"):
                col1, col2, col3 = st.columns(3)
                col1.markdown(f"**Type:** `{h['query_type']}`")
                if h.get("latency_ms"):
                    col2.markdown(f"**Time:** `{h['latency_ms']}ms`")
                col3.markdown(f"**Date:** {h['created_at'][:10] if h['created_at'] else 'N/A'}")

                if h.get("answer_text"):
                    st.divider()
                    st.markdown(h["answer_text"])
    else:
        st.markdown("""
        <div class="card" style="text-align:center; padding:2.5rem;">
            <div style="font-size:2rem; margin-bottom:0.5rem;">📭</div>
            <div style="color:#6b6b8a;">No history yet. Start asking questions!</div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════

elif page == "dashboard":
    st.markdown("## 📊 Dashboard")
    st.caption("Overview of your StudyMate AI knowledge base and usage.")

    # ── Stats row
    health = fetch_health()
    docs = fetch_documents()
    history_result = api_get("/history", {"user_id": 1, "limit": 100})
    history = history_result["data"] if history_result["success"] else []

    total_words = sum(d["word_count"] for d in docs)
    total_chunks = sum(d["num_chunks"] for d in docs)
    total_queries = len(history)
    avg_latency = int(sum(h["latency_ms"] for h in history if h.get("latency_ms")) / max(1, sum(1 for h in history if h.get("latency_ms"))))

    st.markdown(f"""
    <div class="metric-row">
        {metric_html(len(docs), 'Documents')}
        {metric_html(f"{total_words:,}", 'Total Words')}
        {metric_html(total_chunks, 'Vector Chunks')}
        {metric_html(total_queries, 'Queries Made')}
        {metric_html(f"{avg_latency}ms" if history else "—", 'Avg Latency')}
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Source breakdown
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 📚 Documents by Source")
        if docs:
            pdf_count = sum(1 for d in docs if d["source_type"] == "pdf")
            yt_count = sum(1 for d in docs if d["source_type"] == "youtube")
            txt_count = sum(1 for d in docs if d["source_type"] == "text")

            for label, count, color in [
                ("📄 PDF", pdf_count, "#f87171"),
                ("▶ YouTube", yt_count, "#ff6b6b"),
                ("📝 Text", txt_count, "#34d399"),
            ]:
                pct = count / max(len(docs), 1)
                st.markdown(f"""
                <div style="margin-bottom:0.7rem;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:3px;">
                        <span style="font-size:0.85rem;">{label}</span>
                        <span style="font-size:0.85rem; color:#6b6b8a;">{count}</span>
                    </div>
                    <div style="height:6px; background:#1f1f2e; border-radius:3px; overflow:hidden;">
                        <div style="height:100%; width:{pct*100:.0f}%; background:{color}; border-radius:3px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No documents yet.")

    with col_right:
        st.markdown("#### 🔍 Queries by Type")
        if history:
            qa_count = sum(1 for h in history if h["query_type"] == "qa")
            sum_count = sum(1 for h in history if h["query_type"] == "summarize")
            quiz_count = sum(1 for h in history if h["query_type"] == "quiz")

            for label, count, color in [
                ("💬 Q&A", qa_count, "#818cf8"),
                ("📋 Summarize", sum_count, "#34d399"),
                ("🧪 Quiz", quiz_count, "#fbbf24"),
            ]:
                pct = count / max(len(history), 1)
                st.markdown(f"""
                <div style="margin-bottom:0.7rem;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:3px;">
                        <span style="font-size:0.85rem;">{label}</span>
                        <span style="font-size:0.85rem; color:#6b6b8a;">{count}</span>
                    </div>
                    <div style="height:6px; background:#1f1f2e; border-radius:3px; overflow:hidden;">
                        <div style="height:100%; width:{pct*100:.0f}%; background:{color}; border-radius:3px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No queries yet.")

    # ── Recent documents
    st.divider()
    st.markdown("#### 📑 Recent Documents")
    if docs:
        for doc in docs[:8]:
            st.markdown(f"""
            <div class="hist-row">
                {badge(doc['source_type'])}
                <span style="font-size:0.9rem; color:#c8c6d9;">{doc['title']}</span>
                <span style="float:right; font-size:0.78rem; color:#4b4b6a;">{doc['num_chunks']} chunks · {doc['word_count']:,} words</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No documents uploaded yet.")

    # ── System info
    st.divider()
    st.markdown("#### ⚙️ System Information")
    sys_col1, sys_col2 = st.columns(2)
    with sys_col1:
        st.json({
            "backend_url": BACKEND_URL,
            "openai_configured": health.get("openai_configured", False),
            "db_connected": health.get("db_connected", False),
            "total_vectors": health.get("vector_store_docs", 0),
        })
    with sys_col2:
        st.json({
            "embedding_model": "all-MiniLM-L6-v2",
            "vector_db": "FAISS (IndexFlatIP)",
            "llm": "gpt-3.5-turbo",
            "tts_engine": "gTTS",
            "version": "1.0.0",
        })
