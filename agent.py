"""
ADK entry point for `adk web` and `adk run` commands.
This file is discovered automatically by the ADK CLI.

Initialization order:
  1. _retry_patch — patches google.genai HTTP layer with exponential backoff
  2. vertex_ai_config — configures Vertex AI credentials (ADC) or API key
  3. orchestrator_agent — imports all agent modules
"""

import _retry_patch  # noqa: F401 — side-effect import; must be first
import vertex_ai_config  # noqa: F401 — side-effect import; sets up Vertex AI

from agents.orchestrator_agent import root_agent  # noqa: E402

__all__ = ["root_agent"]
