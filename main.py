"""
MathViz — 2D Math Animation System
====================================
An agentic pipeline that:
  1. Solves any math question (algebra, geometry, calculus, statistics, …)
  2. Saves a step-by-step markdown solution
  3. Creates an engaging animation story
  4. Generates and renders a Manim 2D animation video

Usage (CLI):
    uv run python main.py "What is the derivative of x^2 + 3x?"

Usage (API server):
    uv run uvicorn main:app --reload --port 8000
    Then POST to http://localhost:8000/solve  {"question": "..."}
    Then GET  http://localhost:8000/status/{job_id}

Usage (ADK Web UI):
    adk web
"""
import asyncio
import concurrent.futures
import os
import random
import sys
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables (.env file must have GOOGLE_API_KEY or PROJECT_ID)
load_dotenv()

# Apply genai HTTP-level retry patch BEFORE any google.genai client is created.
import _retry_patch  # noqa: F401

# Configure Vertex AI credentials or API key authentication
import vertex_ai_config  # noqa: F401

from config import models, retry as retry_cfg, manim as manim_cfg, output as output_cfg, google_cloud

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# ADK imports
# ---------------------------------------------------------------------------
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

# ---------------------------------------------------------------------------
# Import the root agent (lazy import to avoid slow startup before env is set)
# ---------------------------------------------------------------------------
def _get_root_agent():
    from agents.orchestrator_agent import root_agent
    return root_agent


# ---------------------------------------------------------------------------
# ADK session service — Firestore-backed for production persistence.
# Falls back to InMemorySessionService if no GCP project is configured.
# ---------------------------------------------------------------------------
APP_NAME = "mathviz"

def _make_session_service():
    project = google_cloud.project_id
    if project:
        from tools.firestore_session_service import FirestoreSessionService
        return FirestoreSessionService(project=project)
    return InMemorySessionService()

_session_service = _make_session_service()


def _is_retryable_error(exc: Exception) -> bool:
    """Return True for transient API errors (503, quota, UNAVAILABLE)."""
    msg = str(exc).lower()
    return any(k in msg for k in (
        "503", "502", "unavailable", "high demand", "overloaded",
        "resource_exhausted", "rate limit", "429", "quota",
        "try again", "temporarily", "internal error", "500",
    ))


# ---------------------------------------------------------------------------
# Agent module names (used for reloading when switching fallback model)
# ---------------------------------------------------------------------------
_AGENT_MODULES = [
    "config",
    "agents.math_solver_agent",
    "agents.solution_writer_agent",
    "agents.story_agent",
    "agents.animation_agent",
    "agents.orchestrator_agent",
    "agents",
]


def _evict_agent_modules() -> None:
    """Remove all agent modules from sys.modules so the next import is fresh."""
    for key in list(sys.modules.keys()):
        if key.startswith("agents"):
            del sys.modules[key]


# ---------------------------------------------------------------------------
# Stage label map — maps ADK agent names to human-readable progress stages
# ---------------------------------------------------------------------------
_STAGE_MAP = {
    "orchestrator_agent": ("starting",   "Starting the pipeline..."),
    "root_agent":         ("starting",   "Starting the pipeline..."),
    "math_solver_agent":  ("solving",    "Solving the math problem..."),
    "solution_writer_agent": ("writing", "Writing step-by-step solution..."),
    "story_agent":        ("story",      "Creating the animation story..."),
    "animation_agent":    ("animation",  "Generating and rendering animation..."),
}


