# MathViz — 2D Math & Physics Animation System

> Submit any math or physics question → get back a **step-by-step solution** and a **cinematic 2D animation video** with narrated audio.
> Powered by **Google Gemini 2.5 Pro** · **Google ADK** · **Manim Community Edition** · **edge-tts**

---

## How It Works — End-to-End Pipeline

```
Student submits a question
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 1 — ROUTE                                                     │
│  mathviz_orchestrator (gemini-2.5-pro)                              │
│  Detects whether the input is a math/physics question or small talk │
│  Routes math questions → mathviz_pipeline                           │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 2 — SOLVE                                                     │
│  math_solver_agent (gemini-2.5-pro)                                 │
│  Identifies the math domain, routes to a specialist sub-agent       │
│                                                                     │
│  Sub-agents (gemini-2.5-flash each):                                │
│   arithmetic_solver · algebra_solver · geometry_solver              │
│   trigonometry_solver · calculus_solver · statistics_solver         │
│   number_theory_solver · physics_solver                             │
│                                                                     │
│  Output → session.state["math_solution"]  (full step-by-step text)  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            │  Step 3 — PARALLEL (both run now)   │
            │                                     │
            ▼                                     ▼
┌───────────────────────┐            ┌────────────────────────────┐
│  story_agent          │            │  solution_writer_agent      │
│  (gemini-2.5-flash)   │            │  (gemini-2.5-flash)         │
│                       │            │                            │
│  Creates a creative,  │            │  Saves the step-by-step    │
│  Pixar-style story    │            │  solution as a markdown     │
│  for the animation    │            │  file in outputs/solutions/ │
│  with characters      │            │                            │
│  and genre genre      │            │  Runs fully in parallel     │
│                       │            │  with the animation stage   │
│  Output →             │            └────────────────────────────┘
│  session.state        │
│  ["animation_story"]  │
└───────────┬───────────┘
            │  (story_agent finishes first)
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 4 — ANIMATE                                                   │
│  animation_agent (gemini-2.5-pro)                                   │
│                                                                     │
│  4a. Reads math_solution + animation_story from session state       │
│  4b. Generates a complete Manim Python script                       │
│      — domain-specific genre (arcade game, roller coaster, etc.)   │
│      — cartoon characters + domain objects as actors               │
│      — color-coded equations + cinematic transitions               │
│  4c. Calls run_manim_animation() tool:                              │
│      ┌───────────────────────────────────────────┐                 │
│      │  In parallel:                             │                 │
│      │   • Manim render  (720p30, ~60-90 s)      │                 │
│      │   • edge-tts TTS  (narration MP3, ~30 s)  │                 │
│      └──────────────┬────────────────────────────┘                 │
│                     │  (both finish)                               │
│                     ▼                                              │
│      ffmpeg merges video + audio  (apad + -shortest)               │
│      → outputs/animations/*.mp4  (narrated animation)              │
│                                                                     │
│  4d. Auto-fallback: if creative script crashes, renders a clean    │
│      text-only solution video automatically (student always gets   │
│      a video)                                                       │
│                                                                     │
│  Output → video file path                                           │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 5 — LOG (fire-and-forget, does not block response)            │
│  BigQuery logs each creative animation run to mathviz.animation_runs│
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
             Student receives: video (.mp4) + solution (.md)
```

### Timing Breakdown (typical)

| Stage | Duration | Notes |
|---|---|---|
| math_solver_agent | ~20 s | Gemini 2.5 Pro reasoning |
| story_agent | ~15 s | Runs at start of parallel stage |
| solution_writer_agent | ~15 s | Overlapped with animation stage |
| animation LLM (code gen) | ~50 s | Gemini 2.5 Pro writes Manim code |
| Manim render (quality m) | ~60-90 s | TTS runs in parallel |
| edge-tts + ffmpeg merge | ~35 s | Parallel with render; merge ~5 s |
| **Total (happy path)** | **~3 min** | First attempt succeeds |
| **Total (1 render retry)** | **~5 min** | Fallback video guaranteed |

---

## Architecture Overview

