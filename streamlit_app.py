"""
MathViz Streamlit UI
====================
Run with:
    uv run streamlit run streamlit_app.py

Requires the FastAPI backend running on port 8000:
    uv run uvicorn main:app --port 8000
"""
import os
import re
import time
import requests
import streamlit as st

API_BASE      = os.environ.get("MATHVIZ_API_BASE", "http://localhost:8000")
POLL_INTERVAL = 2     # seconds between in-place status polls
TIMEOUT_SHORT = 15    # seconds for /solve and /status calls
TIMEOUT_FILE  = 60    # seconds for video/solution downloads

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
    .question-preview {
        background: #e8f5e9; border-left: 4px solid #43a047;
        padding: 0.5rem 0.8rem; border-radius: 0 6px 6px 0;
        font-size: 0.95rem; margin: 0.4rem 0;
    }
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


# ── Image question extractor ──────────────────────────────────────────────────

def _extract_questions_from_image(image_bytes: bytes, mime_type: str) -> list[str]:
    """Call Gemini Vision to extract math/physics questions from an image."""
    prompt = (
        "Extract every math or physics question visible in this image. "
        "Return ONLY the question text(s), one per line, numbered if there are multiple. "
        "Do NOT include any solutions, explanations, or extra commentary."
    )
    try:
        import config as _cfg  # loads .env and sets GOOGLE_API_KEY / Vertex AI env vars  # noqa: F401

        import base64 as _b64
        from google import genai as _genai
        from google.genai import types as _types

        client = _genai.Client()
        b64data = _b64.b64encode(image_bytes).decode()
        contents = [
            _types.Content(parts=[
                _types.Part(inline_data=_types.Blob(data=b64data, mime_type=mime_type)),
                _types.Part(text=prompt),
            ])
        ]
        resp = client.models.generate_content(model="gemini-2.0-flash", contents=contents)
        raw_text = (resp.text or "").strip()

        if not raw_text:
            return ["[Could not extract text from image. Please type the question manually.]"]

        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        questions = []
        for line in lines:
            line = re.sub(r"^\d+[.)]\s*", "", line).strip()
            if line:
                questions.append(line)
        return questions if questions else [raw_text]
    except Exception as exc:
        return [f"[Error extracting questions: {exc}]"]


# ── Input area: tabs for text / image ─────────────────────────────────────────
tab_text, tab_image = st.tabs(["📝 Type Your Question", "🖼️ Upload Image"])

with tab_text:
    question_text = st.text_area(
        "Enter your math or physics question:",
        value=st.session_state.get("prefill_question", ""),
        placeholder=(
            "e.g.  Solve x² − 5x + 6 = 0\n"
            "      Find the derivative of sin(x)·cos(x)\n"
            "      In ΔABC, DE ∥ BC, AD/DB = 3/5, AC = 5.6 cm. Find AE."
        ),
        height=110,
        key="question_textarea",
    )

with tab_image:
    st.caption("Upload an image containing one or more math/physics questions.")
    uploaded_file = st.file_uploader(
        "Choose an image:",
        type=["png", "jpg", "jpeg", "gif", "webp"],
        key="image_uploader",
    )

    if uploaded_file is not None:
        col_img, col_ext = st.columns([1, 1])
        with col_img:
            st.image(uploaded_file, caption="Uploaded image", use_container_width=True)
        with col_ext:
            st.markdown("**Extract questions from this image:**")
            if st.button("🔍 Extract Questions", use_container_width=True):
                with st.spinner("Reading image with Gemini Vision..."):
                    extracted = _extract_questions_from_image(
                        uploaded_file.getvalue(), uploaded_file.type
                    )
                st.session_state["extracted_questions"] = extracted
                st.session_state["selected_img_question"] = extracted[0] if extracted else ""
                st.rerun()

    extracted_qs = st.session_state.get("extracted_questions", [])
    if extracted_qs:
        if extracted_qs[0].startswith("[Error"):
            st.error(extracted_qs[0])
        elif len(extracted_qs) == 1:
            st.markdown(
                f'<div class="question-preview">✅ Found: <strong>{extracted_qs[0]}</strong></div>',
                unsafe_allow_html=True,
            )
            st.session_state["selected_img_question"] = extracted_qs[0]
        else:
            st.markdown(f"**Found {len(extracted_qs)} questions — select one:**")
            selected = st.radio(
                "Select question to animate:",
                extracted_qs,
                key="img_q_radio",
                label_visibility="collapsed",
            )
            st.session_state["selected_img_question"] = selected
        if st.button("Use this question ↓", use_container_width=True, key="use_img_q"):
            st.session_state["prefill_question"] = st.session_state.get("selected_img_question", "")
            st.session_state.pop("extracted_questions", None)
            st.rerun()

# ── Generate button (works for both text and image tabs) ──────────────────────
st.write("")
col_btn, col_hint = st.columns([1, 3])
with col_btn:
    generate_clicked = st.button(
        "🎬 Generate Animation",
        type="primary",
        use_container_width=True,
    )
with col_hint:
    st.caption("Takes 2 – 5 minutes. Progress updates live — no page refresh.")

st.divider()