async def run_math_question(
    question: str,
    session_id: str | None = None,
    *,
    _model_override: str | None = None,
    _progress_cb=None,
    _session_svc: InMemorySessionService | None = None,
) -> str:
    """
    Run the MathViz agent pipeline for a given question.

    Args:
        question:        The math question from the student.
        session_id:      Optional session ID for conversation continuity.
        _model_override: Internal — forces a specific model (used for fallback).
        _progress_cb:    Optional callback(author: str) called on each ADK event.
        _session_svc:    Optional session service (pass a thread-local one to avoid
                         sharing the module-level service across threads).

    Returns:
        The full agent response text.
    """
    if _model_override is not None:
        _evict_agent_modules()
        os.environ["GEMINI_MODEL"] = _model_override

    root_agent = _get_root_agent()

    if session_id is None:
        session_id = str(uuid.uuid4())

    svc = _session_svc or _session_service

    session = await svc.get_session(
        app_name=APP_NAME, user_id="student", session_id=session_id
    )
    if session is None:
        session = await svc.create_session(
            app_name=APP_NAME, user_id="student", session_id=session_id
        )

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=svc,
    )

    user_message = Content(parts=[Part(text=question)])

    max_attempts = retry_cfg.max_attempts
    delays = retry_cfg.delays
    last_exc: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            full_response = []
            async for event in runner.run_async(
                user_id="student",
                session_id=session_id,
                new_message=user_message,
            ):
                # Report current agent to progress callback
                if _progress_cb:
                    author = getattr(event, "author", None)
                    if author:
                        _progress_cb(author)

                if event.is_final_response():
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                full_response.append(part.text)
            return "\n".join(full_response) if full_response else "No response generated."
        except Exception as exc:
            last_exc = exc
            if _is_retryable_error(exc) and attempt < max_attempts:
                wait = delays[attempt - 1] + random.uniform(0, 5)
                print(
                    f"[MathViz] API unavailable (attempt {attempt}/{max_attempts}): {exc}\n"
                    f"          Retrying in {wait:.0f}s… "
                    f"(model: {models.primary})"
                )
                await asyncio.sleep(wait)
                session_id = str(uuid.uuid4())
                await _session_service.create_session(
                    app_name=APP_NAME, user_id="student", session_id=session_id
                )
            else:
                raise

    # All primary retries exhausted — try fallback model
    if last_exc is not None and _is_retryable_error(last_exc) and _model_override is None:
        primary_model = models.primary
        fallback_model = models.fallback
        if fallback_model != primary_model:
            print(
                f"[MathViz] All retries exhausted for {primary_model}. "
                f"Switching to fallback model: {fallback_model}"
            )
            try:
                result = await run_math_question(
                    question,
                    _model_override=fallback_model,
                    _progress_cb=_progress_cb,
                    _session_svc=_session_svc,
                )
                _evict_agent_modules()
                os.environ.pop("GEMINI_MODEL", None)
                return result
            except Exception as fb_exc:
                print(f"[MathViz] Fallback model also failed: {fb_exc}")
                _evict_agent_modules()
                os.environ.pop("GEMINI_MODEL", None)
                raise ServerError503(
                    f"The Gemini API is currently experiencing high demand."
                    f" Both {primary_model} and the fallback {fallback_model} are unavailable."
                    f" Please wait a few minutes and try again.\n\nOriginal error: {last_exc}"
                ) from last_exc

    raise last_exc  # type: ignore[misc]


class ServerError503(RuntimeError):
    """Raised when all Gemini API retry attempts (including fallback model) are exhausted."""


# ---------------------------------------------------------------------------
# Artifact scanning — finds files created during a specific run window
# ---------------------------------------------------------------------------

_session_artifacts: dict[str, dict] = {}


def _scan_artifacts(since_time: float) -> tuple[str | None, str | None, bool]:
    """
    Scan output directories for files created after *since_time*.

    Returns:
        (video_path, solution_path, is_fallback)
    """
    anim_dir = output_cfg.animations_dir
    sol_dir = output_cfg.solutions_dir
    media_dir = anim_dir / "media"

    video_path: str | None = None
    is_fallback = False

    if media_dir.exists():
        mp4_hits = [
            p for p in media_dir.rglob("MathAnimationScene*.mp4")
            if p.is_file() and p.stat().st_mtime >= since_time and p.stat().st_size > 0
        ]
        if mp4_hits:
            video_path = str(max(mp4_hits, key=lambda p: p.stat().st_mtime))
            new_py = [
                p for p in anim_dir.glob("*.py")
                if p.stat().st_mtime >= since_time
            ]
            creative_py = [p for p in new_py if "_textonly" not in p.name]
            is_fallback = bool(new_py) and not creative_py

    solution_path: str | None = None
    if sol_dir.exists():
        md_hits = [
            p for p in sol_dir.glob("*.md")
            if p.is_file() and p.stat().st_mtime >= since_time
        ]
        if md_hits:
            solution_path = str(max(md_hits, key=lambda p: p.stat().st_mtime))

    return video_path, solution_path, is_fallback


# ---------------------------------------------------------------------------
# Async job tracking
# ---------------------------------------------------------------------------

# _jobs stores the state of every background pipeline run.
# {job_id: {"status": "processing"|"done"|"error", "stage": str, ...}}
_jobs: dict[str, dict] = {}

# Maximum jobs to keep in memory (prevent unbounded growth)
_MAX_JOBS = 100

# Thread pool for pipeline execution — each job runs in its own thread with
# its own event loop so that blocking subprocess.run() calls in animation_runner
# do NOT freeze the FastAPI event loop (and therefore do NOT block /status polls).
_pipeline_pool = concurrent.futures.ThreadPoolExecutor(
    max_workers=2, thread_name_prefix="mathviz-pipeline"
)


