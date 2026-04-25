"""
Enable google.genai's built-in tenacity retry for transient errors (503, 429, …).

The SDK already has full tenacity-based retry machinery, but it is DISABLED by
default: when ``http_options.retry_options`` is None, ``retry_args()`` returns
``stop_after_attempt(1)`` — one attempt, no retries.

This module patches ``BaseApiClient.__init__`` to inject a sensible default
``HttpRetryOptions`` when the caller has not provided one, so every genai
client (including those created internally by the ADK) retries automatically.

Supports both API key and Vertex AI (vertexai=True) modes:
  - API key: Uses api_key from environment
  - Vertex AI: Uses vertexai=True with Application Default Credentials (ADC)

Import this module before any google.genai code that creates a client.
Works for both ``adk web`` (via agent.py) and ``uvicorn main:app`` (via main.py).
"""
import functools

import google.genai._api_client as _api_client_mod
from google.genai.types import HttpRetryOptions

# Guard: only patch once even if the module is imported from multiple places.
if not getattr(_api_client_mod.BaseApiClient, "_retry_patch_applied", False):

    _DEFAULT_RETRY_OPTIONS = HttpRetryOptions(
        attempts=3,               # 1 initial + 2 retries — fail fast, let application layer handle
        http_status_codes=[429, 500, 502, 503, 504],
        initial_delay=3.0,        # first retry after ~3 s
        max_delay=30.0,           # cap individual waits at 30 s
        exp_base=2,               # 3 → 6 → 12 → 24 → 30 s (+ jitter)
        jitter=2,                 # ± 2 s random jitter per wait
    )

    _original_init = _api_client_mod.BaseApiClient.__init__

    @functools.wraps(_original_init)
    def _patched_init(self, *args, **kwargs):
        # If caller didn't set http_options.retry_options, inject our defaults.
        http_options = kwargs.get("http_options") or (
            args[5] if len(args) > 5 else None  # positional: (vertexai, api_key, credentials, project, location, http_options)
        )
        if http_options is None:
            # No http_options at all — create a minimal one with retry enabled.
            kwargs["http_options"] = {"retry_options": _DEFAULT_RETRY_OPTIONS}
        else:
            # http_options provided but may not have retry_options set.
            if isinstance(http_options, dict):
                if not http_options.get("retry_options"):
                    http_options = dict(http_options)
                    http_options["retry_options"] = _DEFAULT_RETRY_OPTIONS
                    if len(args) > 5:
                        args = args[:5] + (http_options,) + args[6:]
                    else:
                        kwargs["http_options"] = http_options
            elif hasattr(http_options, "retry_options") and not http_options.retry_options:
                http_options.retry_options = _DEFAULT_RETRY_OPTIONS

        _original_init(self, *args, **kwargs)

    _api_client_mod.BaseApiClient.__init__ = _patched_init
    _api_client_mod.BaseApiClient._retry_patch_applied = True  # type: ignore[attr-defined]
