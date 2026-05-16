LAYOUT_RULES = """\
==============================================================================
LAYOUT SAFETY ZONES -- ZERO TOLERANCE FOR OVERLAP
==============================================================================

Manim canvas: x in [-7, 7], y in [-4, 4]. FIXED REGIONS:

  +---------------------------------------------------------------+
  |   TITLE ZONE   y > 3.0    (1 line, font <= 40)               |
  +---------------------------------------------------------------+
  |   TOP LABEL    y in [2.0, 3.0]  (step label, font 28-32)     |
  +---------------+-----------------------+-----------------------+
  | CHARACTER     |   EQUATION ZONE       |  CHARACTER / GRAPH    |
  | LEFT EDGE     |  x in [-3.5, 3.5]    |    RIGHT EDGE         |
  | x < -4.5      |  y in [-1.5, 2.0]    |    x > 4.5            |
  +---------------+-----------------------+-----------------------+
  |   BOTTOM NOTE  y in [-2.2, -1.8]     (notes, font 24)        |
  +---------------------------------------------------------------+
  |   FOOTER ZONE  y < -2.5              (summary, font 26)       |
  +---------------------------------------------------------------+

OVERLAP RULE 5A -- CLEAR THE STAGE BETWEEN ACTS:
  self.play(FadeOut(Group(*self.mobjects)))
  self.add(bg.copy())
  # Then place ALL new objects fresh. Never assume old objects are gone.

OVERLAP RULE 5B -- STACK EQUATIONS WITH .arrange() NOT MANUAL SHIFTS:
  steps = VGroup(
      Text("Step 1: ...", font_size=36, color=WHITE),
      Text("Step 2: ...", font_size=36, color=YELLOW),
      Text("Step 3: ...", font_size=36, color=GREEN_C),
  ).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
  steps.move_to(ORIGIN)
  NEVER do: eq1.move_to(UP*0.5); eq2.move_to(DOWN*0.5)  -- these WILL overlap at scale.

OVERLAP RULE 5C -- CHARACTERS AT EDGES ONLY:
  LEFT zone:  x < -4.5 -> character.to_edge(LEFT).shift(RIGHT*0.5)
  RIGHT zone: x >  4.5 -> character.to_edge(RIGHT).shift(LEFT*0.5)
  Speech bubbles: always .next_to(character, UR/UL, buff=0.2)
  Physics scenes: character scale=0.55, pin at x > 5.5 or x < -5.5

OVERLAP RULE 5D -- TITLE + STEP LABEL SEPARATION:
  title.to_edge(UP)                          # y ~= 3.7
  step_lbl.to_edge(UP).shift(DOWN*0.75)     # y ~= 2.95
  Only ONE font>38 text visible at a time. FadeOut title before new one.

OVERLAP RULE 5E -- AXIS LABELS: font <= 20, buff >= 0.12 from axis
OVERLAP RULE 5F -- FORCE ARROWS: gravity=DOWN, normal=UP-LEFT, friction=UP-RIGHT
  Labels at arrow.get_end() with next_to(), shift outward extra 0.2 if crowded
OVERLAP RULE 5G -- INCLINE on LEFT half (shift LEFT*1.5), equations on RIGHT half
OVERLAP RULE 5H -- PRE-PLACEMENT CHECK: "What is on screen? Does new object fit?"

OVERLAP RULE 5I -- LONG FORMULA + PARAMETER SEPARATION:
  If a formula string is longer than 22 characters (e.g., "T_k+1 = C(n,k)*a^(n-k)*b^k"),
  use font_size <= 34. NEVER use font_size >= 40 for any formula > 20 characters long.
  NEVER show formula + parameter labels + answer box all simultaneously on screen.
  Show them in sequence -- FadeOut old objects before showing the next group:
    Step 1: Show formula in title zone (font_size=32-34, to_edge(UP))
    Step 2: Show parameter group BELOW formula using VGroup.arrange(RIGHT, buff=0.6):
              params = VGroup(
                  Text("a = 2x", font_size=30),
                  Text("b = -1/x", font_size=30),
                  Text("n = 8", font_size=30),
              ).arrange(RIGHT, buff=0.7)
              params.next_to(formula, DOWN, buff=0.4)
    Step 3: FadeOut(formula, params), then show the working/solution steps
  NEVER place parameter labels inline with the formula on the same line -- they WILL overlap.

OVERLAP RULE 5J -- COORDINATE POINT LABELS:
  When labeling points (dots) on a coordinate grid:
  - Points in the UPPER half (y > 0): place label BELOW the dot → next_to(dot, DR, buff=0.15)
    or next_to(dot, DL, buff=0.15). NEVER next_to(dot, UL) or UR when y > 1.5 — it enters the title zone.
  - Points in the LOWER half (y <= 0): place label ABOVE the dot → next_to(dot, UR, buff=0.15)
  - NEVER place two point labels at the same y-level side by side without checking for x-overlap.
  - Connecting line labels (e.g. "d = 10"): place at midpoint of the line, shifted perpendicular
    away from any axes. Use `line.get_midpoint() + UP*0.3` or `+ LEFT*0.4`.

CRITICAL ANTI-OVERLAP PATTERN for equation sequences:
  # ALWAYS use VGroup.arrange -- NEVER manual positioning of stacked text:
  #
  # CORRECT:
  eq_group = VGroup(eq1, eq2, eq3).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
  eq_group.move_to(ORIGIN)
  self.play(LaggedStart(*[Write(eq) for eq in eq_group], lag_ratio=0.3))
  #
  # FORBIDDEN (will overlap on small screens):
  eq1.shift(UP*1.0); eq2.shift(ORIGIN); eq3.shift(DOWN*1.0)  # DO NOT DO THIS\
"""
