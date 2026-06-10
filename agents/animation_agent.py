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

==============================================================================
CRITICAL — ANIMATE ONLY THE EXACT PROBLEM GIVEN (violations produce wrong answers)
==============================================================================
Every value, expression, variable, and equation in your animation MUST be taken
VERBATIM from the MATH SOLUTION block above. No exceptions.

FORBIDDEN (using generic textbook placeholder values):
  • Problem says "find x" but animation shows "find AE = 2.1 cm"
  • Problem says "AL = x-3, AC = 2x" but animation shows "AD/DB = 3/5, AC = 5.6"
  • Problem has algebraic expressions but animation uses random numeric values
  • Animation solves a completely different question than what was asked

REQUIRED (use actual problem values):
  • If MATH SOLUTION says AL = x-3, AC = 2x, BM = x-2, BC = 2x+3 → animate THOSE exact expressions
  • If MATH SOLUTION derives x = 9 → final answer MUST show x = 9, not 2.1 or any other value
  • Copy every label, value, and variable name character-for-character from the solution

"""

ANIMATION_AGENT_FULL_INSTRUCTION = (
    _ANIMATION_PREAMBLE
    + ANIMATION_AGENT_INSTRUCTION
    + """

## Execution Workflow

1. **Receive** the math solution and animation story from the INPUTS block at the top of this instruction
2. **Plan** the animation: map each story scene to Manim code blocks
3. **Write** the complete Manim Python script:
   - Class: `MathAnimationScene(Scene)` for 2D animations (default)
     OR     `MathAnimationScene(ThreeDScene)` for 3D surface plots ONLY
     PREFER ThreeDScene ONLY when: problem has 3 variables (x,y,z) AND a surface/plane
     visualization is essential. Examples:
       - "find xy+yz+zx given x+y+z=6, x²+y²+z²=14" → 3D sphere + plane
       - "find critical points of f(x,y)=x²+y²" → 3D surface plot
     FORBIDDEN from ThreeDScene (use isometric 2D Scene instead):
       - Volume / surface area of cone, sphere, cylinder, cube (→ GEOMETRY TYPE 7)
       - Volume conservation: "cone reshaped into sphere", "melted/recast" (→ GEOMETRY TYPE 11)
       - Hollow hemisphere → cylinder: "hollow hemispherical shell", "internal/external diameter" (→ GEOMETRY TYPE 12)
       - BPT / similar triangles (→ GEOMETRY TYPE 10)
       - Any problem where shapes can be drawn as 2D isometric solids
     Use 2D Scene for: single-variable equations, proofs/identities, polynomials,
     inequalities, calculus, trig, geometry — these are better as 2D plots.
   - Import: `from manim import *`
   - Implement all story scenes within `construct(self)`
4. **Call** `run_manim_animation` tool with ALL FIVE parameters:
   - `manim_code`: the complete Python script as a string
   - `problem_slug`: a short slug derived from the question (no spaces, max 30 chars)
   - `question`: the exact original math/physics question (copy it verbatim)
   - `solution_text`: the full step-by-step solution text (copy the complete solution from INPUTS above)
   - `narration_script`: ONLY the sentences from the **NARRATION SCRIPT** section of the
     ANIMATION STORY. Extract those 4-6 sentences only. Do NOT copy scene plans, visual
     descriptions, colors, font sizes, or Manim object names — those must NOT appear in
     the audio. The narration must sound like a teacher explaining math at a chalkboard,
     not a script reader describing screen elements.
   CRITICAL: Always pass `question`, `solution_text`, and `narration_script`. The narration_script
   is spoken aloud over the video — it must contain only plain teaching sentences.
   solution_text enables the automatic guaranteed fallback video if your creative script fails.

   ⚠ MANDATORY: Step 4 is a FUNCTION CALL, not text output. Your next action after
   writing the code must be the run_manim_animation function call. If you write the
   code as a text block and stop, NO video is produced and the student gets nothing.
   Do NOT say "Here is the code:" and stop. ALWAYS call the tool.

5. **Report** the result:
   - If `status == 'success'` and the `message` field contains `[FALLBACK VIDEO]`:
     the creative script failed but the system **automatically produced** a 2D visual
     animation (diagram + solution steps). Report the `video_path` to the user.
     **Do NOT retry** — the student already has a working visual video.
   - If `status == 'success'` (no FALLBACK tag): the creative animation succeeded.
     Report the `video_path`, `script_path`, and what was animated.
   - If `status == 'error'`: read the `message` field and retry (see Retry Logic below).
   - When retrying after `status == 'error'`: always fix the specific error before
     calling `run_manim_animation` again. Never retry without making a concrete fix.

