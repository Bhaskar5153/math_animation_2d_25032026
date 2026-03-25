"""
Story Agent — transforms math solutions into creative, funny, and engaging
animation stories that bring math to life for students.
"""
from google.adk.agents import LlmAgent
from prompts.story_prompts import STORY_AGENT_INSTRUCTION


story_agent = LlmAgent(
    name="story_agent",
    model="gemini-2.5-pro",
    description=(
        "Creative animation story generator that transforms dry math solutions into "
        "captivating, funny, and visually memorable 5-act stories for 2D animation. "
        "Generates detailed scene-by-scene animation scripts."
    ),
    instruction=STORY_AGENT_INSTRUCTION,
)