```
math_animation_2d_25032026/
│
├── agent.py                     ← ADK entry point (adk web / adk run)
├── main.py                      ← FastAPI server + CLI runner + async job queue
├── streamlit_app.py             ← Streamlit web UI (connects to FastAPI)
├── config.py                    ← Loads config.yaml + .env into typed dataclasses
├── config.yaml                  ← All tunable settings (models, quality, timeouts)
├── .env                         ← Secrets: API keys, GCP project ID (not committed)
├── .env.example                 ← Template for .env
├── vertex_ai_config.py          ← Configures Vertex AI ADC or Google AI Studio key
├── _retry_patch.py              ← HTTP-level exponential backoff for google.genai
│
├── agents/
│   ├── orchestrator_agent.py    ← Root agent + pipeline composition
│   ├── math_solver_agent.py     ← Domain router + 8 specialist solver sub-agents
│   ├── story_agent.py           ← Creates Pixar-style animation story
│   ├── solution_writer_agent.py ← Saves markdown solution file
│   └── animation_agent.py       ← Manim code generator + executor
│
├── prompts/
│   ├── orchestrator_prompts.py  ← Routing instructions
│   ├── math_prompts.py          ← Per-domain solver instructions (8 domains)
│   ├── story_prompts.py         ← Animation storyline instructions
│   └── animation_prompts.py     ← Full Manim code generation guide + code helpers
│
├── tools/
│   ├── animation_runner.py      ← run_manim_animation(): render + TTS + merge
│   ├── file_tools.py            ← save/read/list markdown solution files
│   ├── bigquery_tracker.py      ← Logs animation runs to BigQuery
│   └── firestore_session_service.py ← Firestore-backed ADK session persistence
│
└── outputs/
    ├── solutions/               ← Generated markdown solution files (*.md)
    └── animations/              ← Manim scripts (*.py) + rendered videos (*.mp4)
        └── media/               ← Manim's internal render cache + final videos
```

---

## Agent Roles

| Agent | Model | Responsibility |
|---|---|---|
| `mathviz_orchestrator` | gemini-2.5-pro | Greets users; routes math questions to the pipeline |
| `math_solver_agent` | gemini-2.5-pro | Detects domain; delegates to the right specialist |
| `arithmetic_solver_agent` | gemini-2.5-flash | Percentages, fractions, basic arithmetic |
| `algebra_solver_agent` | gemini-2.5-flash | Equations, quadratics, inequalities |
| `geometry_solver_agent` | gemini-2.5-flash | Shapes, area, volume, coordinate geometry |
| `trigonometry_solver_agent` | gemini-2.5-flash | Identities, angles, inverse trig |
| `calculus_solver_agent` | gemini-2.5-flash | Derivatives, integrals, limits |
| `statistics_solver_agent` | gemini-2.5-flash | Mean, median, probability, distributions |
| `number_theory_solver_agent` | gemini-2.5-flash | GCD, LCM, primes, modular arithmetic |
| `physics_solver_agent` | gemini-2.5-flash | Kinematics, forces, energy, optics |
| `story_agent` | gemini-2.5-flash | Writes the animation narrative with characters |
| `solution_writer_agent` | gemini-2.5-flash | Saves markdown solution to `outputs/solutions/` |
| `animation_agent` | gemini-2.5-pro | Generates Manim code; calls `run_manim_animation` tool |

### Pipeline Composition

```python
# agents/orchestrator_agent.py

story_then_animation = SequentialAgent([story_agent, animation_agent])

outer_parallel = ParallelAgent([
    story_then_animation,      # critical path
    solution_writer_agent,     # off critical path — overlapped for free
])

mathviz_pipeline = SequentialAgent([math_solver_agent, outer_parallel])

root_agent = LlmAgent(sub_agents=[mathviz_pipeline])
```

---