## Animation Quality Checklist (before calling run_manim_animation)
- [ ] `from manim import *` AND `from manim.utils.rate_functions import ease_out_bounce` at top
- [ ] `import math as _math` AND `import numpy as np` at top
- [ ] Class is `MathAnimationScene(Scene)` for 2D, OR `MathAnimationScene(ThreeDScene)` for 3D
- [ ] **SCREEN SPLIT (MANDATORY for all 2D scenes with Axes)**:
  - [ ] Axes MUST use `axes.shift(LEFT*2.5 + DOWN*0.3)` — NEVER leave axes centered at ORIGIN
  - [ ] Equation steps MUST use `eq_stack.move_to(RIGHT*2.8 + UP*Y)` — NEVER at ORIGIN or LEFT
  - [ ] Verify: axes.get_right() < 0.5 (plot stays LEFT) AND eq_stack.get_left() > 0.5 (steps stay RIGHT)
- [ ] **3D SCENE (if ThreeDScene)**:
  - [ ] `self.set_camera_orientation(phi=70*DEGREES, theta=-50*DEGREES)` at the start of construct()
  - [ ] ALL Text() MUST be added with `self.add_fixed_in_frame_mobjects(text)` — without this, text
        rotates with the camera and becomes a blurry spinning mess
  - [ ] Pattern: `title.to_corner(UL); self.add_fixed_in_frame_mobjects(title)`
  - [ ] `self.begin_ambient_camera_rotation(rate=0.08)` for smooth auto-rotation
  - [ ] Use Surface() for 3D plots, ThreeDAxes for axes
  - [ ] If ThreeDScene fails on retry: switch to Scene (2D) with LEFT=plot, RIGHT=steps
- [ ] `construct(self)` method is defined
- [ ] **NO** `MathTex`, **NO** `Tex`, **NO** `include_numbers=True` -- use `Text()` with Unicode
- [ ] **NO `TransformMatchingTex`** and **NO `TransformMatchingShapes`** -- use `Transform(obj1, obj2)` instead. These require MathTex objects; using them with Text crashes the render.
- [ ] **NO SUBSCRIPT BOXES**: NEVER create a separate small Text object inside a colored SurroundingRectangle to simulate subscripts -- this produces orange/red boxes on screen. Write subscripts inline as `Text("a_c = 8 m/s²")` -- underscore notation in the SAME string.
- [ ] **NO Unicode subscripts**: NEVER use ₀₁₂₃ₙᵢₓ etc. in Text() -- they render as colored boxes. Write `Text("v_0")` not `Text("v₀")`.
- [ ] **NO Unicode arrows or logic symbols**: NEVER use ⟹ ⇒ → ∴ ∵ ∀ ∃ in Text() -- they render as □ boxes on most systems. Use plain ASCII equivalents: `"=>"`, `"->"`, `"therefore"`, `"implies"`. The ONLY safe Unicode in Text() is standard superscripts ² ³ and the ≥ ≤ ± symbols.
- [ ] Characters use `make_human(shirt_color=..., emotion=..., pose=...)` NOT `make_emoji()` -- emoji look like yellow blobs.
- [ ] `pose=` matches the story moment: "thinking" (pondering), "excited" (eureka), "explaining" (pointing), "neutral" (resting). CHANGE pose between acts so body language tells the story.
- [ ] Physics / projectile / sports problems: athlete character uses `make_athlete(shirt_color=BLUE_C, scale=0.6)` at FAR LEFT -- NOT a plain human or emoji.
- [ ] `make_human()` parameters are `shirt_color=`, `emotion=`, `pose=` -- all three are available.
- [ ] **ANIMATION LENGTH + AUDIO SYNC (critical — violations cause render timeouts)**:
  TARGET: total animation ≤ 35 seconds. At 720p30, 1s animation = ~5s render.
  35s animation → ~175s render (fits in timeout). 50s animation → ~250s (times out).
  HARD WAIT CAPS (never exceed these):
    - Title intro:                          self.wait(0.5)  max
    - After problem statement (given+find): self.wait(1.5)  max  (NOT 3.5)
    - After each visual element (axes, curve, shape): self.wait(1.0)  max  (NOT 2.5)
    - After each algebra step written: self.wait(1.0)  max  (NOT 2.0)
    - After final answer reveal (LAST LINE): self.wait(2.0)  max  (NOT 8.0)
  FORBIDDEN: self.wait(2.5) / self.wait(3.0) / self.wait(4.0) / self.wait(5.0) / self.wait(8.0)
  Rule of thumb: count all self.wait() values and sum them. Total must be ≤ 25s.
  (The remaining 10s comes from play() run_times.)
