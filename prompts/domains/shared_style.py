VISUAL_STYLE = """\
==============================================================================
VISUAL STYLE: DARK ELEGANCE  (reference quality benchmark)
==============================================================================
Every animation must match or exceed mathematisa-quality visual standards:

BACKGROUND -- MANDATORY:
  bg = Rectangle(width=16, height=9, fill_color=BLACK, fill_opacity=1)
  self.add(bg)
  NEVER use a gradient or colored background. Pure BLACK only.

TITLE (always present, top of screen):
  title = Text("Your Topic Here", font_size=52)
  title.set_color_by_gradient(CYAN, BLUE_B)   # pick palette below
  title.to_edge(UP, buff=0.35)
  self.play(Write(title), run_time=1.0)

  TITLE COLOR PALETTE (match the math domain):
    Trigonometry / Waves / Oscillations  → CYAN,   BLUE_B
    Calculus / Integrals / Derivatives   → PINK,   PURPLE
    Series / Sequences / Number Theory   → TEAL,   GREEN_C
    Algebra / Equations / Polynomials    → YELLOW, ORANGE
    Statistics / Probability / Normal    → BLUE_C, PURPLE
    Geometry / Shapes / Vectors          → ORANGE, RED
    Physics / Motion / Forces            → GREEN_C, TEAL

CURVES AND SHAPES on black:
  - Vibrant single-color strokes: CYAN, PINK, BLUE_B, TEAL, PURPLE, or GREEN_C
  - stroke_width = 3 to 4 for main curves
  - Dot radius = 0.12–0.16 at key points (endpoints, peaks, roots)
  - DashedLine for construction lines (dash_length=0.12, stroke_width=1.5)

AXES on black background:
  axis_config={"color": GRAY_A, "stroke_width": 2}
  NEVER use include_numbers=True or add_coordinates()
  Add tick labels manually as Text() in a loop (see code helpers)
  Arrow tips on axes: use axis_config={"tip_length": 0.2} for clean arrow tips

EQUATIONS (bottom zone):
  font_size=38–48 for main formula, WHITE or gradient matching title
  Center below the visualization at y = -2.5 to -3.0
  Step equations revealed one line at a time

CHARACTERS:
  PURE CONCEPT animations (trig graphs, infinite series, integrals, limits,
  Fourier series, complex numbers, parametric curves):
    → NO characters. The math IS the visual. No humans, no robots, no emoji.
  WORD PROBLEMS (find X, prove Y, a ball is thrown at angle θ, etc.):
    → Characters optional, at screen EDGES ONLY (x < -4.5 left, x > 4.5 right)\
"""
