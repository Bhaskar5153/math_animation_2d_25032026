"""
Central configuration loader for MathViz.

All other modules import settings from here.  Never call os.getenv() for
application settings in agent or tool files — add the value to config.yaml
and read it through the namespaces below.

Priority (highest → lowest):
  1. Environment variable / .env  — overrides everything (CI/CD, containers)
  2. config.yaml setting          — the main place operators edit
  3. Built-in default             — safe fallback if yaml key is missing

Secrets (PROJECT_ID, GOOGLE_API_KEY) stay in .env and are never put in
config.yaml so the yaml file can be safely committed to version control.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from types import SimpleNamespace

from dotenv import load_dotenv

load_dotenv()

_ROOT = Path(__file__).resolve().parent

# ── YAML loader (graceful fallback if pyyaml not yet installed) ───────────────
try:
    import yaml as _yaml

    def _load_yaml() -> dict:
        path = _ROOT / "config.yaml"
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                return _yaml.safe_load(fh) or {}
        return {}

except ImportError:  # pyyaml not installed — use built-in defaults only
    def _load_yaml() -> dict:  # type: ignore[misc]
        return {}


def _resolve(value):
    """Recursively replace ${VAR} placeholders with environment variable values."""
    if isinstance(value, str):
        return re.sub(r"\$\{([^}]+)\}", lambda m: os.environ.get(m.group(1), ""), value)
    if isinstance(value, dict):
        return {k: _resolve(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve(item) for item in value]
    return value


_raw: dict = _resolve(_load_yaml())


def _section(key: str) -> dict:
    return _raw.get(key) or {}


def _get(section: str, key: str, default):
    """Return yaml value, falling back to *default* if absent."""
    return _section(section).get(key, default)


# ── Models ────────────────────────────────────────────────────────────────────
# Env vars GEMINI_MODEL / FAST_MODEL / ANIMATION_MODEL / GEMINI_FALLBACK_MODEL
# override the yaml values — used by main.py's fallback-model-switch mechanism.
models = SimpleNamespace(
    primary=os.getenv("GEMINI_MODEL") or _get("models", "primary", "gemini-2.5-pro"),
    fast=os.getenv("FAST_MODEL") or _get("models", "fast", "gemini-2.5-flash"),
    animation=os.getenv("ANIMATION_MODEL") or _get("models", "animation", "gemini-2.5-pro"),
    fallback=os.getenv("GEMINI_FALLBACK_MODEL") or _get("models", "fallback", "gemini-2.0-flash"),
)

# ── Google Cloud / Vertex AI ──────────────────────────────────────────────────
# All settings read from config.yaml; environment variables override them.
# After building the namespace, we propagate values back to os.environ so ADK
# and google.genai pick them up regardless of whether .env is present.
google_cloud = SimpleNamespace(
    project_id=(
        os.getenv("PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
        or _get("google_cloud", "project_id", "")
    ),
    location=(
        os.getenv("GOOGLE_CLOUD_LOCATION")
        or _get("google_cloud", "location", "us-central1")
    ),
    use_vertex_ai=(
        os.getenv("VERTEXAI") or str(_get("google_cloud", "use_vertex_ai", True))
    ).lower() in ("1", "true", "yes"),
    api_key=(
        os.getenv("GOOGLE_API_KEY")
        or _get("google_cloud", "api_key", "")
    ),
)

# Propagate to the environment variables ADK and google.genai expect.
# This ensures the settings work whether the user configures via config.yaml,
# .env, or shell environment — whichever is present.
if google_cloud.use_vertex_ai and google_cloud.project_id:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
    os.environ["GOOGLE_CLOUD_PROJECT"] = google_cloud.project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = google_cloud.location
    os.environ["PROJECT_ID"] = google_cloud.project_id      # for legacy reads
    os.environ["VERTEXAI"] = "True"
elif google_cloud.api_key:
    os.environ["GOOGLE_API_KEY"] = google_cloud.api_key
    os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)
    os.environ["VERTEXAI"] = "False"

# ── Manim / Rendering ─────────────────────────────────────────────────────────
manim = SimpleNamespace(
    quality=os.getenv("MANIM_QUALITY") or _get("manim", "quality", "m"),
    render_timeout=int(_get("manim", "render_timeout", 150)),
    fallback_render_timeout=int(_get("manim", "fallback_render_timeout", 90)),
)

# ── Audio / TTS ───────────────────────────────────────────────────────────────
audio = SimpleNamespace(
    enabled=str(_get("audio", "enabled", True)).lower() not in ("0", "false", "no"),
    voice=os.getenv("TTS_VOICE") or _get("audio", "voice", "en-US-AriaNeural"),
    max_chars=int(_get("audio", "max_chars", 3000)),
    generation_timeout=int(_get("audio", "generation_timeout", 60)),
    merge_timeout=int(_get("audio", "merge_timeout", 120)),
)

# ── Output Paths ──────────────────────────────────────────────────────────────
output = SimpleNamespace(
    animations_dir=_ROOT / _get("output", "animations_dir", "outputs/animations"),
    solutions_dir=_ROOT / _get("output", "solutions_dir", "outputs/solutions"),
)

# ── API Retry ─────────────────────────────────────────────────────────────────
retry = SimpleNamespace(
    max_attempts=int(_get("retry", "max_attempts", 4)),
    delays=list(_get("retry", "delays", [5, 15, 30, 60])),
)