- [ ] **Line() takes EXACTLY 2 points**: `Line(start, end)` ONLY. NEVER `Line(p1, p2, p3)` -- passing 3 points crashes with `ValueError: truth value of array`. Use `Polygon(p1, p2, p3)` for triangles.
- [ ] **VARIABLE GUARD**: scan construct() top-to-bottom -- every name you USE must have been ASSIGNED on an earlier line. E.g. if you write `label.move_to(r_part)`, check `r_part = ...` exists above it. Missing assignments are the #1 cause of NameError crashes.
- [ ] **INDEX GUARD**: before writing `group[N]`, count the elements added to `group` -- it must have at least N+1 items. `IndexError: list index out of range` is the #2 cause of crashes.
- [ ] **NO funky/joke code comments** -- only short functional section headers like `# --- Act 1 ---`
- [ ] **NEVER `self.add(self.camera.background_color)`**: This crashes Manim with `AttributeError: 'ManimColor' object has no attribute 'submobjects'`. To restore a black background between acts: define `bg = Rectangle(width=16, height=9, fill_color=BLACK, fill_opacity=1)` at the VERY TOP of construct(), then after FadeOut use `self.add(bg.copy())`. Never pass a color object to self.add().
- [ ] **NO code variable names or debug text in any Text() object on screen**
- [ ] **VALUE SUBSTITUTION — make the math LIVE on screen**:
  When substituting a known value into an equation, do NOT just write the next equation silently.
  Show the substitution happening:
    1. Write the identity/equation first, then self.wait(1.0)
    2. Write the substituted form (e.g. "(6)^2 = ..."), then self.wait(1.0)
    3. Use Circumscribe(equation, color=TEAL) or Indicate(plot_element) to visually highlight
       what changed — connects the plot on the LEFT to the algebra on the RIGHT.
    4. Each algebra step MUST have its own self.play(Write(step)) + self.wait(1.0).
       NEVER write all steps in a single loop with no waits — the animation will flash past.
  Example: after writing step "(6)^2 = 14 + 2(xy+yz+zx)", call Indicate(constraint_line)
  to show the viewer WHY 6 appears there.
- [ ] Domain-correct visualization: incline+rolling sphere for physics, axes for calculus, shapes for geometry
- [ ] **POLYNOMIAL ROOTS / VIETA'S FORMULAS** — if problem names polynomial roots (α,β,γ or a,b,c) and asks to COMPUTE any expression from them:
  - [ ] !! NEVER produce text-only (listing σ1/σ2/σ3 as plain text) — this is the MOST COMMON failure mode for this problem type !!
  - [ ] LEFT HALF: plot the polynomial curve using axes.plot(). axes.shift(LEFT*2.5 + DOWN*0.3) MANDATORY.
  - [ ] THREE GOLD Dots at the root positions on the x-axis (Dot(axes.c2p(root, 0), color=GOLD)).
  - [ ] DashedLine from bottom to each root + label "alpha=1" / "beta=2" / "gamma=-3".
  - [ ] Flash each GOLD dot in sequence after plotting.
  - [ ] RIGHT HALF: Vieta's formulas (s1/s2/s3) one at a time, then substitution steps.
  - [ ] Indicate(root_dots) when writing Vieta's to connect the plot to the algebra.
  - [ ] Use the POLYNOMIAL ROOTS code helper. Adapt poly() function and root values to the actual problem.
  - [ ] Curve: `axes.plot(lambda x: max(-14.5, min(poly(x), 14.5)), ...)` — clipped to axes range.
  - [ ] For 3D: this problem does NOT benefit from ThreeDScene — use 2D Scene always.
- [ ] **DIOPHANTINE EQUATION / INTEGER SOLUTIONS** — HIGHEST PRIORITY CHECK:
  !! READ THIS BEFORE WRITING ANY CODE for "solve in integers", "find integer solutions",
  !! "prove only x=y=z=0 satisfies", "no non-trivial integer solution" problems. !!
  - [ ] **MANDATORY LEFT-HALF PLOT**: The animation MUST have `Axes()` with integer grid dots,
        even if the story plan does not mention a plot. If the story plan is text-only, ADD
        the 2D axes grid YOURSELF — it is non-negotiable for this problem type.
  - [ ] Scene MUST use regular `Scene` (NOT ThreeDScene).
  - [ ] LEFT HALF (MANDATORY, NO EXCEPTIONS):
        axes = Axes(x_range=[-4,4,1], y_range=[-4,4,1], x_length=5.5, y_length=5.5,
                    axis_config={"color": GRAY_A, "include_ticks": False})
        axes.shift(LEFT*2.5 + DOWN*0.3)
        PARITY GRID: nested loop over xi in range(-3,4), yi in range(-3,4):
          BLUE_C dot (radius=0.10) if xi%2==0 and yi%2==0 (both even = "candidate" zone)
          GRAY_B dot (radius=0.07) otherwise (parity contradiction)
        GOLD Dot at (0,0) radius=0.22 + label "only solution" + Flash(origin_dot).
  - [ ] RIGHT HALF: parity argument steps + descent step. VGroup.arrange(DOWN,buff=0.30).move_to(RIGHT*2.8+UP*0.3).
        Include: "RHS=2xyz is even" → "LHS ≡ 2 (mod 4) if any var odd" → "Contradiction"
        → "All must be even" → "x=2x_1 gives same equation → divisible by 2^k → x=y=z=0"
  - [ ] Use the DIOPHANTINE EQUATION code helper from Step 2 for the grid loop and axes setup.
  - [ ] Scene 3: "x = y = z = 0" font_size=96, YELLOW→ORANGE, gold box, Flash.
