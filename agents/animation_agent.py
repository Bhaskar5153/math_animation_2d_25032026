"""
Animation Agent -- generates complete Manim 2D animation Python code based on
the math solution and animation story, then executes it to produce a video.
"""
from google.adk.agents import LlmAgent

from config import models
from prompts.animation_prompts import ANIMATION_AGENT_INSTRUCTION
from tools.animation_runner import run_manim_animation, list_animations

# Placeholders resolved from ADK session state at runtime:
#   {math_solution}   -> set by math_solver_agent  (output_key="math_solution")
#   {animation_story} -> set by story_agent         (output_key="animation_story")
_ANIMATION_PREAMBLE = """\
==============================================================================
YOUR ONLY JOB: Call run_manim_animation with the Manim code.
==============================================================================
Do NOT output the Python code as a text message. Do NOT explain what you will do.
Write the code INTERNALLY, then IMMEDIATELY call run_manim_animation with it.

The pipeline works as follows:
  1. Read MATH SOLUTION and ANIMATION STORY below.
  2. Write the complete Manim Python script (class MathAnimationScene).
  3. Call run_manim_animation — pass ALL FIVE parameters: manim_code, problem_slug,
     question, solution_text, narration_script.
  4. After the tool returns, report what was produced.

If you output the code as text and stop WITHOUT calling run_manim_animation,
no video will be produced and the student gets nothing. Always call the tool.
==============================================================================

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
4. **Call** `run_manim_animation` tool with ALL FIVE parameters:
   - `manim_code`: the complete Python script as a string
   - `problem_slug`: a short slug derived from the question (no spaces, max 30 chars)
   - `question`: the exact original math/physics question (copy it verbatim)
   - `solution_text`: the full step-by-step solution text (copy the complete solution from INPUTS above)
   - `narration_script`: the full ANIMATION STORY text (copy it verbatim from INPUTS above)
   CRITICAL: Always pass `question`, `solution_text`, and `narration_script`. The narration_script
   makes the audio sound like the story characters are talking, not reading equations.
   solution_text enables the automatic guaranteed fallback video if your creative script fails.

   ⚠ MANDATORY: Step 4 is a FUNCTION CALL, not text output. Your next action after
   writing the code must be the run_manim_animation function call. If you write the
   code as a text block and stop, NO video is produced and the student gets nothing.
   Do NOT say "Here is the code:" and stop. ALWAYS call the tool.

5. **Report** the result:
   - If `status == 'success'` and message contains `[FALLBACK VIDEO]`: a clean text-based
     solution animation was auto-generated because the creative script failed. Report the
     video path to the user with a note that the full step-by-step solution is visible.
     Do NOT retry -- the student has a complete, working video. Present it immediately.
   - If `status == 'success'` with no `[FALLBACK VIDEO]`: the creative animation succeeded.
     Report the video_path, script_path, and what was animated.
   - If `status == 'error'`: read the message and retry (see Retry Logic below).

## Animation Quality Checklist (before calling run_manim_animation)
- [ ] `from manim import *` AND `from manim.utils.rate_functions import ease_out_bounce` at top
- [ ] `import math as _math` AND `import numpy as np` at top
- [ ] Class is `MathAnimationScene(Scene)`
- [ ] `construct(self)` method is defined
- [ ] **NO** `MathTex`, **NO** `Tex`, **NO** `include_numbers=True` -- use `Text()` with Unicode
- [ ] **NO SUBSCRIPT BOXES**: NEVER create a separate small Text object inside a colored SurroundingRectangle to simulate subscripts -- this produces orange/red boxes on screen. Write subscripts inline as `Text("a_c = 8 m/s²")` -- underscore notation in the SAME string.
- [ ] **NO Unicode subscripts**: NEVER use ₀₁₂₃ₙᵢₓ etc. in Text() -- they render as colored boxes. Write `Text("v_0")` not `Text("v₀")`.
- [ ] Characters use `make_human(shirt_color=..., emotion=..., pose=...)` NOT `make_emoji()` -- emoji look like yellow blobs.
- [ ] `pose=` matches the story moment: "thinking" (pondering), "excited" (eureka), "explaining" (pointing), "neutral" (resting). CHANGE pose between acts so body language tells the story.
- [ ] Physics / projectile / sports problems: athlete character uses `make_athlete(shirt_color=BLUE_C, scale=0.6)` at FAR LEFT -- NOT a plain human or emoji.
- [ ] `make_human()` parameters are `shirt_color=`, `emotion=`, `pose=` -- all three are available.
- [ ] construct() ends with `self.wait(3.0)` as the VERY LAST line -- required for audio sync.
- [ ] **VARIABLE GUARD**: scan construct() top-to-bottom -- every name you USE must have been ASSIGNED on an earlier line. E.g. if you write `label.move_to(r_part)`, check `r_part = ...` exists above it. Missing assignments are the #1 cause of NameError crashes.
- [ ] **INDEX GUARD**: before writing `group[N]`, count the elements added to `group` -- it must have at least N+1 items. `IndexError: list index out of range` is the #2 cause of crashes.
- [ ] **NO funky/joke code comments** -- only short functional section headers like `# --- Act 1 ---`
- [ ] **NO code variable names or debug text in any Text() object on screen**
- [ ] Domain-correct visualization: incline+rolling sphere for physics, axes for calculus, shapes for geometry
- [ ] Binomial Theorem / Combinations checklist (if problem asks for coefficient of x^r):
  - [ ] Use the BINOMIAL THEOREM SCATTER-LINE code helper from Step 2 -- NOT bars/Rectangles
  - [ ] x-axis = INTEGER k values ONLY (0,1,...,n). NO fractional ticks (set include_ticks=False)
  - [ ] Add integer labels with a loop: `for k in range(n+1): Text(str(k),...).next_to(axes.c2p(k,0), DOWN)`
  - [ ] Add y-axis power labels with a loop using Text, NOT include_numbers or add_coordinates
  - [ ] Dots: `Dot(axes.c2p(k, power), radius=0.14, color=GOLD if k==target_k else BLUE_C)`
  - [ ] Polyline: `VMobject().set_points_as_corners([axes.c2p(k,p) for k,p in zip(k_vals, x_pows)])`
  - [ ] Formula font_size=32; parameters BELOW in VGroup.arrange(RIGHT, buff=0.7) at font_size=28
  - [ ] Characters: biologist (make_human TEAL) at LEFT edge; robot at RIGHT edge
  - [ ] Biologist starts pose="thinking" (both arms move); switches to pose="excited" after answer
- [ ] Physics/Projectile MOTION checklist (if problem asks for Hmax / T / R from angled launch):
  - [ ] Stadium background: dark blue sky Rectangle + green grass Rectangle (NOT plain black bg)
  - [ ] make_athlete(shirt_color=BLUE_C, scale=0.6) at FAR LEFT edge (x < -5.5) -- NOT center; ball is the hero
  - [ ] Dashed parabolic arc via ParametricFunction + proj_pt() mapping (use PROJECTILE MOTION helper)
  - [ ] Ball animates along arc via ValueTracker t_trk (run_time=3.0, rate_func=smooth)
  - [ ] Three velocity vectors at launch: u (white diagonal), ux (teal horizontal), uy (orange vertical)
  - [ ] Dashed vertical line at peak + "Hmax" label + "vy=0 at peak" label
  - [ ] Flash() on landing; three gold answer boxes side by side: Hmax | T | R
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
5. Repeat up to **1** retry (2 total attempts maximum). If the second attempt also fails,
   the system's automatic fallback guarantees a video — report it and stop. Do NOT attempt
   a third cycle; it wastes minutes and the student already has a working video.

## ABSOLUTE GUARANTEE -- You must ALWAYS deliver a video
The `run_manim_animation` tool has a built-in auto-fallback: if your creative script fails
AND you supplied `solution_text`, the system automatically renders a clean text-based
animation showing the full solution. This means `status == 'success'` will be returned
almost always. Your job is to maximise creative quality; the system guarantees delivery.

NEVER tell the user "no video was produced" without first verifying that:
- You have called `run_manim_animation` at least once
- You passed both `question=` and `solution_text=` in that call
If you did both and still got `status == 'error'`, try once more with the corrected script,
then accept whatever the system delivers. Never exceed 2 total attempts.

==============================================================================
REMINDER: Your FIRST action must be to call run_manim_animation.
DO NOT output the Manim code as a text block. DO NOT explain the code first.
Write it internally → call the tool → THEN report the result.
A text-only response with no tool call = no video for the student.
==============================================================================
"""
)


animation_agent = LlmAgent(
    name="animation_agent",
    # gemini-2.5-pro is required: complex Manim code generation fails with flash
    # (undefined variables, IndexError, wrong API calls → render failures + retries)
    # Switching to flash saves ~60s on LLM but costs 8+ min extra on render retries.
    model=models.animation,
    description=(
        "Generates and EXECUTES Manim 2D animation code by calling run_manim_animation. "
        "Handles all math domains (algebra, calculus, geometry, statistics, trigonometry) "
        "AND physics domains (kinematics, forces, rolling/rotation, energy, optics, circuits). "
        "ALWAYS calls run_manim_animation — never outputs code as text and stops. "
        "Takes a solution and animation story, writes executable Manim Python code, "
        "calls run_manim_animation to render it, and reports the produced video path."
    ),
    instruction=ANIMATION_AGENT_FULL_INSTRUCTION,
    tools=[
        run_manim_animation,
        list_animations,
    ],
)