def _prune_jobs() -> None:
    """Remove oldest completed jobs when the store exceeds _MAX_JOBS."""
    if len(_jobs) <= _MAX_JOBS:
        return
    done = [jid for jid, j in _jobs.items() if j.get("status") in ("done", "error")]
    for jid in done[: len(_jobs) - _MAX_JOBS]:
        _jobs.pop(jid, None)


def _pipeline_thread(job_id: str, question: str, session_id: str) -> None:
    """
    Entry point for each ThreadPoolExecutor worker.

    Creates a brand-new asyncio event loop (isolated from FastAPI's loop) and
    runs the pipeline coroutine on it.  Because this loop lives entirely inside
    the worker thread, any blocking call — including subprocess.run() during
    Manim rendering — only blocks THIS thread, never the FastAPI event loop.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    local_svc = _make_session_service()
    try:
        loop.run_until_complete(
            _run_pipeline_job(job_id, question, session_id, local_svc)
        )
    except Exception as exc:
        _jobs[job_id] = {
            "status": "error",
            "stage": "error",
            "stage_label": "Pipeline crashed",
            "question": question,
            "session_id": session_id,
            "response": str(exc),
            "elapsed": 0,
        }
        print(f"[MathViz] Job {job_id} thread crashed: {exc}")
    finally:
        loop.close()


async def _run_pipeline_job(
    job_id: str,
    question: str,
    session_id: str,
    session_service: InMemorySessionService,
) -> None:
    """Background coroutine: runs the full pipeline and updates _jobs[job_id]."""
    run_start = time.time()

    def _on_agent(author: str) -> None:
        """Update job stage when the ADK runner switches agents."""
        if author in _STAGE_MAP:
            stage, label = _STAGE_MAP[author]
            _jobs[job_id]["stage"] = stage
            _jobs[job_id]["stage_label"] = label
            _jobs[job_id]["elapsed"] = round(time.time() - run_start)

    try:
        response_text = await run_math_question(
            question, session_id, _progress_cb=_on_agent, _session_svc=session_service
        )

        video_path, solution_path, is_fallback = _scan_artifacts(run_start)
        _session_artifacts[session_id] = {
            "video_path": video_path,
            "solution_path": solution_path,
        }

        if video_path and not is_fallback:
            from tools.bigquery_tracker import log_run
            # Fire-and-forget: BQ logging must not delay the "done" response
            asyncio.get_event_loop().run_in_executor(None, lambda: log_run(
                session_id=session_id,
                question=question,
                solution_filename=Path(solution_path).name if solution_path else None,
                video_filename=Path(video_path).name if video_path else None,
                render_quality=manim_cfg.quality,
                status="success",
            ))

        _jobs[job_id] = {
            "status": "done",
            "stage": "done",
            "stage_label": "Animation ready!",
            "question": question,
            "session_id": session_id,
            "response": response_text,
            "video_filename": Path(video_path).name if video_path else None,
            "solution_filename": Path(solution_path).name if solution_path else None,
            "elapsed": round(time.time() - run_start),
        }

    except ServerError503 as exc:
        _jobs[job_id] = {
            "status": "error",
            "stage": "error",
            "stage_label": "Gemini API overloaded",
            "question": question,
            "session_id": session_id,
            "response": (
                "The Gemini API is currently under high demand. "
                "Please wait a few minutes and try again."
            ),
            "elapsed": round(time.time() - run_start),
        }
        print(f"[MathViz] Job {job_id} failed (503): {exc}")

    except Exception as exc:
        _jobs[job_id] = {
            "status": "error",
            "stage": "error",
            "stage_label": "Pipeline error",
            "question": question,
            "session_id": session_id,
            "response": str(exc),
            "elapsed": round(time.time() - run_start),
        }
        print(f"[MathViz] Job {job_id} failed: {exc}")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    print("=" * 60)
    print("  MathViz — 2D Math Animation System")
    print("  Powered by Google Gemini + ADK + Manim")
    print("=" * 60)
    from tools.bigquery_tracker import ensure_table
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, ensure_table)
    print("=" * 60)
    yield
    print("MathViz shutting down.")


app = FastAPI(
    title="MathViz API",
    description="Agentic 2D math animation system powered by Gemini + ADK + Manim",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class MathQuestionRequest(BaseModel):
    question: str
    session_id: str | None = None


class MathQuestionResponse(BaseModel):
    question: str
    session_id: str
    response: str
    status: str
    video_filename: str | None = None
    solution_filename: str | None = None


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index():
    """Landing page with usage instructions."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MathViz — Math Animation System</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 900px; margin: 60px auto; padding: 0 20px; }
            h1 { color: #1a73e8; }
            code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }
            pre { background: #f8f8f8; padding: 16px; border-radius: 6px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>MathViz API v2</h1>
        <p>Submit a math question, get back an animation + solution.</p>
        <h2>Async workflow</h2>
        <pre>POST /solve          → { job_id, session_id, status:"processing" }
GET  /status/{job_id} → { status:"done"|"processing"|"error", stage_label, ... }
GET  /video/{session_id}
GET  /solution_content/{session_id}</pre>
        <h2>Docs</h2>
        <p><a href="/docs">Interactive API docs (Swagger UI)</a></p>
    </body>
    </html>
    """


@app.post("/solve")
async def solve_math_question(request: MathQuestionRequest):
    """
    Submit a math question. Returns immediately with a job_id.
    Poll GET /status/{job_id} every 5 seconds for progress and results.
    """
    session_id = request.session_id or str(uuid.uuid4())
    job_id = str(uuid.uuid4())

    _prune_jobs()

    _jobs[job_id] = {
        "status": "processing",
        "stage": "starting",
        "stage_label": "Starting the pipeline...",
        "question": request.question,
        "session_id": session_id,
        "elapsed": 0,
    }

    _pipeline_pool.submit(_pipeline_thread, job_id, request.question, session_id)

    return {
        "job_id": job_id,
        "session_id": session_id,
        "status": "processing",
        "message": "Pipeline started. Poll /status/{job_id} every 5 seconds.",
    }


@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Poll this endpoint every 5 seconds after calling POST /solve.

    Returns the current pipeline stage while processing, and the full result
    (video_filename, solution_filename, response) when status == 'done'.
    """
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found. It may have expired.")
    return job


@app.get("/solutions")
async def list_solutions():
    """List all saved solution markdown files."""
    from tools.file_tools import list_solutions as _list
    return {"solutions": _list()}


@app.get("/animations")
async def list_animations():
    """List all generated animation scripts."""
    from tools.animation_runner import list_animations as _list
    return {"animations": _list()}


@app.get("/solutions/{filename}")
async def get_solution(filename: str):
    """Download a specific solution markdown file."""
    from tools.file_tools import SOLUTIONS_DIR
    filepath = SOLUTIONS_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Solution file not found")
    return FileResponse(str(filepath), media_type="text/markdown")


@app.get("/video/{session_id}")
async def get_video(session_id: str):
    """Stream the rendered animation video for a session."""
    artifacts = _session_artifacts.get(session_id, {})
    video_path = artifacts.get("video_path")
    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="No video found for this session.")
    return FileResponse(video_path, media_type="video/mp4", filename=Path(video_path).name)


