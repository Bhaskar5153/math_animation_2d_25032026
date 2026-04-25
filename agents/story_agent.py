"""
Story Agent -- transforms math solutions into creative, funny, and engaging
animation stories that bring math to life for students.
"""
import os

from google.adk.agents import LlmAgent
from prompts.story_prompts import STORY_AGENT_INSTRUCTION

# Preamble injected at runtime: {math_solution} is resolved from session state
# (stored by math_solver_agent via output_key="math_solution").
_STORY_PREAMBLE = """\
MATH SOLUTION (provided by the math solver -- use this as the basis for your story):
---
{math_solution}
---

Now create the animation story following all rules below.

"""

story_agent = LlmAgent(
    name="story_agent",
    model=os.getenv("FAST_MODEL", "gemini-2.5-flash"),
    description=(
        "Creative animation story generator that transforms dry math solutions into "
        "captivating, funny, and visually memorable 5-act stories for 2D animation. "
        "Generates detailed scene-by-scene animation scripts."
    ),
    instruction=_STORY_PREAMBLE + STORY_AGENT_INSTRUCTION,
    # Store the story in session state so animation_agent reads it via {animation_story}.
    output_key="animation_story",
)
