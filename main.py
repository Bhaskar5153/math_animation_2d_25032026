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

Usage (ADK Web UI):
    adk web
"""
import asyncio
import os
import sys
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

# Load environment variables (.env file must have GOOGLE_API_KEY)
load_dotenv()

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
# ADK session service (in-memory for simplicity; swap for DB-backed in prod)
# ---------------------------------------------------------------------------
_session_service = InMemorySessionService()
APP_NAME = "mathviz"


async def run_math_question(question: str, session_id: str | None = None) -> str:
    """
    Run the MathViz agent pipeline for a given question.

    Args:
        question:   The math question from the student.
        session_id: Optional session ID for conversation continuity.

    Returns:
        The full agent response text.
    """
    root_agent = _get_root_agent()

    if session_id is None:
        session_id = str(uuid.uuid4())

    # Create or reuse session
    try:
        session = await _session_service.get_session(
            app_name=APP_NAME, user_id="student", session_id=session_id
        )
    except Exception:
        session = await _session_service.create_session(
            app_name=APP_NAME, user_id="student", session_id=session_id
        )

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=_session_service,
    )

    user_message = Content(parts=[Part(text=question)])

    full_response = []
    async for event in runner.run_async(
        user_id="student",
        session_id=session_id,
        new_message=user_message,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        full_response.append(part.text)

    return "\n".join(full_response) if full_response else "No response generated."


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
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        print("  WARNING: GOOGLE_API_KEY not set in .env!")
    else:
        print(f"  API Key loaded: {'*' * (len(api_key) - 4)}{api_key[-4:]}")
    print("=" * 60)
    yield
    print("MathViz shutting down.")


app = FastAPI(
    title="MathViz API",
    description="Agentic 2D math animation system powered by Gemini + ADK + Manim",
    version="1.0.0",
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
            h2 { color: #333; }
            code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }
            pre { background: #f8f8f8; padding: 16px; border-radius: 6px; overflow-x: auto; }
            .badge { background: #1a73e8; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.85em; }
        </style>
    </head>
    <body>
        <h1>🎓 MathViz — 2D Math Animation System</h1>
        <p><span class="badge">Powered by Gemini 2.5 Pro + ADK + Manim</span></p>
        <p>Transform any math question into a beautiful step-by-step solution AND a 2D animation.</p>

        <h2>API Endpoints</h2>
        <ul>
            <li><code>POST /solve</code> — Submit a math question</li>
            <li><code>GET /solutions</code> — List saved solution files</li>
            <li><code>GET /animations</code> — List generated animation scripts</li>
            <li><code>GET /docs</code> — Interactive API docs (Swagger UI)</li>
        </ul>

        <h2>Example</h2>
        <pre>curl -X POST http://localhost:8000/solve \\
  -H "Content-Type: application/json" \\
  -d '{"question": "Solve x^2 - 5x + 6 = 0"}'</pre>

        <h2>Math Domains Supported</h2>
        <ul>
            <li>Arithmetic</li>
            <li>Algebra (linear, quadratic, polynomials, systems)</li>
            <li>Geometry (shapes, angles, area, coordinate geometry)</li>
            <li>Trigonometry (sin/cos/tan, identities, equations)</li>
            <li>Calculus (limits, derivatives, integrals)</li>
            <li>Statistics & Probability</li>
            <li>Number Theory</li>
        </ul>
    </body>
    </html>
    """


@app.post("/solve", response_model=MathQuestionResponse)
async def solve_math_question(request: MathQuestionRequest):
    """
    Submit a math question to the MathViz agentic pipeline.

    The agent will:
    1. Identify the math domain and solve the problem
    2. Save a step-by-step markdown solution to outputs/solutions/
    3. Generate a creative animation story
    4. Render a 2D Manim animation to outputs/animations/
    """
    session_id = request.session_id or str(uuid.uuid4())
    try:
        response_text = await run_math_question(request.question, session_id)
        return MathQuestionResponse(
            question=request.question,
            session_id=session_id,
            response=response_text,
            status="success",
        )
    except Exception as exc:
        return MathQuestionResponse(
            question=request.question,
            session_id=session_id,
            response=f"Error: {exc}",
            status="error",
        )


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
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Solution file not found")
    return FileResponse(str(filepath), media_type="text/markdown")


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
        print("  uv run python main.py \"<your math question>\"")
        print()
        print("Examples:")
        print("  uv run python main.py \"Solve x^2 - 5x + 6 = 0\"")
        print("  uv run python main.py \"Find the area of a circle with radius 7\"")
        print("  uv run python main.py \"What is the derivative of sin(x)?\"")
        print("  uv run python main.py \"Calculate the mean of 4, 8, 6, 5, 3, 2\"")
        print()
        print("Or start the web server:")
        print("  uv run uvicorn main:app --reload --port 8000")
        print()
        print("Or use the ADK developer UI:")
        print("  adk web")
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

