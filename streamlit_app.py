"""
MathViz Streamlit UI
====================
Run with:
    uv run streamlit run streamlit_app.py

Requires the FastAPI backend running on port 8000:
    uv run uvicorn main:app --port 8000
"""
import time
import requests
import streamlit as st

API_BASE    = "http://localhost:8000"
POLL_EVERY  = 5     # seconds between status polls
TIMEOUT_SHORT = 15  # seconds for /solve and /status calls
TIMEOUT_FILE  = 60  # seconds for video/solution downloads

# Stage display config  (stage key -> (progress 0-1, emoji, label))
_STAGES = {
    "starting":  (0.05, "⚙️",  "Starting the pipeline..."),
    "solving":   (0.20, "🧮",  "Solving the math problem..."),
    "writing":   (0.40, "📝",  "Writing step-by-step solution..."),
    "story":     (0.60, "🎬",  "Creating the animation story..."),
    "animation": (0.85, "🎨",  "Generating and rendering animation..."),
    "done":      (1.00, "✅",  "Animation ready!"),
    "error":     (0.00, "❌",  "Pipeline error"),
}

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MathViz — Math & Physics Animation",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title  { font-size: 2.2rem; font-weight: 700; color: #1a73e8; }
    .sub-caption { color: #666; font-size: 0.95rem; margin-top: -0.6rem; }
    .stage-box {
        background: #f0f7ff; border-left: 4px solid #1a73e8;
        padding: 0.7rem 1rem; border-radius: 0 8px 8px 0;
        font-size: 1.05rem; margin: 0.5rem 0;
    }
    .history-q    { font-weight: 600; font-size: 0.9rem; }
    .history-meta { color: #888; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar: history ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📚 Recent Animations")
    if st.button("Refresh", use_container_width=True):
        st.rerun()

    try:
        hist_resp = requests.get(f"{API_BASE}/history", timeout=10)
        rows = hist_resp.json().get("history", []) if hist_resp.ok else []
    except Exception:
        rows = []

    if not rows:
        st.caption("No history yet — submit a question to get started.")
    else:
        for row in rows:
            q_preview = (row.get("question") or "")[:70]
            created   = (row.get("created_at") or "")[:16].replace("T", " ")
            quality   = row.get("render_quality", "")
            with st.expander(f"🎬 {q_preview}", expanded=False):
                st.markdown(
                    f'<div class="history-meta">'
                    f'{created} &nbsp;·&nbsp; quality: <code>{quality}</code>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if row.get("video_filename"):
                    st.caption(f"Video: `{row['video_filename']}`")
                if row.get("solution_filename"):
                    st.caption(f"Solution: `{row['solution_filename']}`")


# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">🎓 MathViz</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-caption">Powered by Gemini 2.5 Pro · ADK · Manim</div>',
    unsafe_allow_html=True,
)
st.write("")

question = st.text_area(
    "Enter your math or physics question:",
    placeholder=(
        "e.g.  Solve x² − 5x + 6 = 0\n"
        "      Find the derivative of sin(x)·cos(x)\n"
        "      A ball is thrown upward at 20 m/s — how high does it go?"
    ),
    height=110,
    label_visibility="visible",
)

col_btn, col_hint = st.columns([1, 4])
with col_btn:
    submit = st.button(
        "Generate Animation 🎬",
        type="primary",
        disabled=not question.strip(),
        use_container_width=True,
    )
with col_hint:
    st.caption("Takes 3 – 8 minutes. Progress updates every 5 seconds.")

st.divider()


# ── Helper: render results ─────────────────────────────────────────────────────
def _show_results(job: dict) -> None:
    """Render tabs with video, solution, and agent response from a completed job."""
    session_id     = job.get("session_id", "")
    video_fname    = job.get("video_filename")
    solution_fname = job.get("solution_filename")
    agent_response = job.get("response", "")
    elapsed        = job.get("elapsed", 0)

    st.success(f"Done! Your animation is ready. (Total time: {elapsed}s)")

    tab_video, tab_solution, tab_response = st.tabs(
        ["🎬 Animation", "📄 Solution", "💬 Agent Response"]
    )

    with tab_video:
        if video_fname and session_id:
            with st.spinner("Loading video..."):
                try:
                    vr = requests.get(
                        f"{API_BASE}/video/{session_id}",
                        timeout=TIMEOUT_FILE,
                    )
                    if vr.ok:
                        st.video(vr.content)
                        st.caption(f"File: `{video_fname}`")
                    else:
                        st.warning("Video file not available from the server.")
                except Exception as e:
                    st.error(f"Could not load video: {e}")
        else:
            st.info("No video was produced for this question.")

    with tab_solution:
        if session_id:
            try:
                sr = requests.get(
                    f"{API_BASE}/solution_content/{session_id}",
                    timeout=TIMEOUT_FILE,
                )
                if sr.ok:
                    content = sr.json().get("content", "")
                    st.markdown(content)
                    if solution_fname:
                        st.caption(f"File: `{solution_fname}`")
                else:
                    st.info("Solution file not available.")
            except Exception as e:
                st.error(f"Could not load solution: {e}")
        else:
            st.info("No solution was saved for this question.")

    with tab_response:
        st.text_area(
            "Raw agent output",
            agent_response,
            height=350,
            label_visibility="collapsed",
        )


# ── Submit: kick off the background job ───────────────────────────────────────
if submit and question.strip():
    try:
        resp = requests.post(
            f"{API_BASE}/solve",
            json={"question": question.strip()},
            timeout=TIMEOUT_SHORT,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        st.error(f"Could not reach the backend: {exc}")
        st.stop()

    st.session_state["job_id"]     = data["job_id"]
    st.session_state["session_id"] = data["session_id"]
    st.session_state["job_done"]   = False
    st.session_state["job_result"] = None
    st.rerun()


# ── Polling loop: show progress or cached results ──────────────────────────────
job_id = st.session_state.get("job_id")

if job_id and not st.session_state.get("job_done"):
    # Poll the backend for current status
    try:
        sr = requests.get(f"{API_BASE}/status/{job_id}", timeout=TIMEOUT_SHORT)
        sr.raise_for_status()
        job = sr.json()
    except Exception as exc:
        st.error(f"Lost connection to backend: {exc}")
        st.stop()

    status = job.get("status", "processing")
    stage  = job.get("stage", "starting")
    label  = job.get("stage_label", "Processing...")
    elapsed = job.get("elapsed", 0)

    pct, emoji, _ = _STAGES.get(stage, (0.1, "⚙️", label))

    if status == "done":
        st.session_state["job_done"]   = True
        st.session_state["job_result"] = job
        _show_results(job)

    elif status == "error":
        st.error(f"Pipeline failed: {job.get('response', 'Unknown error')}")
        # Clear job so user can retry
        st.session_state.pop("job_id", None)
        st.session_state.pop("job_done", None)
        st.session_state.pop("job_result", None)

    else:
        # Still processing — show live progress
        st.markdown(
            f'<div class="stage-box">{emoji} &nbsp; <strong>{label}</strong>'
            f' &nbsp; <span style="color:#888">({elapsed}s elapsed)</span></div>',
            unsafe_allow_html=True,
        )
        st.progress(pct)
        st.caption(
            "The animation pipeline is running in the background. "
            "This page refreshes automatically every 5 seconds."
        )
        time.sleep(POLL_EVERY)
        st.rerun()

elif st.session_state.get("job_done") and st.session_state.get("job_result"):
    # Results already fetched — just display them (no extra network calls)
    _show_results(st.session_state["job_result"])