- [ ] **TRIGONOMETRY -- ALWAYS HAS A PLOT** — if problem involves sin/cos/tan, inverse trig, trig equations, or trig identities:
  - [ ] NEVER produce text-only — unit circle + trig wave curve is MANDATORY even if the story plan is text-only.
        If the story plan has no visual, ADD the unit circle and Axes graph YOURSELF — non-negotiable.
  - [ ] **TRIG LAYOUT (TYPE 1/2 — unit circle + wave)**: unit circle AND wave axes BOTH go in LEFT half.
        Circle(radius=1.2, color=CYAN).move_to(LEFT*4.5). Crosshair lines length 1.5.
        Axes(x_range=[0,2*PI,PI/2], y_range=[-1.6,1.6], x_length=4.0, y_length=3.0,
          axis_config={"color":GRAY_A,"include_ticks":False}).shift(LEFT*1.0+DOWN*0.2).
        Circle spans x=-5.7→-3.3; wave axes span x=-3.0→1.0 — together they fill LEFT half.
        Tick labels: Text("π/2"), Text("π"), Text("3π/2"), Text("2π") placed next_to(g_axes.c2p(val,0), DOWN).
        NEVER use include_numbers=True on trig axes.
  - [ ] **EQUATION STEPS (TYPE 1/2)**: MUST go on RIGHT HALF only — NEVER over the wave axes.
        VGroup.arrange(DOWN, buff=0.30, aligned_edge=LEFT).move_to(RIGHT*2.8 + UP*Y).
  - [ ] Use np.cos/np.sin in circ_pt()/graph_pt() — these are always available via `import numpy as np`.
  - [ ] TracedPath(g_dot.get_center, stroke_color=CURVE_COLOR, stroke_width=3) for the wave.
        DashedLine always_redraw connecting circle dot to graph dot as angle sweeps.
  - [ ] TRIG EQUATIONS (solve sin(x)=k): after full wave trace, draw ORANGE DashedLine at y=k.
        GOLD Dot at each solution on the wave + DashedLine vertical to x-axis + angle label.
        Mirror solution as GOLD Dot on unit circle. Flash each GOLD dot.
  - [ ] TRIG IDENTITIES ("prove sin²x+cos²x=1"): axes.shift(LEFT*2.5+DOWN*0.3) for split layout.
        CYAN curve for LHS, PURPLE curve for RHS on the SAME Axes — they overlap = visual proof.
        Mark GOLD Dot at a sample x showing coincidence. Flash it. Algebraic steps on RIGHT half.
  - [ ] Color: sin=CYAN, cos=PURPLE, tan=PINK. Title: CYAN->BLUE_B.
        Label below circle: "sin θ" / "cos θ" / "tan θ" in the curve color.
  - [ ] MAX/MIN OF TRIG EXPRESSION (find max/min of a·sinx + b·cosx):
        NEVER text-only. ALWAYS plot the combined function. Use TRIGONOMETRY TYPE 4 helper.
        axes.plot(lambda x: a*np.sin(x)+b*np.cos(x), x_range=[0,2*PI,0.02], color=CYAN).
        GREEN_C DashedLine at y=+R + GOLD Dot at peak. RED DashedLine at y=-R + ORANGE Dot at trough.
        R = np.sqrt(a**2 + b**2). NEVER try to solve for x; the answer is just Max=+R, Min=-R.
  - [ ] Use the TRIGONOMETRY code helpers from Step 2 for the unit circle + TracedPath pattern.
- [ ] **ALGEBRA IDENTITY PROOF** — if problem says "prove", "show", "verify" an algebraic identity:
  - [ ] NEVER produce text-only for proof problems — this is the most common failure mode.
  - [ ] Use the IDENTITY PROOF code helper. LEFT half = D(t) curve, RIGHT = factorization chain.
  - [ ] D(t) = LHS(t,1,1) - RHS(t,1,1) with b=c=1, a=t. For a^3+b^3+c^3=3abc: D(t)=t^3-3t+2.
  - [ ] Curve in YELLOW drawn with Create() run_time=2.5. NEVER static/add.
  - [ ] DashedLine at y=0 in GRAY_B. GOLD Dots at zeros with labels. Flash each dot.
  - [ ] Zeros of D(t): t=1 (equality case a=b=c) and t=-2 (condition a+b+c=0).
  - [ ] RIGHT HALF: factorization chain one step at a time. Circumscribe the factored form in TEAL.
  - [ ] Indicate(zero_dot2) after writing "When a+b+c=0:" to connect plot to algebra.
  - [ ] Circumscribe(final_step, GOLD) on the conclusion line.
  - [ ] self.wait(1.0) after EACH step. self.wait(2.0) on the final answer reveal.
