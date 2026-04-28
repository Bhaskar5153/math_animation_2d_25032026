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
        "Discovery narrative generator that connects math solutions to real-world "
        "applications — showing the scientist who discovered it, where it's used today, "
        "and how the answer maps back to a concrete real-world outcome. Generates "
        "cinematic 5-act scene-by-scene animation scripts for the animation agent."
    ),
    instruction=_STORY_PREAMBLE + STORY_AGENT_INSTRUCTION,
    # Store the story in session state so animation_agent reads it via {animation_story}.
    output_key="animation_story",
)
