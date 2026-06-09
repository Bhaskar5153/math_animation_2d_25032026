LAYOUT_RULES = """\
==============================================================================
LAYOUT SAFETY ZONES -- ZERO TOLERANCE FOR OVERLAP
==============================================================================

Manim canvas: x in [-7, 7], y in [-4, 4]. FIXED REGIONS:

  +---------------------------------------------------------------+
  |   TITLE ZONE   y > 3.0    (1 line, font <= 40)               |
  +---------------------------------------------------------------+
  |   TOP LABEL    y in [2.0, 3.0]  (step label, font 28-32)     |
  +---------------------------+-----------------------------------+
  | PLOT / AXES ZONE          |  EQUATION / STEPS ZONE           |
  | LEFT HALF  x in [-7, 0]  |  RIGHT HALF  x in [0, 7]         |
  | axes.shift(LEFT*2.5)     |  eq_stack.move_to(RIGHT*2.8)     |
  | y in [-2.5, 2.5]         |  y in [-2.0, 2.5]                |
  +---------------------------+-----------------------------------+
  |   BOTTOM NOTE  y in [-2.2, -1.8]     (notes, font 24)        |
  +---------------------------------------------------------------+
  |   FOOTER ZONE  y < -2.5              (summary, font 26)       |
  +---------------------------------------------------------------+

  CRITICAL: LEFT and RIGHT halves MUST NOT overlap.
    axes center ≈ (-2.5, -0.3).  axes.shift(LEFT*2.5 + DOWN*0.3) is MANDATORY.
    eq_stack center ≈ (2.8, Y).  eq_stack.move_to(RIGHT*2.8 + UP*Y) is MANDATORY.

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

OVERLAP RULE 5D -- TITLE + STEP LABEL SEPARATION (CRITICAL — ZERO TOLERANCE):
  TITLE FONT SIZE RULES (violations produce the overlapping-title screenshot bug):
    title chars ≤ 15  → font_size ≤ 44    e.g. "Quadratics"
    title chars ≤ 25  → font_size ≤ 36    e.g. "Basic Algebra Lesson"
    title chars > 25  → font_size ≤ 28    e.g. "Basic Proportionality Theorem"
  TITLE POSITION RULES (MANDATORY):
    title.to_edge(UP, buff=0.25)           # y ~= 3.6  — TOP EDGE ONLY
    NEVER: title.move_to(ORIGIN)           # ← overlaps everything
    NEVER: title.to_edge(LEFT/RIGHT)       # ← wrong axis
    NEVER: title.move_to(UP*2) or UP*1    # ← too low, collides with steps
  Step label (appears AFTER title, not simultaneously):
    step_lbl.to_edge(UP).shift(DOWN*0.75) # y ~= 2.95
  Only ONE font>30 text visible at a time. FadeOut title before showing steps.

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

OVERLAP RULE 5L -- ANY DIAGRAM/VENN/TREE IN LEFT HALF (HIGHEST PRIORITY):
  !! Applies to: Venn diagrams, factor trees, bar diagrams, number lines, flowcharts !!
  !! These are NOT just Axes — ANY visual diagram MUST stay in the LEFT HALF !!

  VENN DIAGRAM layout (MANDATORY):
    v_radius = 1.5          # maximum radius to fit both circles in LEFT half
    lc = LEFT * 3.0         # left circle center  — spans x: -4.5 to -1.5
    rc = LEFT * 1.0         # right circle center — spans x: -2.5 to +0.5
    # Overlap lens at approximately x = -2.0 (LEFT half)
    # Token positions:
    tok_left_only.move_to(np.array([-3.8, 0, 0]))   # left non-overlap zone
    tok_center.move_to(np.array([-2.0, Y, 0]))       # overlap zone
    tok_right_only.move_to(np.array([-0.3, 0, 0]))   # right non-overlap zone (still LEFT half)
    # Equations on RIGHT:
    eq_column.move_to(RIGHT * 2.8 + UP * Y)          # RIGHT half, NEVER over circles

  FACTOR TREE layout (MANDATORY):
    # If two trees side by side: LEFT tree roots at LEFT*4+UP*2, RIGHT tree at RIGHT*2+UP*2
    # If single tree: root at LEFT*2+UP*2, spans LEFT half; equations on RIGHT*2.8

  BAR DIAGRAM layout: bar.align_to(LEFT*4.0, LEFT) — equations on RIGHT*2.8

OVERLAP RULE 5M -- MULTIPLE ANSWER BOXES MUST BE STACKED VERTICALLY:
  !! When showing 2+ answer values (e.g. HCF=6 and LCM=36), ALWAYS arrange DOWN !!
  !! NEVER place two answer boxes side by side — they WILL overlap at any font size !!

  CORRECT (vertical stack):
    ans1 = Text("HCF  =  6",  font_size=80, color=GOLD,    weight="BOLD")
    ans2 = Text("LCM  =  36", font_size=80, color=GREEN_C, weight="BOLD")
    answer_stack = VGroup(ans1, ans2).arrange(DOWN, buff=1.0)
    answer_stack.move_to(ORIGIN)
    rect1 = SurroundingRectangle(ans1, color=GOLD,    buff=0.30)
    rect2 = SurroundingRectangle(ans2, color=GREEN_C, buff=0.30)

  FORBIDDEN (side by side — causes overlap):
    ans1.move_to(LEFT*2);  ans2.move_to(RIGHT*2)  # DO NOT DO THIS
    VGroup(ans1, ans2).arrange(RIGHT, buff=0.5)    # DO NOT DO THIS

  For 3+ answers: same rule — always arrange(DOWN, buff=0.8+).

OVERLAP RULE 5K -- ALGEBRA LEFT/RIGHT SPLIT (HIGHEST PRIORITY):
  !! For ANY scene with Axes + equations, screen MUST be split LEFT=plot, RIGHT=text !!

  CORRECT pattern:
    axes = Axes(...).shift(LEFT*2.5 + DOWN*0.3)          # center of axes at (-2.5, -0.3)
    eq_stack = VGroup(eq1, eq2, ...).arrange(DOWN, buff=0.30, aligned_edge=LEFT)
    eq_stack.move_to(RIGHT*2.8 + UP*0.4)                 # center of steps at (2.8, 0.4)
    # axes spans roughly x in [-5.3, +0.3] -- stays LEFT
    # eq_stack spans roughly x in [+0.5, +5.3] -- stays RIGHT
    # NO OVERLAP

  VIOLATION pattern (produces screenshot overlap):
    axes = Axes(...)                     # no shift → centered at (0, 0)
    eq_stack.move_to(RIGHT*2.5)          # steps at x≈2.5
    # axes spans x in [-5, +5], steps at x=2.5 → OVERLAP in range x=[0, 5]

CRITICAL ANTI-OVERLAP PATTERN for equation sequences:
  # ALWAYS use VGroup.arrange -- NEVER manual positioning of stacked text:
  #
  # CORRECT:
  eq_group = VGroup(eq1, eq2, eq3).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
  eq_group.move_to(RIGHT*2.8 + UP*0.4)   # RIGHT half only
  self.play(LaggedStart(*[Write(eq) for eq in eq_group], lag_ratio=0.3))
  #
  # FORBIDDEN (will overlap on small screens):
  eq1.shift(UP*1.0); eq2.shift(ORIGIN); eq3.shift(DOWN*1.0)  # DO NOT DO THIS\
"""