- [ ] **THREE-VARIABLE ALGEBRA SYSTEM** — if problem gives x+y+z=S1 and x^2+y^2+z^2=S2:
  - [ ] Regular `Scene` (NOT ThreeDScene — ThreeDScene is forbidden).
  - [ ] Left half: Axes + GOLD Circle growing via GrowFromCenter() + ORANGE constraint line.
  - [ ] Centroid: cx = cy = S1/3.  Circle radius: r_int = sqrt(S2 - S1**2/3).
  - [ ] Follow the THREE-VARIABLE SYSTEM 2D AXES + CIRCLE code helper from Step 2 exactly.
  - [ ] Problem statement → visual (circle + line) → substitution steps → answer reveal.
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
- [ ] **ALGEBRA POLYNOMIALS / PERFECT SQUARE** checklist (if problem has P(x) with unknown coefficients, find a,b, polynomial factoring):
  - [ ] !! NEVER produce text-only — this is the most common failure mode. ALWAYS plot curves. !!
  - [ ] If problem is P(x)=x^4-4x^3+ax^2+bx+1: use the POLYNOMIAL TWO-CASE helper. There are EXACTLY TWO solutions: Case A (d=1, a=6, b=-4) and Case B (d=-1, a=2, b=4). Show BOTH curves.
  - [ ] Axes: x_range=[-1.0, 4.0], y_range=[-0.3, 6.0], shift LEFT*2.3+DOWN*0.3. x/y labels with loops.
  - [ ] Case A curve: `axes.plot(lambda x: min((x-1)**4, 5.9), x_range=[-0.7,3.7,0.02], color=BLUE_C)` drawn with Create(run_time=2.5). Mark Dot(GOLD) at (1,0). Flash it.
  - [ ] Case B curve: AFTER FadeOut of Case A, `axes.plot(lambda x: min((x**2-2*x-1)**2, 5.9), x_range=[-0.95,3.9,0.02], color=TEAL)`. Mark TWO Dot(GOLD) at x=1-sqrt(2) AND x=1+sqrt(2).
  - [ ] Axis labels with loops: `for xv in [-1,0,1,2,3]: Text(str(xv),...).next_to(axes.c2p(xv,0), DOWN)`.
  - [ ] RIGHT HALF: algebra steps show the factoring (c=-2, d=±1) and both cases' a/b values. VGroup.arrange(DOWN, buff=0.26).move_to(RIGHT*2.8 + UP*0.2).
  - [ ] Scene 3: Two answer boxes side by side — one for Case A, one for Case B.
  - [ ] bg defined at TOP: `bg = Rectangle(width=16, height=9, fill_color=BLACK, fill_opacity=1)`. Reset between acts with `self.play(FadeOut(Group(*self.mobjects)))` then `self.add(bg.copy())`.
- [ ] **LOGARITHMIC EQUATIONS** checklist (if problem has log, log2, log10, ln, logarithm):
  - [ ] NEVER produce text-only — ALWAYS plot the log function on LEFT half even if story plan omits it.
  - [ ] LEFT HALF (MANDATORY): Axes.shift(LEFT*2.5+DOWN*0.3). Use axes.plot(f_log, ...) in GREEN_C.
        f_log(x) returns log_b(x)+log_b(x-SHIFT). Guard: if x<=0 or (x-SHIFT)<=0: return float('nan').
  - [ ] Domain boundary: DashedLine(axes.c2p(DOM_BOUND, y_lo), axes.c2p(DOM_BOUND, y_hi), color=RED).
        Label "x > 2" in RED. NEVER shade with Line(p1,p2,p3,p4) — that crashes with ValueError.
  - [ ] RHS horizontal line: DashedLine at y=RHS_VAL in ORANGE. Label "y = RHS_VAL".
  - [ ] GOLD Dot at (SOL_X, RHS_VAL) + DashedLine vertical from (SOL_X,0) to solution. Flash it.
  - [ ] RIGHT HALF: algebra steps: domain → "log_b(x(x-a))=c" → "x(x-a)=b^c" → quadratic →
        reject extraneous (negative or out-of-domain root). VGroup.move_to(RIGHT*2.8+UP*0.3).
  - [ ] Title gradient: TEAL→GREEN_C. Use the LOGARITHMIC EQUATIONS code helper from Step 2.
  - [ ] ABSOLUTE CRASH PREVENTION: Line() takes EXACTLY 2 points. For any region highlight
        use DashedLine (boundary only) or Polygon(p1,p2,p3,p4) — NEVER Line with 3+ points.
