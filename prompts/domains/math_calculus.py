CALCULUS_HELPERS = """\
### CALCULUS -- DERIVATIVE + ANIMATED TANGENT LINE (split layout)
```python
# Use for: "differentiate f(x)", "find dy/dx", "find f'(x)", "find d/dx"
# LAYOUT: LEFT half = graph + tangent sweep    RIGHT half = step-by-step rule
# Always: Create() the curve over 2.5 s -- NEVER show it static from the start
# Axis value labels via loop -- NEVER use include_numbers=True (it crashes)

import math as _math
import numpy as np

# Replace these two functions with the actual problem function and its derivative:
def f(x):       return x**3 * _math.sin(x)
def f_prime(x): return 3*x**2 * _math.sin(x) + x**3 * _math.cos(x)

x_lo, x_hi = -3.5, 3.5
y_lo, y_hi = -15.0, 15.0

# LEFT HALF: axes shifted left + down (keeps curve below title zone)
axes = Axes(
    x_range=[x_lo, x_hi, 1],
    y_range=[y_lo, y_hi, 5],
    x_length=5.8,
    y_length=5.5,
    axis_config={"color": GRAY_A, "stroke_width": 1.5, "include_ticks": False},
).shift(LEFT*2.5 + DOWN*0.5)

# Integer labels on BOTH axes -- ALWAYS add these with loops
for xv in [-3, -2, -1, 1, 2, 3]:
    Text(str(xv), font_size=16, color=GRAY_B).next_to(axes.c2p(xv, 0), DOWN, buff=0.10)
for yv in [-10, -5, 5, 10]:
    Text(str(yv), font_size=14, color=GRAY_B).next_to(axes.c2p(0, yv), LEFT, buff=0.10)
x_lbl = Text("x", font_size=22, color=GRAY_A).next_to(axes.x_axis.get_right(), RIGHT, buff=0.10)
y_lbl = Text("y", font_size=22, color=GRAY_A).next_to(axes.y_axis.get_top(), UP, buff=0.10)

# Original curve drawn with Create() over 2.5 s so students see it traced
curve = axes.plot(f, x_range=[x_lo, x_hi, 0.05], color=BLUE_C, stroke_width=3)
self.play(Create(axes), Write(x_lbl), Write(y_lbl))
self.play(Create(curve), run_time=2.5)

# Curve label in upper-left of graph area
curve_lbl = Text("f(x) = x^3 sin(x)", font_size=22, color=BLUE_C)
curve_lbl.to_corner(UL).shift(RIGHT*0.3 + DOWN*1.0)
self.play(Write(curve_lbl))

# Moving dot + tangent line sweep via ValueTracker
t_track = ValueTracker(x_lo)

moving_dot = always_redraw(lambda: Dot(
    axes.c2p(t_track.get_value(), f(t_track.get_value())),
    radius=0.13, color=YELLOW, z_index=2,
))

def _get_tangent():
    xc = t_track.get_value()
    yc = f(xc)
    slope = f_prime(xc)
    dx_t = 0.65
    p1 = axes.c2p(xc - dx_t, yc - slope * dx_t)
    p2 = axes.c2p(xc + dx_t, yc + slope * dx_t)
    return Line(p1, p2, color=YELLOW, stroke_width=3, z_index=1)

tangent_line = always_redraw(_get_tangent)

self.add(moving_dot, tangent_line)
self.play(t_track.animate.set_value(x_hi), run_time=4.0, rate_func=smooth)
self.remove(moving_dot, tangent_line)

# RIGHT HALF: step-by-step rule (appears alongside sweep using LaggedStart or after)
eq1 = Text("Product Rule: d/dx[uv] = u'v + uv'", font_size=26, color=WHITE)
eq2 = Text("u = x^3       v = sin(x)",            font_size=26, color=TEAL)
eq3 = Text("u' = 3x^2     v' = cos(x)",           font_size=26, color=ORANGE)
eq4 = Text("dy/dx = 3x^2 sin(x) + x^3 cos(x)",   font_size=26, color=YELLOW)

eq_stack = VGroup(eq1, eq2, eq3, eq4).arrange(DOWN, buff=0.42, aligned_edge=LEFT)
eq_stack.move_to(RIGHT*2.8 + UP*0.5)
for eq in eq_stack:
    self.play(Write(eq), run_time=0.9)

# Derivative curve overlaid after rule is shown
deriv_curve = axes.plot(f_prime, x_range=[x_lo, x_hi, 0.05], color=ORANGE, stroke_width=2.5)
deriv_lbl = Text("f'(x) = 3x^2 sin(x) + x^3 cos(x)", font_size=18, color=ORANGE)
deriv_lbl.next_to(curve_lbl, DOWN, buff=0.25, aligned_edge=LEFT)
self.play(Create(deriv_curve), Write(deriv_lbl), run_time=2.0)
```

### CALCULUS -- 2D AXES + CURVE
```python
axes = Axes(
    x_range=[-3, 3, 1], y_range=[-2, 6, 1],
    x_length=8, y_length=5,
    axis_config={"color": GRAY_A, "stroke_width": 2},
).shift(DOWN*0.3)
for xv in range(-3, 4):
    Text(str(xv), font_size=18, color=GRAY_A).next_to(axes.c2p(xv,0), DOWN, buff=0.12)
for yv in range(0, 7, 2):
    Text(str(yv), font_size=18, color=GRAY_A).next_to(axes.c2p(0,yv), LEFT, buff=0.14)
x_lbl = Text("x", font_size=26, color=GRAY_A).next_to(axes.x_axis.get_right(), RIGHT, buff=0.1)
y_lbl = Text("y", font_size=26, color=GRAY_A).next_to(axes.y_axis.get_top(), UP, buff=0.1)
curve = axes.plot(lambda x: x**2 - 1, x_range=[-2.5, 2.5], color=BLUE_C)
self.play(Create(axes), Write(x_lbl), Write(y_lbl))
self.play(Create(curve), run_time=2)
```

### PARAMETRIC CURVES (parabola, ellipse, cycloid, locus — NEVER use ImplicitFunction)
```python
# ── Parabola y² = 4ax (opens right) ──────────────────────────────────────────
# CORRECT: ParametricFunction with t as the y-coordinate
a = 1.0
axes = Axes(x_range=[-1, 6, 1], y_range=[-4, 4, 1], x_length=7, y_length=6,
            axis_config={"color": GRAY_A, "stroke_width": 2}).shift(DOWN*0.3)
parabola = ParametricFunction(
    lambda t: axes.c2p(t**2 / (4*a), t),
    t_range=[-3.8, 3.8, 0.05],
    color=ORANGE, stroke_width=3,
)
# ALSO CORRECT: two explicit branches for y = ±2√(ax)
upper = axes.plot(lambda x: 2*_math.sqrt(a * x), x_range=[0.01, 5.5], color=ORANGE)
lower = axes.plot(lambda x: -2*_math.sqrt(a * x), x_range=[0.01, 5.5], color=ORANGE)

# ── Circle  x² + y² = r² ─────────────────────────────────────────────────────
# Use the built-in Circle Mobject -- NOT an implicit/parametric plot
r = 2.0
circle_mob = Circle(radius=r, color=BLUE_C, stroke_width=3)
circle_mob.move_to(axes.c2p(0, 0))

# ── Ellipse  x²/a² + y²/b² = 1 ───────────────────────────────────────────────
a_e, b_e = 3.0, 2.0
ellipse_mob = Ellipse(width=2*a_e, height=2*b_e, color=TEAL, stroke_width=3)
ellipse_mob.move_to(axes.c2p(0, 0))

# ── General parametric curve ─────────────────────────────────────────────────
# (x(t), y(t)) — use for any locus, cycloid, epicycloid, spiral, etc.
spiral = ParametricFunction(
    lambda t: axes.c2p(t * _math.cos(t), t * _math.sin(t)),
    t_range=[0, 4*PI, 0.05],
    color=PURPLE, stroke_width=2,
)
```

### CALCULUS -- AREA FILL (water-rising effect)
```python
area = axes.get_area(curve, x_range=[0, 2], color=[BLUE, TEAL], opacity=0.4)
self.play(FadeIn(area), run_time=1.5)
```\
"""
