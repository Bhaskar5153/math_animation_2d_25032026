"""
Animation Agent — generates complete Manim 2D animation Python code based on
the math solution and animation story, then executes it to produce a video.
"""
from google.adk.agents import LlmAgent
from prompts.animation_prompts import ANIMATION_AGENT_INSTRUCTION
from tools.animation_runner import run_manim_animation, list_animations


ANIMATION_AGENT_FULL_INSTRUCTION = (
    ANIMATION_AGENT_INSTRUCTION
    + """

## Execution Workflow

1. **Receive** the math question, step-by-step solution, and animation story
2. **Plan** the animation: map each story scene to Manim code blocks
3. **Write** the complete Manim Python script:
   - Class: `MathAnimationScene(Scene)`
   - Import: `from manim import *`
   - Implement all story scenes within `construct(self)`
4. **Call** `run_manim_animation` tool with:
   - `manim_code`: the complete Python script as a string
   - `problem_slug`: a short slug derived from the question (no spaces, max 30 chars)
5. **Report** the result:
   - If success: video_path, script_path, and a description of what was animated
   - If error: the error message AND a corrected version of the code

## Animation Quality Checklist (before calling run_manim_animation)
- [ ] `from manim import *` at the top
- [ ] Class is `MathAnimationScene(Scene)`
- [ ] `construct(self)` method is defined
- [ ] All MathTex strings use raw strings: `MathTex(r"...")`
- [ ] No undefined variables or missing imports
- [ ] Animation covers: intro, each solution step, answer reveal, outro
- [ ] At least one fun/creative element from the story is included
- [ ] Total estimated animation time is 30-90 seconds
- [ ] Uses color coding consistently
- [ ] Ends with the FINAL ANSWER clearly displayed

## Retry Logic
If the first render fails (status == 'error'):
1. Read the stderr/stdout from the result
2. Fix the identified errors in the code
3. Call `run_manim_animation` again with the corrected code
4. Try up to 2 additional times before reporting failure
"""
)


animation_agent = LlmAgent(
    name="animation_agent",
    model="gemini-2.5-pro",
    description=(
        "Elite Manim 2D animation code generator. Takes a math solution and animation "
        "story, writes complete executable Manim Python code, and runs it to produce "
        "a beautiful 2D math animation video."
    ),
    instruction=ANIMATION_AGENT_FULL_INSTRUCTION,
    tools=[
        run_manim_animation,
        list_animations,
    ],
)