- [ ] **ALGEBRA RADICAL EQUATIONS** checklist (if problem has sqrt(...) = constant, nested radicals, solve for x):
  - [ ] **NEVER show a NumberLine with "x >= [domain bound]" as the answer.** That is only the DOMAIN, not the solution. The SOLUTION is a specific number (e.g. x = 11/4).
  - [ ] LEFT HALF: plot f(x) using the RADICAL EQUATION helper. For nested radicals, derive the simplified form first: e.g. sqrt(x+sqrt(2x-1))+sqrt(x-sqrt(2x-1)) = sqrt(2) for x in [0.5,1] and sqrt(4x-2) for x>1.
  - [ ] Draw TWO segments: `Line(axes.c2p(0.5, sqrt2), axes.c2p(1.0, sqrt2), color=BLUE_C)` for flat part; `axes.plot(lambda x: sqrt(4*x-2), x_range=[1.0, 4.95, 0.02], color=BLUE_C)` for growing part.
  - [ ] Draw RHS horizontal line in ORANGE: `Line(axes.c2p(0.4, rhs), axes.c2p(5.0, rhs), color=ORANGE)`.
  - [ ] Mark the SOLUTION (not the domain): `Dot(axes.c2p(sol_x, rhs), radius=0.18, color=GOLD)` + DashedLine vertical + Text("x = 11/4") below.
  - [ ] RIGHT HALF: algebraic derivation with u/v substitution. VGroup.arrange(DOWN, buff=0.32).move_to(RIGHT*2.8 + UP*0.4).
  - [ ] Scene 3: final answer "x = 11/4" (or exact value), font_size=96, gold box. Include a one-line verification.
- [ ] **ALGEBRA INEQUALITIES** checklist (if problem asks to "prove X >= Y", inequality with abc=1 or similar constraint):
  - [ ] NEVER produce a pure-text animation for inequality proofs — ALWAYS include a 1-variable function plot from the INEQUALITY PROOF helper.
  - [ ] LEFT HALF: plot the LHS as a function of one variable t by fixing the others (e.g. b=c=1, a=t, with abc=1 so c=1/t). Axes x_range=[0.3, 3.0], y_range=[0, 30]. x_length=5.5, y_length=5.0.
  - [ ] CURVE: `axes.plot(S_func, x_range=[0.32, 2.98, 0.02], color=YELLOW, stroke_width=3)` drawn with Create() run_time=2.5 — NEVER static.
  - [ ] Mark minimum: `Dot(GREEN_C)` at equality point + DashedLine horizontal + DashedLine vertical + "a=b=c=1" label.
  - [ ] AXIS LABELS: x and y integer/decimal labels with loops. x-axis label describes the parametrization.
  - [ ] RIGHT HALF: AM-GM step chain using ASCII `"=>"` not unicode `"⟹"`. VGroup.arrange(DOWN, buff=0.35).move_to(RIGHT*2.8 + UP*0.3).
  - [ ] `"=>"` for implication, `">="` for inequality — NEVER use ⟹ → ≥ as standalone Unicode text (they box).
  - [ ] Scene 2: FadeOut problem_group from bottom first, THEN mark minimum, THEN show equations.
  - [ ] Animation has axes + curve + marks — total Manim objects should be < 30 to avoid slow renders.
