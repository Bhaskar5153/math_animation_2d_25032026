"""
Vertex AI configuration for google.genai client.

All settings come from config.yaml (via config.py), which propagates the required
env vars (GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, GOOGLE_GENAI_USE_VERTEXAI)
to os.environ before this module runs. ADK and google.genai 1.x pick them up
automatically — no google.genai.configure() call is needed or supported in 1.x.
"""
from config import google_cloud

USE_VERTEX_AI = google_cloud.use_vertex_ai
PROJECT_ID = google_cloud.project_id
GOOGLE_CLOUD_REGION = google_cloud.location

if USE_VERTEX_AI:
    if not PROJECT_ID:
        raise ValueError(
            "google_cloud.project_id is required in config.yaml when use_vertex_ai: true"
        )
    print(f"[Vertex AI Config] Using Vertex AI (ADC) authentication")
    print(f"  Project: {PROJECT_ID}")
    print(f"  Region:  {GOOGLE_CLOUD_REGION}")
else:
    if google_cloud.api_key:
        print(f"[Config] Using API Key authentication")
    else:
        print(f"[WARNING] No API key or Vertex AI configured — set api_key in config.yaml")


def get_client_config() -> dict:
    """Return google.genai.Client kwargs matching the active auth mode."""
    if USE_VERTEX_AI:
        return {"vertexai": True, "project": PROJECT_ID, "location": GOOGLE_CLOUD_REGION}
    if google_cloud.api_key:
        return {"api_key": google_cloud.api_key}
    raise ValueError(
        "No authentication configured. Set use_vertex_ai: true or provide api_key in config.yaml"
    )
