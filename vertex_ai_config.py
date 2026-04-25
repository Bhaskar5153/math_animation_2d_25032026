"""
Vertex AI configuration for google.genai client.

This module configures the google.genai SDK to use Vertex AI with Application
Default Credentials (ADC) instead of API keys. This allows authentication through
Google Cloud service accounts and user credentials.

Import this module early, before creating any google.genai clients.
"""
import os

from dotenv import load_dotenv
import google.genai

# Load environment variables
load_dotenv()

# Vertex AI settings from .env
USE_VERTEX_AI = os.getenv("VERTEXAI", "False").lower() == "true"
PROJECT_ID = os.getenv("PROJECT_ID", "")
GOOGLE_CLOUD_REGION = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")

# Configure google.genai for Vertex AI if enabled
if USE_VERTEX_AI:
    if not PROJECT_ID:
        raise ValueError(
            "PROJECT_ID is required in .env when VERTEXAI=True"
        )
    
    # Set environment variables that google.genai uses for Vertex AI
    os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
    os.environ["GOOGLE_CLOUD_LOCATION"] = GOOGLE_CLOUD_REGION
    
    # Configure google.genai to use Vertex AI globally
    google.genai.configure(
        vertexai=True,
        project=PROJECT_ID,
        location=GOOGLE_CLOUD_REGION,
    )
    
    print(f"[Vertex AI Config] Using Vertex AI authentication")
    print(f"  Project: {PROJECT_ID}")
    print(f"  Region: {GOOGLE_CLOUD_REGION}")
else:
    # Configure with API key authentication
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if api_key:
        google.genai.configure(api_key=api_key)
        print(f"[Config] Using API Key authentication")
    else:
        print(f"[WARNING] No API key or Vertex AI configured")


def get_client_config() -> dict:
    """
    Return the configuration dict for google.genai.Client.

    When VERTEXAI=True:
      - Uses vertexai=True (enables Vertex AI mode)
      - Uses project and location for Vertex AI endpoints
      - Uses Application Default Credentials (ADC) for authentication

    When VERTEXAI=False:
      - Uses api_key from .env (legacy API key authentication)
    """
    if USE_VERTEX_AI:
        return {
            "vertexai": True,
            "project": PROJECT_ID,
            "location": GOOGLE_CLOUD_REGION,
        }
    else:
        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY is required in .env when VERTEXAI=False"
            )
        return {
            "api_key": api_key,
        }
