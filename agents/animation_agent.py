"""
Animation Agent -- generates complete Manim 2D animation Python code based on
the math solution and animation story, then executes it to produce a video.
"""
import os

from google.adk.agents import LlmAgent
from prompts.animation_prompts import ANIMATION_AGENT_INSTRUCTION
from tools.animation_runner import run_manim_animation, list_animations

# Placeholders resolved from ADK session state at runtime:
#   {math_solution}   -> set by math_solver_agent  (output_key="math_solution")
#   {animation_story} -> set by story_agent         (output_key="animation_story")
_ANIMATION_PREAMBLE = """\
INPUTS FROM PIPELINE (injected from session state):

MATH SOLUTION:
---
{math_solution}
---

ANIMATION STORY:
---
{animation_story}
---

Use the math solution and animation story above to generate the Manim animation.
If either block appears empty, check the conversation history for the content.

"""

ANIMATION_AGENT_FULL_INSTRUCTION = (
    _ANIMATION_PREAMBLE
    + ANIMATION_AGENT_INSTRUCTION
    + """

## Execution Workflow

1. **Receive** the math solution and animation story from the INPUTS block at the top of this instruction
2. **Plan** the animation: map each story scene to Manim code blocks
3. **Write** the complete Manim Python script:
   - Class: `MathAnimationScene(Scene)`
   - Import: `from manim import *`
   - Implement all story scenes within `construct(self)`
4. **Call** `run_manim_animation` tool with ALL FOUR parameters:
   - `manim_code`: the complete Python script as a string
   - `problem_slug`: a short slug derived from the question (no spaces, max 30 chars)
   - `question`: the exact original math/physics question (copy it verbatim)
   - `solution_text`: the full step-by-step solution text (copy the complete solution from INPUTS above)
   CRITICAL: Always pass `question` and `solution_text`. These enable an automatic
   guaranteed fallback video if your creative script has any runtime errors.
5. **Report** the result:
   - If `status == 'success'` and message contains `[FALLBACK VIDEO]`: a clean text-based
     solution animation was auto-generated because the creative script failed. Report the
     video path to the user with a note that the solution is fully visible, then attempt
     one more retry with fixed creative code if the error is clear.
   - If `status == 'success'` with no `[FALLBACK VIDEO]`: the creative animation succeeded.
     Report the video_path, script_path, and what was animated.
   - If `status == 'error'`: read the message and retry (see Retry Logic below).

## Animation Quality Checklist (before calling run_manim_animation)
- [ ] `from manim import *` AND `from manim.utils.rate_functions import ease_out_bounce` at top
- [ ] `import math as _math` AND `import numpy as np` at top
- [ ] Class is `MathAnimationScene(Scene)`
- [ ] `construct(self)` method is defined
- [ ] **NO** `MathTex`, **NO** `Tex`, **NO** `include_numbers=True` -- use `Text()` with Unicode
- [ ] **VARIABLE GUARD**: scan construct() top-to-bottom -- every name you USE must have been ASSIGNED on an earlier line. E.g. if you write `label.move_to(r_part)`, check `r_part = ...` exists above it. Missing assignments are the #1 cause of NameError crashes.
- [ ] **INDEX GUARD**: before writing `group[N]`, count the elements added to `group` -- it must have at least N+1 items. `IndexError: list index out of range` is the #2 cause of crashes.
- [ ] **NO funky/joke code comments** -- only short functional section headers like `# --- Act 1 ---`
- [ ] **NO code variable names or debug text in any Text() object on screen**
- [ ] Domain-correct visualization: incline+rolling sphere for physics, axes for calculus, shapes for geometry
- [ ] Physics: sphere PHYSICALLY MOVES with roll_sphere(); force arrows in RED/GREEN_C/ORANGE/YELLOW
- [ ] Physics: force arrow labels each placed with next_to(arrow.get_end(), direction, buff=0.12)
- [ ] Physics: incline shifted LEFT*1.5 so right half of screen is free for equations
- [ ] Physics: equations colour-coded to match their force arrow colour
- [ ] Physics: energy bars animate from zero (BLUE_C=KE_trans, TEAL=KE_rot, ORANGE=PE)
- [ ] Gradient background added first; every title/equation uses `.set_color_by_gradient()`
- [ ] Characters at screen EDGES ONLY (x < -4.5 LEFT or x > 4.5 RIGHT) -- NEVER over equations
- [ ] Physics character: scale=0.55, pinned at x > 5.5 or x < -5.5
- [ ] Layout: Title at y > 3.0, equations at centre, characters at edges
- [ ] `FadeOut(Group(*self.mobjects))` between acts -- **never** `VGroup(*self.mobjects)`
- [ ] At least 2 amusing moments (panic wiggle, wrong-answer crash, happy jump)
- [ ] Confetti + Flash + gold SurroundingRectangle at the final answer reveal
- [ ] Total estimated animation time is 60-120 seconds
- [ ] Ends with the FINAL ANSWER in rainbow gradient, clearly displayed and boxed in gold

## Retry Logic -- MANDATORY on error
If `run_manim_animation` returns `status == 'error'`:
1. Read the `message` field -- it contains the EXACT error line and a code snippet showing where it crashed.
2. Identify the root cause from the error type:
   - `NameError: name 'X' is not defined` -> find where `X` is first USED, add `X = ORIGIN` (or the correct Manim object) BEFORE that line. Do not remove the usage -- fix the missing definition.
   - `IndexError: list index out of range` -> a VGroup/list has fewer elements than you're accessing. Either add more elements to the group before that line, or reduce the index. Check how many `.add()` calls or list items precede the subscript.
   - `TypeError: Mobject.__init__() got an unexpected keyword argument 'corner_radius'` -> replace with `RoundedRectangle(..., corner_radius=...)`.
   - `AttributeError: ... has no attribute 'rotate'` -> replace `DIRECTION.copy().rotate(a)` with `np.array([np.cos(a), np.sin(a), 0])`
   - `TypeError: getter() takes 1 positional argument` -> you used a MathTex method on a Text/Mobject -- rewrite using Transform between two Text objects
   - `AttributeError: 'NoneType'` -> a variable was assigned from a forbidden method -- remove and rewrite
   - Any other error -> fix the specific lines shown in the code snippet
3. Fix ONLY the broken section. Keep all other animations intact.
4. Call `run_manim_animation` again with the corrected full script AND with `question` and `solution_text` again.
5. Repeat up to **3** total attempts. Never report failure without attempting all 3.

## ABSOLUTE GUARANTEE -- You must ALWAYS deliver a video
The `run_manim_animation` tool has a built-in auto-fallback: if your creative script fails
AND you supplied `solution_text`, the system automatically renders a clean text-based
animation showing the full solution. This means `status == 'success'` will be returned
almost always. Your job is to maximise creative quality; the system guarantees delivery.

NEVER tell the user "no video was produced" without first verifying that:
- You have called `run_manim_animation` at least once
- You passed both `question=` and `solution_text=` in that call
If you did both and still got `status == 'error'`, retry up to 3 times as described above.
"""
)


animation_agent = LlmAgent(
    name="animation_agent",
    # gemini-2.5-pro is required: complex Manim code generation fails with flash
    # (undefined variables, IndexError, wrong API calls → render failures + retries)
    # Switching to flash saves ~60s on LLM but costs 8+ min extra on render retries.
    model=os.getenv("ANIMATION_MODEL", "gemini-2.5-pro"),
    description=(
        "Elite Manim 2D animation code generator for math AND physics problems. "
        "Handles all math domains (algebra, calculus, geometry, statistics, trigonometry) "
        "AND physics domains (kinematics, forces, rolling/rotation, energy, optics, circuits). "
        "For physics problems, uses built-in helpers: make_incline(), make_sphere_on_incline(), "
        "roll_sphere(), make_force_arrows(), make_energy_bars(). "
        "Takes a solution and animation story, writes complete executable Manim Python code, "
        "and runs it to produce a beautiful 2D animation video."
    ),
    instruction=ANIMATION_AGENT_FULL_INSTRUCTION,
    tools=[
        run_manim_animation,
        list_animations,
    ],
)
