# MathViz — 2D Math Animation System

> **Transform any math problem into a step-by-step solution AND a beautiful 2D animation.**  
> Powered by **Google Gemini 2.5 Pro** · **Google ADK** · **Manim Community Edition**

---

## What It Does

A student asks a math question → the system:

1. **Identifies the math domain** (algebra, geometry, calculus, statistics, trigonometry, arithmetic, number theory)
2. **Solves the problem** step-by-step using a specialized AI agent for that domain
3. **Saves the solution** as a structured markdown file in `outputs/solutions/`
4. **Creates an animation story** — a creative, funny, Pixar-style narrative built around the math
5. **Generates & renders** a 2D Manim animation video in `outputs/animations/`

---

## Architecture

```
User Question
     │
     ▼
┌─────────────────────────────────────────────────┐
│          MathViz Orchestrator                   │  ← gemini-2.5-pro
│         (agents/orchestrator_agent.py)          │
└───────┬─────────┬──────────┬────────────────────┘
        │         │          │          │
        ▼         ▼          ▼          ▼
  Math Solver  Solution   Story    Animation
  Agent        Writer     Agent    Agent
  (Router)     Agent      │        │
     │         │          │        │
     ├─ Arithmetic        │   Manim Code
     ├─ Algebra           │   Generator
     ├─ Geometry          │        │
     ├─ Trigonometry      │        ▼
     ├─ Calculus          │   run_manim_animation()
     ├─ Statistics        │        │
     └─ Number Theory     │        ▼
          │               │   outputs/animations/
          ▼               ▼        *.mp4
    step-by-step    outputs/solutions/
    solution        *.md
```

### Agent Roles

| Agent | Model | Role |
|-------|-------|------|
| `mathviz_orchestrator` | gemini-2.5-pro | Coordinates the full pipeline |
| `math_solver_agent` | gemini-2.5-pro | Routes to domain specialists |
| `arithmetic_solver_agent` | gemini-2.0-flash | Solves arithmetic problems |
| `algebra_solver_agent` | gemini-2.0-flash | Solves algebra problems |
| `geometry_solver_agent` | gemini-2.0-flash | Solves geometry problems |
| `trigonometry_solver_agent` | gemini-2.0-flash | Solves trig problems |
| `calculus_solver_agent` | gemini-2.0-flash | Solves calculus problems |
| `statistics_solver_agent` | gemini-2.0-flash | Solves statistics problems |
| `number_theory_solver_agent` | gemini-2.0-flash | Solves number theory problems |
| `solution_writer_agent` | gemini-2.0-flash | Saves markdown solution files |
| `story_agent` | gemini-2.5-pro | Creates animation storylines |
| `animation_agent` | gemini-2.5-pro | Generates + runs Manim code |

---

## Project Structure

```
math_animation_2d_25032026/
├── agent.py                    # ADK entry point (adk web / adk run)
├── main.py                     # FastAPI app + CLI runner
├── .env.example                # Environment template
├── pyproject.toml
│
├── agents/
│   ├── orchestrator_agent.py   # Root orchestrator
│   ├── math_solver_agent.py    # Domain detector + 7 solver sub-agents
│   ├── solution_writer_agent.py
│   ├── story_agent.py
│   └── animation_agent.py
│
├── prompts/
│   ├── orchestrator_prompts.py
│   ├── math_prompts.py         # Per-domain solver instructions
│   ├── story_prompts.py
│   └── animation_prompts.py
│
├── tools/
│   ├── file_tools.py           # save/read/list markdown solutions
│   └── animation_runner.py     # run Manim and capture output
│
└── outputs/
    ├── solutions/              # Generated markdown files
    └── animations/             # Manim scripts + rendered videos
```

---

## Quick Start

### 1. Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- Google API Key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- For Manim rendering: [FFmpeg](https://ffmpeg.org/download.html) must be in PATH

### 2. Setup

```bash
# Clone / open the project
cd math_animation_2d_25032026

# Install dependencies (already done if you ran uv add earlier)
uv sync

# Configure your API key
cp .env.example .env
# Edit .env and set GOOGLE_API_KEY=your_key_here
```

### 3. Run — Three Ways

#### Option A: CLI (simplest)
```bash
uv run python main.py "Solve the quadratic equation x^2 - 5x + 6 = 0"
uv run python main.py "Find the area of a triangle with base 8 and height 5"
uv run python main.py "What is the derivative of sin(x) * x^2?"
uv run python main.py "Calculate probability of rolling doubles with two dice"
```

#### Option B: FastAPI Web Server
```bash
uv run uvicorn main:app --reload --port 8000
```
Then open http://localhost:8000 or use the API:
```bash
curl -X POST http://localhost:8000/solve \
  -H "Content-Type: application/json" \
  -d '{"question": "Solve x^2 - 5x + 6 = 0"}'
```

#### Option C: ADK Developer UI
```bash
adk web
```
This opens the ADK web interface where you can interact with all agents visually.

---

## Sample Questions by Domain

| Domain | Example Question |
|--------|-----------------|
| Arithmetic | `"What is 15% of 240?"` |
| Algebra | `"Solve 2x^2 - 7x + 3 = 0"` |
| Geometry | `"Find the area of a circle with radius 5"` |
| Trigonometry | `"Find all angles where sin(θ) = 0.5 in [0, 360°]"` |
| Calculus | `"Find the integral of x^2 * e^x"` |
| Statistics | `"Find mean, median, mode of: 4, 8, 6, 5, 3, 2, 8, 9, 2, 5"` |
| Number Theory | `"Find the GCD and LCM of 48 and 18"` |

---

## Output Examples

After running a question you'll find:

- **`outputs/solutions/algebra_solve_2x2_7x_3_0_*.md`** — formatted step-by-step solution  
- **`outputs/animations/solve_2x2_7x_3_0_*.py`** — generated Manim script  
- **`outputs/animations/media/videos/.../MathAnimationScene.mp4`** — the animation video  

---

## Extending the System

### Add a New Math Domain
1. Add a system instruction to `prompts/math_prompts.py`
2. Create a new `LlmAgent` in `agents/math_solver_agent.py`
3. Add it to the `sub_agents` list of `math_solver_agent`

### Improve Animation Quality
- Change `MANIM_QUALITY` in `.env` from `l` (low) to `m` (medium) or `h` (high)
- Edit the animation prompt in `prompts/animation_prompts.py`

### Use a Different Model
Edit the `model=` parameter in any agent file:
- `"gemini-2.5-pro"` — most capable, best for complex math
- `"gemini-2.0-flash"` — faster and cheaper, great for solving

---

## Dependencies

- `google-adk` — Google Agent Development Kit
- `google-genai` — Gemini API client  
- `manim` — 2D mathematical animation engine
- `fastapi` + `uvicorn` — Web API server
- `python-dotenv` — Environment management

---

*MathViz — Making the invisible world of mathematics visible* 🎓✨