## Setup

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.13+ | Check with `python --version` |
| [uv](https://docs.astral.sh/uv/) | latest | Fast Python package manager |
| Google AI API Key | — | From [Google AI Studio](https://aistudio.google.com/app/apikey) |
| Google Cloud Project | — | For Firestore session persistence + BigQuery logging |

FFmpeg is bundled automatically via `imageio-ffmpeg` — no manual install needed.

### Step 1 — Clone and install

```bash
cd math_animation_2d_25032026

# Install all dependencies using uv
uv sync
```

### Step 2 — Configure secrets

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
# Required
GOOGLE_API_KEY=your_google_ai_studio_key_here

# Required for Firestore + BigQuery (GCP project)
PROJECT_ID=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
VERTEXAI=false          # set true if using Vertex AI instead of Google AI Studio
```

### Step 3 — (Optional) Google Cloud services

**Firestore** — stores ADK sessions so they survive server restarts:
1. Go to [Firestore console](https://console.cloud.google.com/firestore)
2. Create a database named exactly `mathviz-memory`
3. The app connects to it automatically on startup

**BigQuery** — logs each animation run for analytics:
- The table `mathviz.animation_runs` is created automatically on first run
- Requires `PROJECT_ID` to be set in `.env`

Both services degrade gracefully — if unavailable the system falls back to in-memory sessions and skips logging.

### Step 4 — Tune render settings (optional)

Edit `config.yaml` to change quality, timeouts, or models without touching code:

```yaml
manim:
  quality: "m"           # l=480p15 (~20s)  m=720p30 (~90s)  h=1080p60 (~3min)
  render_timeout: 150    # seconds before a stuck render is killed
  fallback_render_timeout: 90

audio:
  enabled: true
  voice: "en-US-AriaNeural"   # edge-tts voice name

models:
  primary:   "gemini-2.5-pro"    # math solver + orchestrator
  fast:      "gemini-2.5-flash"  # story + solution writer
  animation: "gemini-2.5-pro"    # animation code generation
  fallback:  "gemini-2.0-flash"  # auto-fallback when primary is rate-limited
```

---

## Running the System

### Option A — Streamlit Web UI (recommended)

Run two terminals side-by-side:

**Terminal 1 — FastAPI backend:**
```bash
uv run uvicorn main:app --port 8000
```

**Terminal 2 — Streamlit frontend:**
```bash
uv run streamlit run streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

The UI shows a live progress bar tracking each pipeline stage, then displays the video player and solution text when done.

---

### Option B — FastAPI only (REST API)

```bash
uv run uvicorn main:app --port 8000
```

The pipeline is **async** — submit a question and poll for results:

**Step 1 — Submit a question:**
```bash
curl -X POST http://localhost:8000/solve \
  -H "Content-Type: application/json" \
  -d '{"question": "Solve x² - 5x + 6 = 0"}'
```
Returns:
```json
{ "job_id": "abc-123", "session_id": "xyz-456", "status": "processing" }
```

**Step 2 — Poll for status every 5 seconds:**
```bash
curl http://localhost:8000/status/abc-123
```
Returns while running:
```json
{ "status": "processing", "stage": "animation", "stage_label": "Generating and rendering animation...", "elapsed": 95 }
```
Returns when done:
```json
{ "status": "done", "stage_label": "Animation ready!", "video_filename": "solve_x2_5x_6_0_20260428.mp4", "elapsed": 183 }
```

**Step 3 — Download the video:**
```bash
curl -O http://localhost:8000/video/xyz-456
```

**Step 4 — Download the solution:**
```bash
curl http://localhost:8000/solution_content/xyz-456
```

**Swagger UI (interactive docs):**
```
http://localhost:8000/docs
```

---

### Option C — CLI (one question, terminal output)

```bash
uv run python main.py "Solve the quadratic equation x² - 5x + 6 = 0"
uv run python main.py "Find the derivative of sin(x) * x²"
uv run python main.py "A sphere of mass 2kg rolls down a 30° incline. Find its acceleration."
uv run python main.py "Integrate x² * e^x dx"
uv run python main.py "Find the GCD and LCM of 48 and 18"
```

The pipeline runs synchronously in the terminal and prints the agent response when done.

---

### Option D — ADK Developer UI (agent inspection)

```bash
adk web
```

Opens the Google ADK web interface at `http://localhost:8000`. You can see each agent's messages, tool calls, and session state in real time — useful for debugging the pipeline.

---

## Sample Questions by Domain

| Domain | Example |
|---|---|
| Arithmetic | `"What is 15% of 240?"` |
| Algebra | `"Solve 2x² - 7x + 3 = 0 and find the roots"` |
| Geometry | `"Find the equation of a circle through points (1,0), (0,1), and (-1,0)"` |
| Trigonometry | `"Find all angles where sin(θ) = 0.5 in [0°, 360°]"` |
| Calculus (derivative) | `"Find the critical points of f(x) = x³ - 3x² + 2"` |
| Calculus (integral) | `"Evaluate ∫₀¹ x² dx"` |
| Statistics | `"Find the mean, median, and mode of: 4, 8, 6, 5, 3, 2, 8, 9, 2, 5"` |
| Number Theory | `"Find all prime factors of 360"` |
| Physics | `"A ball is thrown at 20 m/s at 45°. Find max height and range."` |

---

## Output Files

After a successful run you will find:

```
outputs/
├── solutions/
│   └── algebra_solve_x2_5x_6_20260428_143022.md     ← step-by-step solution
│
└── animations/
    ├── solve_x2_5x_6_20260428_143025.py              ← generated Manim script
    ├── solve_x2_5x_6_20260428_143025.mp3             ← narration audio (temp)
    └── media/
        └── videos/
            └── solve_x2_5x_6_20260428_143025/
                └── 720p30/
                    └── MathAnimationScene_narrated.mp4  ← final video
```

If the creative script fails, a text-only fallback is rendered instead:
```
animations/
    └── solve_x2_5x_6_20260428_143025_textonly.py     ← safe fallback script
```

---

## Configuration Reference

All tunable settings live in `config.yaml`. Secrets belong in `.env`.

| Setting | Default | Description |
|---|---|---|
| `models.primary` | `gemini-2.5-pro` | Orchestrator + math solver model |
| `models.fast` | `gemini-2.5-flash` | Story + solution writer model |
| `models.animation` | `gemini-2.5-pro` | Animation code generation model |
| `models.fallback` | `gemini-2.0-flash` | Auto-fallback when primary is rate-limited |
| `manim.quality` | `m` | `l`=480p15, `m`=720p30, `h`=1080p60 |
| `manim.render_timeout` | `150` | Seconds before a stuck render is killed |
| `manim.fallback_render_timeout` | `90` | Seconds for the text-only fallback render |
| `audio.enabled` | `true` | Enable/disable edge-tts narration |
| `audio.voice` | `en-US-AriaNeural` | TTS voice (run `edge-tts --list-voices`) |
| `audio.max_chars` | `3000` | Max narration script length sent to TTS |
| `retry.max_attempts` | `4` | API retry attempts before fallback model |
| `retry.delays` | `[5,15,30,60]` | Seconds between retry attempts |

Override any setting with a shell environment variable (highest priority):
```bash
MANIM_QUALITY=h uv run uvicorn main:app --port 8000
```

---

## Extending the System

### Add a new math domain

1. Add a solver instruction to [prompts/math_prompts.py](prompts/math_prompts.py)
2. Create an `LlmAgent` in [agents/math_solver_agent.py](agents/math_solver_agent.py)
3. Add it to the `sub_agents` list of `math_solver_agent`

### Improve animation quality

- Change `quality: "h"` in `config.yaml` for 1080p60 (renders in ~3 min)
- Change `models.animation` to `gemini-2.5-pro` for more accurate Manim code
- Edit animation rules in [prompts/animation_prompts.py](prompts/animation_prompts.py)

### Use Vertex AI instead of Google AI Studio

Set in `.env`:
```env
VERTEXAI=true
PROJECT_ID=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```
Then authenticate:
```bash
gcloud auth application-default login
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `google-adk` | Google Agent Development Kit — multi-agent orchestration |
| `google-genai` | Gemini API client |
| `manim` | 2D mathematical animation engine |
| `edge-tts` | Free text-to-speech narration (Microsoft Edge voices) |
| `imageio-ffmpeg` | Bundled FFmpeg for audio-video merging |
| `fastapi` + `uvicorn` | Async REST API server |
| `streamlit` | Web UI frontend |
| `google-cloud-firestore` | Session persistence across server restarts |
| `google-cloud-bigquery` | Animation run analytics and history |
| `python-dotenv` | Loads `.env` secrets |
| `pyyaml` | Reads `config.yaml` |

---

*MathViz — Making the invisible world of mathematics visible*
