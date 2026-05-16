"""
Story Agent -- transforms math solutions into real-world discovery narratives
that show students where this math actually lives and who first used it.
"""
from google.adk.agents import LlmAgent

from config import models
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
    model=models.fast,
    description=(
        "Mathematical visual scene planner. Reads the math solution and produces a "
        "precise 3-scene animation plan: pure math visualization on black background, "
        "vibrant curves and shapes, step-by-step equations. No stories, no characters, "
        "no real-world metaphors. Mathematisa-style dark elegance."
    ),
    instruction=_STORY_PREAMBLE + STORY_AGENT_INSTRUCTION,
    # Store the scene plan in session state so animation_agent reads it via {animation_story}.
    output_key="animation_story",
)