- [ ] **CALCULUS DERIVATIVES** checklist (if problem asks for dy/dx, f'(x), differentiate, d/dx):
  - [ ] SPLIT LAYOUT: axes on LEFT half (shift LEFT*2.5 + DOWN*0.5), equations on RIGHT half (x > 1.5). NEVER full-screen axes.
  - [ ] x-axis AND y-axis integer labels using loops (Text(str(xv), ...).next_to(axes.c2p(xv,0), DOWN)). NEVER use include_numbers=True.
  - [ ] Original curve f(x) in BLUE_C drawn with `Create(curve, run_time=2.5)` — NEVER add it statically with self.add().
  - [ ] Moving dot (YELLOW Dot radius=0.13) + tangent line (YELLOW Line) both use `always_redraw()` with ValueTracker t_track.
  - [ ] Tangent line computed as: slope = f_prime(xc); p1 = axes.c2p(xc-0.65, yc-slope*0.65); p2 = axes.c2p(xc+0.65, yc+slope*0.65); Line(p1, p2).
  - [ ] Sweep: `self.play(t_track.animate.set_value(x_hi), run_time=4.0, rate_func=smooth)` — shows slope changing across the curve.
  - [ ] After sweep: `self.remove(moving_dot, tangent_line)` then show step equations.
  - [ ] Scene 1 problem text (e.g. "y = ..." and "Find: dy/dx") goes at the BOTTOM of the screen (y ≈ -3.0), grouped as `problem_group = VGroup(prob_lbl, find_lbl)`. NEVER place it on the right half where equations will go.
  - [ ] Scene 2 FIRST action: `self.play(FadeOut(problem_group))` — clear the bottom labels BEFORE any equations appear. Then sweep the tangent, then write equations.
  - [ ] Differentiation rule on RIGHT half: identify rule (Product/Chain/Power), show components, compute derivatives, write final expression. Use VGroup.arrange(DOWN, buff=0.42, aligned_edge=LEFT).move_to(RIGHT*2.8 + UP*0.5).
  - [ ] Overlay derivative curve f'(x) in ORANGE with Create() after rule steps are shown.
  - [ ] Final derivative expression: font_size=52+, gradient PINK→PURPLE, gold SurroundingRectangle, Flash.
- [ ] **VOLUME CONSERVATION** checklist (if problem says "cone/cylinder reshaped into sphere", "melted and recast", "find radius of sphere"):
  - [ ] NEVER use ThreeDScene. Use regular Scene with isometric 2D shapes.
  - [ ] Use GEOMETRY TYPE 11 code helper as the starting template.
  - [ ] Act 1 (LEFT): isometric cone/cylinder with r and h labels. Act 2 (LEFT): sphere with R=? label.
  - [ ] RIGHT: V1 formula → substitute → V1=V2 → solve for R step by step.
  - [ ] Adapt r_cone, h_cone, vol_num, r3_val, r_sphere from the ACTUAL problem values.
  - [ ] Final answer: SurroundingRectangle(GOLD) + Circumscribe + Flash.
- [ ] **HOLLOW HEMISPHERE → CYLINDER** checklist (if problem says "hollow hemispherical shell", "internal/external diameter", "melted and recast into cylinder", "find height of cylinder"):
  - [ ] NEVER use ThreeDScene. Use regular Scene with 2D Arc shapes.
  - [ ] Use GEOMETRY TYPE 12 code helper as the starting template.
  - [ ] Act 1 (LEFT): outer Arc + inner Arc (showing hollow), with R and r labels. Formulas on RIGHT.
  - [ ] Act 2 (LEFT after FadeOut): Rectangle cylinder with "h=?" label. V_shell=V_cyl solve on RIGHT.
  - [ ] Formula: V_shell = (2/3)π(R³ − r³). NEVER use Line(*[many_points]) — use Arc directly.
  - [ ] Adapt R_outer, r_inner, r_cyl, h_answer, v_num from the ACTUAL problem values.
  - [ ] Final answer: SurroundingRectangle(GOLD) + Circumscribe + Flash.
- [ ] **BPT / SIMILAR TRIANGLES** checklist (if problem says "DE || BC", "LM || AB", "PQ || XY" in a triangle):
  - [ ] NEVER produce text-only. NEVER use generic textbook values (3/5, 5.6, 2.1). Use EXACT expressions from the problem.
  - [ ] LEFT HALF (MANDATORY): Large triangle (Polygon A,B,C) in BLUE_C/BLUE_E. Parallel line (DE/LM/PQ) drawn in YELLOW.
  - [ ] DashedLine for each of the FOUR segments (AD,DB,AE,EC or AL,LC,BM,MC). Labels in GOLD (shorter segment) and GREEN_C (longer).
  - [ ] All four segment labels MUST match the problem values exactly (e.g. "x-3", "2x", "x-2", "2x+3").
  - [ ] RIGHT HALF: BPT ratio → substitute → cross-multiply → solve for x. VGroup.arrange(DOWN,buff=0.38).move_to(RIGHT*2.8+UP*0.3).
  - [ ] Final answer: font_size=42+, GOLD, SurroundingRectangle(GOLD), Flash + Circumscribe.
  - [ ] Use GEOMETRY TYPE 10 code helper as the starting template. Adapt ALL variable names and expressions.
- [ ] Physics/Projectile MOTION checklist (if problem asks for Hmax / T / R from angled launch):
  - [ ] Stadium background: dark blue sky Rectangle + green grass Rectangle (exception to the pure black rule -- stadium scenes need sky color)
  - [ ] make_athlete(shirt_color=BLUE_C, scale=0.6) at FAR LEFT edge (x < -5.5) -- NOT center; ball is the hero
  - [ ] Dashed parabolic arc via ParametricFunction + proj_pt() mapping (use PROJECTILE MOTION helper)
  - [ ] Ball animates along arc via ValueTracker t_trk (run_time=3.0, rate_func=smooth)
  - [ ] Three velocity vectors at launch: u (white diagonal), ux (teal horizontal), uy (orange vertical)
  - [ ] Dashed vertical line at peak + "Hmax" label + "vy=0 at peak" label
  - [ ] Flash() on landing; three gold answer boxes side by side: Hmax | T | R
- [ ] **GEOMETRY / DISTANCE FORMULA** checklist (if problem asks for distance between two points):
  - [ ] SPLIT LAYOUT: axes on LEFT half (shift LEFT*2.5 + DOWN*0.9), equations on RIGHT half (x > 1.5). NEVER full-width axes.
  - [ ] Axes x_range and y_range clipped to just contain both points + padding 1.5. x_length=5.8, y_length=5.5 (short height keeps dots below title zone).
  - [ ] EDGE-SAFE labels: P1 near left edge → `lbl1.next_to(dot1, RIGHT, buff=0.14)`. P2 near right edge → `lbl2.next_to(dot2, LEFT, buff=0.14)`. NEVER place label in the direction that goes off-screen.
  - [ ] BOUNCING BALL: `Circle(radius=0.18, color=YELLOW)` rolls from P1 to P2 via ValueTracker + perp_dir bounce (4 bouncing arcs, decaying height). `self.play(Create(dist_line), t_ball.animate.set_value(1.0), run_time=2.5, rate_func=linear)`. Flash + Transform ball→dot2 at landing.
  - [ ] Right-angle legs: `DashedLine(P1, corner)` + `DashedLine(corner, P2)` in TEAL. Δx label BELOW h_leg (DOWN buff=0.10), Δy label LEFT of v_leg (LEFT buff=0.10) — both INSIDE the triangle.
  - [ ] Equation stack: font_size=25 for all steps (prevents overflow). `VGroup.arrange(DOWN, buff=0.38, aligned_edge=LEFT).move_to(RIGHT*2.8 + UP*0.8)`. Answer font_size=38 below stack.
- [ ] Physics: sphere PHYSICALLY MOVES with roll_sphere(); force arrows in RED/GREEN_C/ORANGE/YELLOW
- [ ] Physics: force arrow labels each placed with next_to(arrow.get_end(), direction, buff=0.12)
- [ ] Physics: incline shifted LEFT*1.5 so right half of screen is free for equations
- [ ] Physics: equations colour-coded to match their force arrow colour
- [ ] Physics: energy bars animate from zero (BLUE_C=KE_trans, TEAL=KE_rot, ORANGE=PE)
- [ ] **PURE BLACK BACKGROUND** -- always: `bg = Rectangle(width=16, height=9, fill_color=BLACK, fill_opacity=1); self.add(bg)`. NEVER use a colored or gradient background rectangle.
- [ ] **TITLE** -- large gradient text at top: `title.set_color_by_gradient(...)` using the domain palette from the VISUAL STYLE section. font_size ≥ 48.
- [ ] **CHARACTERS** -- PURE CONCEPT animations (trig graphs, infinite series, integrals, limits, Fourier, parametric curves, number theory visualizations): **NO characters**. The math IS the visual. For word problems only, characters go at screen edges.
- [ ] Characters at screen EDGES ONLY (x < -4.5 LEFT or x > 4.5 RIGHT) -- NEVER over equations
- [ ] Physics character: scale=0.55, pinned at x > 5.5 or x < -5.5
- [ ] Layout: Title at y > 3.0, equations at centre, characters at edges
- [ ] Title and equations use `.set_color_by_gradient()` matching the domain palette
- [ ] `FadeOut(Group(*self.mobjects))` between acts -- **never** `VGroup(*self.mobjects)`
- [ ] At least 2 amusing moments (panic wiggle, wrong-answer crash, happy jump) -- for word problems only; skip for pure concept animations
- [ ] Confetti + Flash + gold SurroundingRectangle at the final answer reveal
- [ ] Total estimated animation time is ≤ 35 seconds (see ANIMATION LENGTH + AUDIO SYNC rule above)
- [ ] Ends with the FINAL ANSWER in gradient color matching the domain, clearly displayed and boxed in gold

## Retry Logic -- MANDATORY on error
If `run_manim_animation` returns `status == 'error'`:
1. Read the `message` field -- it contains the EXACT error and instructions.

2. **If message contains a Python error** (NameError, IndexError, TypeError, AttributeError):
   - `NameError: name 'X' is not defined` -> add `X = ORIGIN` BEFORE the first use of X
   - `IndexError: list index out of range` -> check VGroup size; reduce index or add items
   - `ValueError: truth value of array` -> `Line()` takes exactly 2 points; use `Polygon()` for triangles
   - `TypeError: unexpected keyword 'corner_radius'` -> use `RoundedRectangle(..., corner_radius=...)`
   - `AttributeError: no attribute 'rotate'` -> use `np.array([np.cos(a), np.sin(a), 0])`
   - Any other -> fix the specific lines shown in the error snippet
   → Fix ONLY the broken section. Call `run_manim_animation` again with the corrected script.

4. **Maximum 2 total attempts** (1 initial + 1 retry). If the second attempt also fails,
   report the failure honestly. NEVER produce a third attempt.
   3D FALLBACK: If the initial attempt used `ThreeDScene` and failed, the retry MUST
   switch to regular `Scene` (2D) with standard LEFT=axes, RIGHT=steps layout.
   This guarantees a visual animation even when 3D rendering is unavailable.

## CRITICAL: NEVER text-only
Text-only animations are NOT acceptable. The student needs a visual animation with:
- Graphs, plots, curves, shapes, or geometric objects drawn on 2D Axes
- Algebra problems: ALWAYS Axes on LEFT half with curve/circle/shapes; steps on RIGHT half
- NEVER just write equations as Text objects stacked on screen with no visual element

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
