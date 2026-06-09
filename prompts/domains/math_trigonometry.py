TRIGONOMETRY_HELPERS = """\
### TRIGONOMETRY TYPE 1: UNIT CIRCLE + TRACED WAVE
# Use for: evaluate sin/cos/tan at an angle, graph a trig function.
# LAYOUT: unit circle at FAR LEFT (center=LEFT*4.5, radius=1.2) + wave Axes shifted LEFT*1.0.
#         Both together fill the LEFT half. Equation steps go to RIGHT*2.8 — RIGHT half is free.
# NEVER produce text-only for trig problems — the unit circle + wave IS the animation.
# Colors: sin=CYAN  cos=PURPLE  tan=PINK    Title gradient: CYAN->BLUE_B
```python
CURVE_COLOR = CYAN   # CYAN for sin, PURPLE for cos, PINK for tan

circ_center = LEFT * 4.5   # unit circle at far-left so wave axes fit next to it
radius = 1.2               # circle spans x=-5.7 to x=-3.3 (LEFT edge zone)

# -- unit circle (far LEFT) --
circle = Circle(radius=radius, color=CURVE_COLOR, stroke_width=3).move_to(circ_center)
c_hax = Line(circ_center+LEFT*1.5, circ_center+RIGHT*1.5, color=GRAY_A, stroke_width=1.5)
c_vax = Line(circ_center+DOWN*1.5, circ_center+UP*1.5,   color=GRAY_A, stroke_width=1.5)

# -- graph axes (CENTER-LEFT) — unit circle + wave share LEFT half; equations go RIGHT --
# wave axes center at x=-1.0, spanning x=-3.0 to x=1.0. RIGHT half (x>1.5) is free for steps.
g_axes = Axes(
    x_range=[0, 2*PI, PI/2],
    y_range=[-1.6, 1.6, 0.5],
    x_length=4.0, y_length=3.0,
    axis_config={"color": GRAY_A, "stroke_width": 1.5, "include_ticks": False},
).shift(LEFT * 1.0 + DOWN * 0.2)
# π/2, π, 3π/2, 2π labels — NEVER use include_numbers=True
pi_lbls = VGroup(
    Text("π/2",  font_size=15, color=GRAY_A).next_to(g_axes.c2p(PI/2,   0), DOWN, buff=0.10),
    Text("π",    font_size=15, color=GRAY_A).next_to(g_axes.c2p(PI,     0), DOWN, buff=0.10),
    Text("3π/2", font_size=15, color=GRAY_A).next_to(g_axes.c2p(3*PI/2, 0), DOWN, buff=0.10),
    Text("2π",   font_size=15, color=GRAY_A).next_to(g_axes.c2p(2*PI,   0), DOWN, buff=0.10),
)

# -- moving dot and traced wave --
t_trk = ValueTracker(0.0)
def circ_pt(t):
    return circ_center + RIGHT * radius * np.cos(t) + UP * radius * np.sin(t)
def graph_pt(t):
    return g_axes.c2p(t, np.sin(t))   # change np.sin -> np.cos for cosθ

c_dot = Dot(radius=0.13, color=CURVE_COLOR, fill_opacity=1)
c_dot.add_updater(lambda m: m.move_to(circ_pt(t_trk.get_value())))
g_dot = Dot(radius=0.13, color=CURVE_COLOR, fill_opacity=1)
g_dot.add_updater(lambda m: m.move_to(graph_pt(t_trk.get_value())))
h_dash = always_redraw(lambda: DashedLine(
    circ_pt(t_trk.get_value()), graph_pt(t_trk.get_value()),
    color=CURVE_COLOR, stroke_width=1.4, dash_length=0.13))
wave_trace = TracedPath(g_dot.get_center, stroke_color=CURVE_COLOR, stroke_width=3)
r_line = always_redraw(lambda: Line(
    circ_center, circ_pt(t_trk.get_value()), color=CURVE_COLOR, stroke_width=2))

self.play(Create(circle), Create(c_hax), Create(c_vax))
self.play(Create(g_axes), Write(pi_lbls))
self.add(r_line, h_dash, wave_trace, c_dot, g_dot)
self.play(t_trk.animate.set_value(2*PI), run_time=5.0, rate_func=linear)
c_dot.clear_updaters(); g_dot.clear_updaters()

# label below circle: "sin θ" / "cos θ" / "tan θ"
func_lbl = Text("sin θ", font_size=34, color=CURVE_COLOR)
func_lbl.set_color_by_gradient(CYAN, BLUE_B)
func_lbl.next_to(circle, DOWN, buff=0.35)
self.play(Write(func_lbl))
# AFTER wave trace: step equations go to RIGHT HALF — NEVER over wave axes.
# eq_stack.arrange(DOWN, buff=0.32, aligned_edge=LEFT).move_to(RIGHT*2.8 + UP*0.3)
```

### TRIGONOMETRY TYPE 2: EQUATION SOLVER (solve sin(x)=k, cos(x)=k)
# After the full wave trace (Type 1), add these to mark the solutions graphically.
# Orange horizontal line at y=k shows the equation; GOLD dots = solutions.
```python
k_val = 0.5    # RHS constant — adapt to actual problem (e.g. 0.5, -sqrt(3)/2, etc.)

# Horizontal line at y=k
sol_hline = DashedLine(
    g_axes.c2p(0, k_val), g_axes.c2p(2*PI, k_val),
    color=ORANGE, stroke_width=2.0, dash_length=0.12)
k_lbl = Text("y = " + str(k_val), font_size=16, color=ORANGE)
k_lbl.next_to(g_axes.c2p(2*PI, k_val), RIGHT, buff=0.08)
self.play(Create(sol_hline), Write(k_lbl))

# GOLD dots at each solution angle on the wave (adapt angles to actual problem)
sol_angles   = [PI/6, 5*PI/6]        # e.g. sin(x)=0.5  -> π/6, 5π/6
sol_labels   = ["x = π/6", "x = 5π/6"]
for ang, lbl_txt in zip(sol_angles, sol_labels):
    sol_dot  = Dot(g_axes.c2p(ang, k_val), radius=0.15, color=GOLD)
    v_dash   = DashedLine(g_axes.c2p(ang, k_val), g_axes.c2p(ang, 0),
                          color=GOLD, stroke_width=1.5, dash_length=0.10)
    ang_lbl  = Text(lbl_txt, font_size=15, color=GOLD)
    ang_lbl.next_to(g_axes.c2p(ang, 0), DOWN, buff=0.12)
    self.play(FadeIn(sol_dot), Create(v_dash), Write(ang_lbl))
    self.play(Flash(sol_dot, color=GOLD, flash_radius=0.22, num_lines=8))
    # Mirror on unit circle (show the angle visually)
    circ_sol = Dot(circ_pt(ang), radius=0.13, color=GOLD)
    self.play(FadeIn(circ_sol))
    self.wait(0.8)
```

### TRIGONOMETRY TYPE 3: IDENTITY PROOF (prove sin²x+cos²x=1, sin(2x)=2sinxcosx, etc.)
# LEFT HALF: plot LHS and RHS as curves on the SAME Axes — they overlap = visual proof.
# RIGHT HALF: algebraic steps proving the identity.
# SCREEN SPLIT: id_axes.shift(LEFT*2.5 + DOWN*0.3). Steps: move_to(RIGHT*2.8 + UP*0.3).
```python
id_axes = Axes(
    x_range=[0, 2*PI, PI/2],
    y_range=[-1.3, 1.6, 0.5],
    x_length=5.5, y_length=4.2,
    axis_config={"color": GRAY_A, "stroke_width": 1.5, "include_ticks": False},
).shift(LEFT * 2.5 + DOWN * 0.3)
id_pi_lbls = VGroup(
    Text("π/2", font_size=14, color=GRAY_A).next_to(id_axes.c2p(PI/2,   0), DOWN, buff=0.08),
    Text("π",   font_size=14, color=GRAY_A).next_to(id_axes.c2p(PI,     0), DOWN, buff=0.08),
    Text("3π/2",font_size=14, color=GRAY_A).next_to(id_axes.c2p(3*PI/2, 0), DOWN, buff=0.08),
    Text("2π",  font_size=14, color=GRAY_A).next_to(id_axes.c2p(2*PI,   0), DOWN, buff=0.08),
)
# LHS curve (what we're proving equals the RHS)
lhs_curve = id_axes.plot(
    lambda x: np.sin(x)**2 + np.cos(x)**2,   # adapt to actual LHS
    x_range=[0.01, 2*PI-0.01, 0.04], color=CYAN, stroke_width=3)
# RHS curve (the known constant or simpler function)
rhs_curve = id_axes.plot(
    lambda x: 1.0,   # adapt to actual RHS
    x_range=[0, 2*PI, 0.5], color=PURPLE, stroke_width=2)

self.play(Create(id_axes), Write(id_pi_lbls))
self.play(Create(lhs_curve), run_time=2.5)   # CYAN = LHS
self.play(Create(rhs_curve), run_time=1.5)   # PURPLE = RHS
# Gold dot at a sample point showing the curves coincide
chk = Dot(id_axes.c2p(PI/4, 1.0), radius=0.15, color=GOLD)
self.play(FadeIn(chk))
self.play(Flash(chk, color=GOLD, flash_radius=0.25, num_lines=10))
lhs_lbl = Text("LHS: sin²x+cos²x", color=CYAN,   font_size=18).move_to(id_axes.c2p(PI,   1.38))
rhs_lbl = Text("RHS: 1",           color=PURPLE, font_size=18).move_to(id_axes.c2p(3*PI/2, 1.38))
self.play(Write(lhs_lbl), Write(rhs_lbl))
```

### TRIGONOMETRY TYPE 4: MAX/MIN OF COMBINED TRIG EXPRESSION (a·sinx + b·cosx)
# Use for: "find max/min of 2sinx+3cosx", "range of asinx+bcosx", "maximum value of..."
# STRATEGY: rewrite as R·sin(x+phi) where R=sqrt(a^2+b^2), tan(phi)=b/a.
#           Max = +R, Min = -R. Plot the curve; mark amplitude lines at +-R.
# SCREEN SPLIT: axes.shift(LEFT*2.5+DOWN*0.3). Steps on RIGHT: move_to(RIGHT*2.8+UP*0.4).
# MANDATORY: always plot the combined trig function — NEVER text-only.
```python
import numpy as np

a_coeff = 2.0      # coefficient of sin(x) — adapt to actual problem
b_coeff = 3.0      # coefficient of cos(x) — adapt to actual problem
R = np.sqrt(a_coeff**2 + b_coeff**2)   # amplitude: R = sqrt(4+9) = sqrt(13)

# LEFT HALF: axes with enough y-range to show the oscillation
axes = Axes(
    x_range=[0, 2*PI, PI/2],
    y_range=[-(R + 0.8), R + 0.8, 1],
    x_length=5.5, y_length=5.0,
    axis_config={"color": GRAY_A, "stroke_width": 1.5, "include_ticks": False},
).shift(LEFT*2.5 + DOWN*0.3)
# Tick labels (never include_numbers)
pi_lbls = VGroup(
    Text("π/2",  font_size=15, color=GRAY_A).next_to(axes.c2p(PI/2,   0), DOWN, buff=0.10),
    Text("π",    font_size=15, color=GRAY_A).next_to(axes.c2p(PI,     0), DOWN, buff=0.10),
    Text("3π/2", font_size=15, color=GRAY_A).next_to(axes.c2p(3*PI/2, 0), DOWN, buff=0.10),
    Text("2π",   font_size=15, color=GRAY_A).next_to(axes.c2p(2*PI,   0), DOWN, buff=0.10),
)
y_lbl = Text("f(x)", font_size=18, color=CYAN).next_to(axes.y_axis.get_top(), UP, buff=0.08)

# Combined trig function curve
func_curve = axes.plot(
    lambda x: a_coeff * np.sin(x) + b_coeff * np.cos(x),
    x_range=[0, 2*PI, 0.02], color=CYAN, stroke_width=3)

# Amplitude dashed lines at +R (max) and -R (min)
max_line = DashedLine(axes.c2p(0, R), axes.c2p(2*PI, R),
                      color=GREEN_C, stroke_width=2.0, dash_length=0.14)
min_line = DashedLine(axes.c2p(0, -R), axes.c2p(2*PI, -R),
                      color=RED, stroke_width=2.0, dash_length=0.14)
max_lbl = Text("Max = sqrt(13)", font_size=18, color=GREEN_C)
max_lbl.next_to(axes.c2p(PI/4, R), UR, buff=0.08)
min_lbl = Text("Min = -sqrt(13)", font_size=18, color=RED)
min_lbl.next_to(axes.c2p(5*PI/4, -R), DR, buff=0.08)

# GOLD dot at max peak; ORANGE dot at min trough
phi = np.arctan2(b_coeff, a_coeff)      # phase shift angle
x_max = (PI/2 - phi) % (2*PI)           # x where f(x) = +R
x_min = (3*PI/2 - phi) % (2*PI)         # x where f(x) = -R
max_dot = Dot(axes.c2p(x_max, R),  radius=0.18, color=GOLD,   z_index=4)
min_dot = Dot(axes.c2p(x_min, -R), radius=0.18, color=ORANGE, z_index=4)

self.play(Create(axes), Write(pi_lbls), Write(y_lbl))
self.play(Create(func_curve), run_time=3.0)
self.wait(1.5)
self.play(Create(max_line), Write(max_lbl), GrowFromCenter(max_dot))
self.play(Flash(max_dot, color=GOLD, flash_radius=0.45, num_lines=12))
self.wait(1.0)
self.play(Create(min_line), Write(min_lbl), GrowFromCenter(min_dot))
self.play(Flash(min_dot, color=ORANGE, flash_radius=0.45, num_lines=12))
self.wait(2.0)

# RIGHT HALF: R·sin(x+phi) derivation — one step at a time
eq1 = Text("2sinx + 3cosx",            font_size=24, color=WHITE)
eq2 = Text("= R·sin(x + phi)",         font_size=24, color=CYAN)
eq3 = Text("R = sqrt(a^2 + b^2)",      font_size=24, color=WHITE)
eq4 = Text("R = sqrt(2^2 + 3^2)",      font_size=24, color=TEAL)
eq5 = Text("R = sqrt(13)",             font_size=28, color=GOLD, weight="BOLD")
eq6 = Text("Max value = +sqrt(13)",    font_size=24, color=GREEN_C)
eq7 = Text("Min value = -sqrt(13)",    font_size=24, color=RED)
eq_stack = VGroup(eq1, eq2, eq3, eq4, eq5, eq6, eq7).arrange(DOWN, buff=0.38, aligned_edge=LEFT)
eq_stack.move_to(RIGHT*2.8 + UP*0.4)
for eq in eq_stack:
    self.play(Write(eq), run_time=0.8)
    self.wait(2.0)
```

### UNIT CIRCLE (simple, for inverse trig angle sweeps)
```python
circle = Circle(radius=2, color=WHITE, stroke_width=2).move_to(ORIGIN)
dot    = Dot(circle.point_at_angle(0), color=YELLOW, radius=0.12)
radius_line = always_redraw(lambda: Line(ORIGIN, dot.get_center(), color=YELLOW))
angle_arc   = always_redraw(lambda: Arc(
    radius=0.5, start_angle=0,
    angle=np.arctan2(dot.get_center()[1], dot.get_center()[0]),
    color=GREEN_C))
# Spin the dot around:
self.play(Rotate(dot, angle=TAU, about_point=ORIGIN), run_time=4.0, rate_func=smooth)
```\
"""