# ── Helper: render results ─────────────────────────────────────────────────────
def _show_results(job: dict) -> None:
    """Render tabs with video, solution, and agent response from a completed job."""
    session_id     = job.get("session_id", "")
    video_fname    = job.get("video_filename")
    solution_fname = job.get("solution_filename")
    agent_response = job.get("response", "")
    elapsed        = job.get("elapsed", 0)
    memory_log     = job.get("memory_log", [])

    st.success(f"Done! Your animation is ready. (Total time: {elapsed}s)")

    # Memory badge — shown inline next to the success banner when BigQuery was accessed
    if memory_log:
        bq_loads  = [e for e in memory_log if e.get("event") == "SESSION_LOADED_FROM_BQ"]
        bq_saves  = [e for e in memory_log if e.get("event") == "EVENT_SAVED_TO_BQ"]
        bq_new    = [e for e in memory_log if e.get("event") == "SESSION_CREATED"]
        parts = []
        if bq_new:
            parts.append(f"session created")
        if bq_loads:
            parts.append(f"{len(bq_loads)} session load{'s' if len(bq_loads)>1 else ''} from BQ")
        if bq_saves:
            parts.append(f"{len(bq_saves)} event{'s' if len(bq_saves)>1 else ''} saved to BQ")
        summary = " · ".join(parts)
        st.markdown(
            f'<div style="background:#1a3a2a;border-left:4px solid #34a853;padding:0.4rem 0.8rem;'
            f'border-radius:0 6px 6px 0;font-size:0.85rem;color:#81c995;margin-bottom:0.5rem;">'
            f'🧠 <strong>BigQuery Memory</strong> — {summary}</div>',
            unsafe_allow_html=True,
        )

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
            height=300,
            label_visibility="collapsed",
        )

        if memory_log:
            st.markdown("---")
            st.markdown("#### 🧠 BigQuery Memory Events")
            st.caption(
                "These events show when the agent read from or wrote to BigQuery "
                "for session persistence. SESSION_LOADED_FROM_BQ means prior context "
                "was recovered after a server restart."
            )
            import datetime as _dt
            for evt in memory_log:
                icon = {
                    "SESSION_CREATED":        "🆕",
                    "SESSION_LOADED_FROM_BQ": "📥",
                    "EVENT_SAVED_TO_BQ":      "💾",
                }.get(evt.get("event", ""), "🔵")
                ts = evt.get("ts", 0)
                ts_str = _dt.datetime.fromtimestamp(ts).strftime("%H:%M:%S") if ts else ""
                st.markdown(
                    f'<div style="font-family:monospace;font-size:0.82rem;'
                    f'padding:0.2rem 0.5rem;border-left:3px solid #34a853;'
                    f'margin-bottom:0.3rem;background:#0e1a14;color:#a8d5b5;">'
                    f'{icon} <strong>{evt.get("event","")}</strong> '
                    f'<span style="color:#6c9e7a">[{ts_str}]</span> — '
                    f'{evt.get("detail","")}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No BigQuery memory events for this run (in-memory session only).")


# ── Submit: collect question and kick off the background job ──────────────────
if generate_clicked:
    # Prefer text tab; fall back to image selection
    question = (
        st.session_state.get("question_textarea", "").strip()
        or st.session_state.get("selected_img_question", "").strip()
        or st.session_state.get("prefill_question", "").strip()
    )
    if not question:
        st.warning("Please enter a question or upload an image and extract a question first.")
        st.stop()
    try:
        resp = requests.post(
            f"{API_BASE}/solve",
            json={"question": question},
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
    # Clear image state after submitting
    st.session_state.pop("extracted_questions", None)
    st.session_state.pop("selected_img_question", None)
    st.session_state.pop("prefill_question", None)
    st.rerun()


# ── Live progress: poll backend every 2 s, update in place ───────────────────
job_id = st.session_state.get("job_id")

if job_id and not st.session_state.get("job_done"):
    stage_placeholder    = st.empty()
    progress_placeholder = st.empty()
    caption_placeholder  = st.empty()

    while True:
        try:
            sr = requests.get(f"{API_BASE}/status/{job_id}", timeout=TIMEOUT_SHORT)
            sr.raise_for_status()
            job = sr.json()
        except Exception as exc:
            stage_placeholder.error(f"Lost connection to backend: {exc}")
            break

        status  = job.get("status", "processing")
        stage   = job.get("stage", "starting")
        label   = job.get("stage_label", "Processing...")
        elapsed = job.get("elapsed", 0)
        pct, emoji, _ = _STAGES.get(stage, (0.1, "⚙️", label))

        if status == "done":
            st.session_state["job_done"]   = True
            st.session_state["job_result"] = job
            stage_placeholder.empty()
            progress_placeholder.empty()
            caption_placeholder.empty()
            st.rerun()
            break

        elif status == "error":
            stage_placeholder.error(
                f"Pipeline failed: {job.get('response', 'Unknown error')}"
            )
            progress_placeholder.empty()
            caption_placeholder.empty()
            st.session_state.pop("job_id",     None)
            st.session_state.pop("job_done",   None)
            st.session_state.pop("job_result", None)
            break

        else:
            stage_placeholder.markdown(
                f'<div class="stage-box">{emoji} &nbsp; <strong>{label}</strong>'
                f' &nbsp; <span style="color:#888">({elapsed}s elapsed)</span></div>',
                unsafe_allow_html=True,
            )
            progress_placeholder.progress(pct)
            caption_placeholder.caption(
                f"Stage: {stage} · {elapsed}s elapsed · "
                f"checking again in {POLL_INTERVAL}s"
            )
            time.sleep(POLL_INTERVAL)

elif st.session_state.get("job_done") and st.session_state.get("job_result"):
    _show_results(st.session_state["job_result"])