@app.get("/solution_content/{session_id}")
async def get_solution_content(session_id: str):
    """Return the markdown solution text for a session."""
    artifacts = _session_artifacts.get(session_id, {})
    solution_path = artifacts.get("solution_path")
    if not solution_path or not Path(solution_path).exists():
        raise HTTPException(status_code=404, detail="No solution found for this session.")
    content = Path(solution_path).read_text(encoding="utf-8")
    return {"filename": Path(solution_path).name, "content": content}


@app.get("/history")
async def get_history(limit: int = 50):
    """Return the most recent creative animation runs from BigQuery."""
    from tools.bigquery_tracker import get_history as _get_history
    loop = asyncio.get_event_loop()
    rows = await loop.run_in_executor(None, lambda: _get_history(limit=limit))
    return {"history": rows}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    """
    CLI: Run a math question directly from the terminal.

    Usage:
        uv run python main.py "What is the derivative of x^2 + 3x?"
    """
    if len(sys.argv) < 2:
        print("MathViz — 2D Math Animation System")
        print()
        print("Usage:")
        print('  uv run python main.py "<your math question>"')
        print()
        print("Or start the web server:")
        print("  uv run uvicorn main:app --reload --port 8000")
        sys.exit(0)

    question = " ".join(sys.argv[1:])
    print(f"\n{'='*60}")
    print(f"  MathViz — Processing Your Question")
    print(f"{'='*60}")
    print(f"  Question: {question}")
    print(f"{'='*60}\n")

    response = asyncio.run(run_math_question(question))
    print("\n" + "=" * 60)
    print("  RESPONSE")
    print("=" * 60)
    print(response)
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
