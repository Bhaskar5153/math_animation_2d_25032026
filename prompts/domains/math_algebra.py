ALGEBRA_HELPERS = """\
### ALGEBRA -- RADICAL EQUATION: PLOT f(x) vs RHS + INTERSECTION POINT
```python
# Use for: "solve sqrt(expr1) + sqrt(expr2) = c", nested radical equations
# KEY RULE: NEVER show a number line with "x >= domain_bound" as the answer.
#           That is only the DOMAIN. The SOLUTION is the specific x where f(x) = RHS.
# STRATEGY: (1) plot f(x) on LEFT, (2) draw RHS horizontal line, (3) mark intersection

# Example: sqrt(x + sqrt(2x-1)) + sqrt(x - sqrt(2x-1)) = 3
# Algebraic insight: let u and v be the two radical terms.
# u + v = 3 (given),  u^2+v^2 = 2x,  (uv)^2 = x^2-(2x-1) = (x-1)^2 => uv = |x-1|
# (u+v)^2 = 2x + 2|x-1| = 9
#   x in [0.5,1]: 2x + 2(1-x) = 2 => LHS = sqrt(2) (constant!) -- no solution here
#   x > 1:        4x - 2 = 9  => x = 11/4  => SOLUTION: x = 11/4

import math as _math
import numpy as np

# Simplified function (derived algebraically -- use this for the plot):
# !! CRITICAL: The function value IS sqrt(4x-2), NOT (4x-2), NOT (2x-1) !!
# Numerical proof: at x=11/4, sqrt(4*(11/4)-2) = sqrt(11-2) = sqrt(9) = 3.0 -- matches RHS
def f_radical(x):
    if x < 0.5:   return 0.0
    if x <= 1.0:  return _math.sqrt(2)         # flat segment at sqrt(2) ≈ 1.414
    return _math.sqrt(4*x - 2)                 # !! sqrt(4x-2), NOT 2x-1, NOT 4x-2 !!

# !! The RHS horizontal line is at y=3.0 (the ORIGINAL equation RHS) !!
# !! NOT y=9 (squared form), NOT y=9/2 (intermediate algebra step) !!
# The algebra step "4x-2=9" describes when sqrt(4x-2)=3, i.e., the SQUARED form.
# The line on the PLOT must be drawn at y=3.0, the ORIGINAL value.
rhs_val = 3.0           # y-coordinate of horizontal line -- always the original equation RHS
sol_x   = 11.0 / 4.0   # exact solution: x = 11/4 = 2.75

# LEFT HALF: axes shifted left + slightly down
axes = Axes(
    x_range=[0.4, 5.0, 0.5],
    y_range=[0.0, 4.5, 0.5],
    x_length=5.8,
    y_length=5.0,
    axis_config={"color": GRAY_A, "stroke_width": 1.5, "include_ticks": False},
).shift(LEFT*2.3 + DOWN*0.3)

# Axis value labels -- always use loops
for xv in [1, 2, 3, 4, 5]:
    Text(str(xv), font_size=16, color=GRAY_B).next_to(axes.c2p(xv, 0), DOWN, buff=0.10)
for yv in [1, 2, 3, 4]:
    Text(str(yv), font_size=16, color=GRAY_B).next_to(axes.c2p(0.4, yv), LEFT, buff=0.10)
x_lbl = Text("x", font_size=20, color=GRAY_A).next_to(axes.x_axis.get_right(), RIGHT, buff=0.1)
y_lbl = Text("f(x)", font_size=18, color=GRAY_A).next_to(axes.y_axis.get_top(), UP, buff=0.1)

# TWO segments of f(x):
flat_seg  = Line(axes.c2p(0.5, _math.sqrt(2)), axes.c2p(1.0, _math.sqrt(2)),
                 color=BLUE_C, stroke_width=3)     # constant at sqrt(2) ≈ 1.414
grow_seg  = axes.plot(lambda x: _math.sqrt(4*x - 2),  # sqrt(4x-2), NOT 2x-1 !
                      x_range=[1.0, 4.95, 0.02], color=BLUE_C, stroke_width=3)

# Labels on the curve segments
flat_lbl  = Text("f = sqrt(2) (constant)", font_size=17, color=BLUE_C)
flat_lbl.next_to(axes.c2p(0.75, _math.sqrt(2)), UP, buff=0.12)
grow_lbl  = Text("f = sqrt(4x-2)", font_size=17, color=BLUE_C)
grow_lbl.next_to(axes.c2p(3.5, f_radical(3.5)), UR, buff=0.12)

# RHS horizontal line y = 3
rhs_line  = Line(axes.c2p(0.4, rhs_val), axes.c2p(5.0, rhs_val),
                 color=ORANGE, stroke_width=2.5)
rhs_lbl   = Text("y = 3", font_size=22, color=ORANGE)
rhs_lbl.next_to(axes.c2p(4.5, rhs_val), UR, buff=0.1)

# Intersection = the SOLUTION (GOLD dot at x=11/4)
sol_dot   = Dot(axes.c2p(sol_x, rhs_val), radius=0.18, color=GOLD, z_index=3)
v_sol     = DashedLine(axes.c2p(sol_x, 0), axes.c2p(sol_x, rhs_val),
                       color=GOLD, stroke_width=2, dash_length=0.13)
sol_lbl   = Text("x = 11/4", font_size=24, color=GOLD)
sol_lbl.next_to(axes.c2p(sol_x, 0), DOWN, buff=0.18)

self.play(Create(axes), Write(x_lbl), Write(y_lbl))
self.play(Create(flat_seg), Write(flat_lbl), run_time=1.2)
self.play(Create(grow_seg), Write(grow_lbl), run_time=2.0)
self.play(Create(rhs_line), Write(rhs_lbl), run_time=0.8)
self.play(GrowFromCenter(sol_dot), Create(v_sol), Write(sol_lbl), run_time=1.2)
self.play(Flash(sol_dot, color=GOLD, flash_radius=0.5, line_length=0.22), run_time=0.6)

# RIGHT HALF: algebraic derivation steps
eq1 = Text("Let u = sqrt(x+sqrt(2x-1)),  v = sqrt(x-sqrt(2x-1))", font_size=21, color=WHITE)
eq2 = Text("u + v = 3   (given)",                                  font_size=24, color=WHITE)
eq3 = Text("u^2 + v^2 = 2x",                                      font_size=24, color=TEAL)
eq4 = Text("uv = sqrt((x-1)^2) = |x-1|",                          font_size=24, color=TEAL)
eq5 = Text("(u+v)^2 = 2x + 2|x-1| = 9",                          font_size=24, color=YELLOW)
eq6 = Text("For x >= 1: 4x - 2 = 9",                              font_size=24, color=YELLOW)
eq7 = Text("x = 11/4",                                             font_size=34, color=GOLD, weight="BOLD")

eq_stack = VGroup(eq1, eq2, eq3, eq4, eq5, eq6, eq7).arrange(DOWN, buff=0.32, aligned_edge=LEFT)
eq_stack.move_to(RIGHT*2.8 + UP*0.4)
for eq in eq_stack:
    self.play(Write(eq), run_time=0.8)
```

### ALGEBRA -- POLYNOMIAL / QUARTIC: TWO-CASE CURVE PLOTS + PERFECT SQUARE FACTORING
```python
# Use for: "find a,b such that P(x) is a perfect square / has all positive real roots"
# KEY INSIGHT: P(x) = x^4-4x^3+ax^2+bx+1 factors as (x^2+cx+d)^2
#   Expand: x^4 + 2cx^3 + (c^2+2d)x^2 + 2cdx + d^2
#   Match:  2c=-4 => c=-2;  d^2=1 => d=1 or d=-1  (TWO VALID CASES)
# Case A (d=1):  P(x)=(x-1)^4,      a=6, b=-4,  quadruple root x=1
# Case B (d=-1): P(x)=(x^2-2x-1)^2, a=2, b=4,   double roots x=1+/-sqrt(2)
# LAYOUT: LEFT = quartic curves shown SEQUENTIALLY on same axes, RIGHT = algebra steps
# !! NEVER produce text-only for this problem type -- ALWAYS show both curves !!

import math as _math
import numpy as np

# Shared axes wide enough for both cases (1-sqrt(2)≈-0.41 to 1+sqrt(2)≈2.41)
axes = Axes(
    x_range=[-1.0, 4.0, 0.5],
    y_range=[-0.3, 6.0, 1],
    x_length=5.8,
    y_length=5.5,
    axis_config={"color": GRAY_A, "stroke_width": 1.5, "include_ticks": False},
).shift(LEFT*2.3 + DOWN*0.3)

# Axis value labels -- always use loops
for xv in [-1, 0, 1, 2, 3]:
    xl = Text(str(xv), font_size=14, color=GRAY_B)
    xl.next_to(axes.c2p(xv, 0), DOWN, buff=0.10)
    self.add(xl)
for yv in [1, 2, 3, 4, 5]:
    yl = Text(str(yv), font_size=14, color=GRAY_B)
    yl.next_to(axes.c2p(-1, yv), LEFT, buff=0.10)
    self.add(yl)
x_lbl = Text("x", font_size=20, color=GRAY_A).next_to(axes.x_axis.get_right(), RIGHT, buff=0.1)
y_lbl = Text("P(x)", font_size=18, color=GRAY_A).next_to(axes.y_axis.get_top(), UP, buff=0.1)

# CASE A: P(x) = (x-1)^4 -- BLUE_C -- quadruple root at x=1
curve_A = axes.plot(lambda x: min((x - 1)**4, 5.9),
                    x_range=[-0.7, 3.7, 0.02], color=BLUE_C, stroke_width=3)
root_dot_A  = Dot(axes.c2p(1.0, 0.0), radius=0.18, color=GOLD, z_index=3)
root_lbl_A  = Text("x=1 (quadruple root)", font_size=18, color=GOLD)
root_lbl_A.next_to(root_dot_A, UR, buff=0.15)
case_A_tag  = Text("Case A: a=6, b=-4", font_size=20, color=BLUE_C)
case_A_tag.next_to(axes.c2p(2.2, 5.5), UP, buff=0.05)

# CASE B: P(x) = (x^2-2x-1)^2 -- TEAL -- double roots at 1-sqrt(2) and 1+sqrt(2)
r1_B = 1.0 - _math.sqrt(2)   # ≈ -0.414
r2_B = 1.0 + _math.sqrt(2)   # ≈  2.414
curve_B = axes.plot(lambda x: min((x**2 - 2*x - 1)**2, 5.9),
                    x_range=[-0.95, 3.9, 0.02], color=TEAL, stroke_width=3)
root_dot_B1 = Dot(axes.c2p(r1_B, 0.0), radius=0.18, color=GOLD, z_index=3)
root_dot_B2 = Dot(axes.c2p(r2_B, 0.0), radius=0.18, color=GOLD, z_index=3)
root_lbl_B1 = Text("1-sqrt(2)", font_size=16, color=GOLD)
root_lbl_B1.next_to(root_dot_B1, DOWN, buff=0.15)
root_lbl_B2 = Text("1+sqrt(2)", font_size=16, color=GOLD)
root_lbl_B2.next_to(root_dot_B2, DOWN, buff=0.15)
case_B_tag  = Text("Case B: a=2, b=4", font_size=20, color=TEAL)
case_B_tag.next_to(axes.c2p(2.2, 5.5), UP, buff=0.05)

# ----- animate: axes first -----
self.play(Create(axes), Write(x_lbl), Write(y_lbl))

# Case A curve
self.play(Create(curve_A), run_time=2.5)
self.play(GrowFromCenter(root_dot_A), Write(root_lbl_A), Write(case_A_tag), run_time=1.0)
self.play(Flash(root_dot_A, color=GOLD, flash_radius=0.45, line_length=0.20), run_time=0.6)

# Transition: fade Case A, draw Case B
self.play(FadeOut(VGroup(curve_A, root_dot_A, root_lbl_A, case_A_tag)))
self.play(Create(curve_B), run_time=2.5)
self.play(GrowFromCenter(root_dot_B1), Write(root_lbl_B1), run_time=0.8)
self.play(GrowFromCenter(root_dot_B2), Write(root_lbl_B2), Write(case_B_tag), run_time=0.8)
self.play(Flash(root_dot_B1, color=GOLD, flash_radius=0.35),
          Flash(root_dot_B2, color=GOLD, flash_radius=0.35))

# RIGHT HALF: algebra step chain (one line at a time)
eq1 = Text("Assume: P(x) = (x^2 + cx + d)^2", font_size=21, color=WHITE)
eq2 = Text("Expand => 2c = -4  =>  c = -2", font_size=21, color=TEAL)
eq3 = Text("d^2 = 1  =>  d = 1  or  d = -1", font_size=21, color=WHITE)
eq4 = Text("Case A: d = 1", font_size=21, color=BLUE_C)
eq5 = Text("  a = c^2+2d = 6,  b = 2cd = -4", font_size=20, color=BLUE_C)
eq6 = Text("  P(x) = (x-1)^4", font_size=20, color=BLUE_C)
eq7 = Text("Case B: d = -1", font_size=21, color=TEAL)
eq8 = Text("  a = c^2+2d = 2,  b = 2cd = 4", font_size=20, color=TEAL)
eq9 = Text("  P(x) = (x^2-2x-1)^2", font_size=20, color=TEAL)
eq10 = Text("  roots: 1 +/- sqrt(2)", font_size=20, color=TEAL)
eq_stack = VGroup(eq1, eq2, eq3, eq4, eq5, eq6, eq7, eq8, eq9, eq10)
eq_stack.arrange(DOWN, buff=0.26, aligned_edge=LEFT)
eq_stack.move_to(RIGHT*2.8 + UP*0.2)
for eq in eq_stack:
    self.play(Write(eq), run_time=0.7)
```

### ALGEBRA -- INEQUALITY PROOF: 1-VARIABLE FUNCTION PLOT + AM-GM GEOMETRY
```python
# Use for: "prove X >= Y", inequality proofs using AM-GM, Cauchy-Schwarz, abc=1 constraints
# LAYOUT: LEFT half = function plot showing minimum,  RIGHT half = algebraic step chain
# Strategy: parametrize with b=c=1 and a=t (or similar) to reduce to 1D and plot the curve.
# Students see the U-shape → minimum at equality case → proof is complete visually.

import math as _math
import numpy as np

# -- Replace with the actual problem's LHS function --
# Example: S = (b+c)^2/a^3 + (c+a)^2/b^3 + (a+b)^2/c^3  with abc=1
# Parametrize: a=t, b=1, c=1/t  so abc = t*1*(1/t) = 1  -- constraint satisfied
def S_func(t):
    if t < 0.05:
        return 29.5
    a, b, c = t, 1.0, 1.0 / t
    val = (b + c)**2 / a**3 + (c + a)**2 / b**3 + (a + b)**2 / c**3
    return min(val, 29.5)   # clip to axes y_range so curve stays visible

t_lo, t_hi = 0.3, 3.0

# LEFT HALF: axes
axes = Axes(
    x_range=[t_lo, t_hi, 0.5],
    y_range=[0, 30, 5],
    x_length=5.5,
    y_length=5.0,
    axis_config={"color": GRAY_A, "stroke_width": 1.5, "include_ticks": False},
).shift(LEFT*2.5 + DOWN*0.3)

# Axis value labels -- ALWAYS add with loops, never include_numbers
for tv in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
    Text(str(tv), font_size=15, color=GRAY_B).next_to(axes.c2p(tv, 0), DOWN, buff=0.10)
for sv in [5, 10, 15, 20, 25]:
    Text(str(sv), font_size=14, color=GRAY_B).next_to(axes.c2p(t_lo, sv), LEFT, buff=0.10)
x_lbl = Text("a   (b = c = 1/a)", font_size=17, color=GRAY_A).next_to(axes.x_axis.get_right(), RIGHT, buff=0.1)
y_lbl = Text("S", font_size=20, color=YELLOW).next_to(axes.y_axis.get_top(), UP, buff=0.1)

# Plot the inequality function -- Create() so students watch it traced
curve = axes.plot(S_func, x_range=[0.32, 2.98, 0.02], color=YELLOW, stroke_width=3)

# Minimum marker: at equality case a=b=c=1, the minimum value is 12
min_dot = Dot(axes.c2p(1.0, 12.0), radius=0.16, color=GREEN_C, z_index=2)
h_line  = DashedLine(axes.c2p(t_lo, 12.0), axes.c2p(t_hi, 12.0),
                     color=GREEN_C, stroke_width=2, dash_length=0.15)
v_line  = DashedLine(axes.c2p(1.0, 0), axes.c2p(1.0, 12.0),
                     color=TEAL, stroke_width=2, dash_length=0.15)
eq_lbl  = Text("a = b = c = 1", font_size=19, color=TEAL)
eq_lbl.next_to(axes.c2p(1.0, 0), DOWN, buff=0.15)
min_lbl = Text("min = 12", font_size=20, color=GREEN_C)
min_lbl.next_to(min_dot, UR, buff=0.14)

self.play(Create(axes), Write(x_lbl), Write(y_lbl))
self.play(Create(curve), run_time=2.5)
self.play(Create(h_line), Create(v_line), Write(eq_lbl),
          GrowFromCenter(min_dot), run_time=1.2)
self.play(Write(min_lbl))
self.play(Flash(min_dot, color=GREEN_C, flash_radius=0.35, line_length=0.16), run_time=0.6)

# RIGHT HALF: AM-GM step chain -- one line at a time
# font_size=25 fits long algebra expressions; VGroup keeps them from overlapping
eq1 = Text("AM-GM: (x+y)^2 >= 4xy",          font_size=25, color=WHITE)
eq2 = Text("=> (b+c)^2 >= 4bc",               font_size=25, color=YELLOW)
eq3 = Text("=> (b+c)^2/a^3 >= 4bc/a^3",      font_size=25, color=YELLOW)
eq4 = Text("abc=1  =>  bc = 1/a",             font_size=25, color=TEAL)
eq5 = Text("=> each term >= 4/a^4",           font_size=25, color=ORANGE)
eq6 = Text("By AM-GM: 1/a^4+1/b^4+1/c^4>=3", font_size=25, color=ORANGE)
eq7 = Text("=> S >= 12",                      font_size=28, color=GREEN_C, weight="BOLD")

eq_stack = VGroup(eq1, eq2, eq3, eq4, eq5, eq6, eq7).arrange(DOWN, buff=0.35, aligned_edge=LEFT)
eq_stack.move_to(RIGHT*2.8 + UP*0.3)
for eq in eq_stack:
    self.play(Write(eq), run_time=0.8)
```

### ALGEBRA -- AM-GM TWO-VARIABLE GEOMETRY (rectangle vs square)
```python
# Use for: showing WHY AM >= GM for two positives (visual proof, not just statement)
# Draw: a rectangle (sides p, q) side-by-side with a square (side = (p+q)/2)
# Show: the square has GREATER or EQUAL area -- that is the AM-GM inequality

import math as _math

p_val, q_val = 1.6, 2.4    # two positive values; replace with problem-relevant values
am_val = (p_val + q_val) / 2
gm_val = _math.sqrt(p_val * q_val)

SCALE = 1.1

rect = Rectangle(
    width=p_val * SCALE, height=q_val * SCALE,
    color=ORANGE, fill_color=ORANGE, fill_opacity=0.28, stroke_width=3
).shift(LEFT*2.0)

sq = Square(side_length=am_val * SCALE,
            color=BLUE_C, fill_color=BLUE_C, fill_opacity=0.28, stroke_width=3
).shift(RIGHT*1.5)

rect_lbl = Text("Area = p x q = GM^2", font_size=22, color=ORANGE)
rect_lbl.next_to(rect, DOWN, buff=0.2)

sq_lbl = Text("Area = ((p+q)/2)^2 = AM^2", font_size=22, color=BLUE_C)
sq_lbl.next_to(sq, DOWN, buff=0.2)

ineq_lbl = Text("AM^2  >=  GM^2   =>   AM  >=  GM", font_size=26, color=YELLOW)
ineq_lbl.to_edge(DOWN, buff=0.6)

self.play(Create(rect), Write(rect_lbl), run_time=1.2)
self.play(Create(sq), Write(sq_lbl), run_time=1.2)
self.play(Write(ineq_lbl))
```

### ALGEBRA -- POLYNOMIAL ROOTS / VIETA'S FORMULAS: CUBIC CURVE + ROOT DOTS
```python
# Use for: ANY problem naming polynomial roots (α,β,γ or a,b,c) and computing an expression.
# "compute E = α²β + β²γ + γ²α", "find α³+β³+γ³", any symmetric/asymmetric root expression.
# !! NEVER text-only. ALWAYS plot the polynomial curve with GOLD dots at roots. !!
# LAYOUT: LEFT = cubic curve + GOLD root dots,  RIGHT = Vieta's formulas + substitution

import math as _math
import numpy as np

# --- Problem-specific constants (replace with actual values) ---
# Polynomial: x^3 - 7x + 6 = 0   roots: alpha=1, beta=2, gamma=-3
def poly(x):
    return x**3 - 7*x + 6    # replace with actual polynomial

roots = [1.0, 2.0, -3.0]                          # replace with actual roots
root_labels = ["alpha=1", "beta=2", "gamma=-3"]   # replace with actual labels
# Vieta's for x^3 + px + q = 0 or general x^3 + ax^2 + bx + c:
s1 = sum(roots)                    # = 0  (coefficient rule)
s2 = roots[0]*roots[1] + roots[1]*roots[2] + roots[2]*roots[0]  # = -7
s3 = roots[0] * roots[1] * roots[2]  # = -6

# LEFT HALF: axes shifted to left half
axes = Axes(
    x_range=[-4.5, 4.5, 1],
    y_range=[-15.0, 15.0, 5],
    x_length=5.5,
    y_length=5.0,
    axis_config={"color": GRAY_A, "stroke_width": 1.5, "include_ticks": False},
).shift(LEFT*2.5 + DOWN*0.3)

# Axis labels with loops
for xv in range(-4, 5):
    xl = Text(str(xv), font_size=14, color=GRAY_B)
    xl.next_to(axes.c2p(xv, 0), DOWN, buff=0.10)
    self.add(xl)
for yv in [-10, -5, 0, 5, 10]:
    yl = Text(str(yv), font_size=14, color=GRAY_B)
    yl.next_to(axes.c2p(-4.5, yv), LEFT, buff=0.10)
    self.add(yl)
x_lbl = Text("x", font_size=20, color=GRAY_A).next_to(axes.x_axis.get_right(), RIGHT, buff=0.1)
y_lbl = Text("f(x)", font_size=18, color=YELLOW).next_to(axes.y_axis.get_top(), UP, buff=0.1)

# Cubic curve — clipped to y_range so it doesn't overshoot axes
curve = axes.plot(
    lambda x: max(-14.5, min(poly(x), 14.5)),
    x_range=[-4.2, 4.2, 0.02],
    color=BLUE_C, stroke_width=3
)

# GOLD dots at the roots with vertical dashed lines and labels
root_dots, root_dashes, root_lbls = VGroup(), VGroup(), VGroup()
label_dirs = [UR, UR, UL]   # adjust per root positions to avoid overlap
for r, lbl_str, ldir in zip(roots, root_labels, label_dirs):
    dot = Dot(axes.c2p(r, 0.0), radius=0.18, color=GOLD, z_index=3)
    dash = DashedLine(axes.c2p(r, -14.0), axes.c2p(r, 0.0),
                      color=GOLD, stroke_width=1.8, dash_length=0.14)
    lbl = Text(lbl_str, font_size=17, color=GOLD)
    lbl.next_to(dot, ldir, buff=0.12)
    root_dots.add(dot); root_dashes.add(dash); root_lbls.add(lbl)

self.play(Create(axes), Write(x_lbl), Write(y_lbl), run_time=1.0)
self.play(Create(curve), run_time=2.5)
self.wait(1.5)
for dot, dash, lbl in zip(root_dots, root_dashes, root_lbls):
    self.play(GrowFromCenter(dot), Create(dash), Write(lbl), run_time=0.8)
    self.play(Flash(dot, color=GOLD, flash_radius=0.40, line_length=0.18), run_time=0.5)
self.wait(2.0)

# RIGHT HALF: Vieta's formulas + substitution steps
vt_title = Text("Vieta's Formulas:", font_size=24, color=YELLOW)
vt1 = Text("s1: alpha+beta+gamma = " + str(int(s1)),         font_size=22, color=TEAL)
vt2 = Text("s2: ab+bg+ga = " + str(int(s2)),                 font_size=22, color=TEAL)
vt3 = Text("s3: alpha*beta*gamma = " + str(int(s3)),         font_size=22, color=TEAL)
# Computation steps for E = α²β + β²γ + γ²α (adapt for actual expression)
e1 = Text("E = alpha^2*beta + beta^2*gamma + gamma^2*alpha", font_size=19, color=WHITE)
e2 = Text("  = (1)^2*(2) + (2)^2*(-3) + (-3)^2*(1)",        font_size=20, color=TEAL)
e3 = Text("  = 2 - 12 + 9",                                  font_size=22, color=TEAL)
e4 = Text("  = -1",                                          font_size=28, color=GOLD, weight="BOLD")

eq_stack = VGroup(vt_title, vt1, vt2, vt3, e1, e2, e3, e4).arrange(DOWN, buff=0.28, aligned_edge=LEFT)
eq_stack.move_to(RIGHT*2.8 + UP*0.5)

self.play(Write(vt_title), run_time=0.6)
self.wait(1.0)
for step in [vt1, vt2, vt3]:
    self.play(Write(step), run_time=0.8); self.wait(1.8)
self.play(Indicate(root_dots, color=GOLD, scale_factor=1.3), run_time=0.6)
self.wait(1.0)
for step in [e1, e2, e3]:
    self.play(Write(step), run_time=0.8); self.wait(1.8)
self.play(Write(e4), run_time=1.0)
self.play(Circumscribe(e4, color=GOLD, buff=0.10), run_time=0.8)
self.wait(3.5)
```

### ALGEBRA -- IDENTITY PROOF: D(t) CURVE SHOWING ZEROS + FACTORIZATION CHAIN
```python
# Use for: "prove a^3+b^3+c^3=3abc", "show a^3+b^3=(a+b)(a^2-ab+b^2)", any "prove/verify/show" identity
# STRATEGY: Fix b=c=1, a=t. Plot D(t) = LHS(t,1,1) - RHS(t,1,1).
#           D(t)=0 marks WHEN the identity holds → GOLD dots at the zeros demonstrate the claim.
# For a^3+b^3+c^3=3abc: D(t) = t^3+1+1-3t = t^3-3t+2 = (t-1)^2*(t+2)
#   Zeros: t=1 (a=b=c equality case) and t=-2 (a+b+c=0 condition)
# LAYOUT: LEFT = D(t) curve + zero dots,  RIGHT = factorization step chain

import math as _math
import numpy as np

def D_func(t):
    # D(t) = a^3+b^3+c^3 - 3abc with b=c=1, a=t → replace with actual identity for the problem
    return t**3 - 3*t + 2

# LEFT HALF: axes
axes = Axes(
    x_range=[-3.5, 3.5, 1],
    y_range=[-1.0, 10.0, 2],
    x_length=5.5,
    y_length=5.0,
    axis_config={"color": GRAY_A, "stroke_width": 1.5, "include_ticks": False},
).shift(LEFT*2.5 + DOWN*0.3)

for xv in [-3, -2, -1, 0, 1, 2, 3]:
    Text(str(xv), font_size=16, color=GRAY_B).next_to(axes.c2p(xv, 0), DOWN, buff=0.10)
for yv in [0, 2, 4, 6, 8]:
    Text(str(yv), font_size=16, color=GRAY_B).next_to(axes.c2p(-3.5, yv), LEFT, buff=0.10)
x_lbl = Text("a   (b = c = 1)", font_size=17, color=GRAY_A).next_to(axes.x_axis.get_right(), RIGHT, buff=0.1)
y_lbl = Text("D(a)", font_size=18, color=YELLOW).next_to(axes.y_axis.get_top(), UP, buff=0.1)

# Zero level line — dashed, GRAY_B
zero_line = DashedLine(axes.c2p(-3.5, 0), axes.c2p(3.5, 0),
                       color=GRAY_B, stroke_width=1.5, dash_length=0.15)

# D(t) curve in YELLOW — drawn with Create() so students watch it traced
curve = axes.plot(lambda t: min(D_func(t), 9.5), x_range=[-3.2, 2.8, 0.02],
                  color=YELLOW, stroke_width=3)

# GOLD dots at zeros
zero_dot1 = Dot(axes.c2p(1.0, 0.0), radius=0.18, color=GOLD, z_index=3)
zero_lbl1 = Text("a=b=c=1", font_size=17, color=GOLD)
zero_lbl1.next_to(zero_dot1, UR, buff=0.10)
v_dash1 = DashedLine(axes.c2p(1.0, -0.5), axes.c2p(1.0, 0.0),
                     color=GOLD, stroke_width=2, dash_length=0.13)

zero_dot2 = Dot(axes.c2p(-2.0, 0.0), radius=0.18, color=GOLD, z_index=3)
zero_lbl2 = Text("a+b+c=0", font_size=17, color=GOLD)
zero_lbl2.next_to(zero_dot2, UL, buff=0.10)
v_dash2 = DashedLine(axes.c2p(-2.0, -0.5), axes.c2p(-2.0, 0.0),
                     color=GOLD, stroke_width=2, dash_length=0.13)

self.play(Create(axes), Write(x_lbl), Write(y_lbl), Create(zero_line), run_time=1.2)
self.play(Create(curve), run_time=2.5)
self.wait(1.5)   # AUDIO: "we plot D(a) — where this curve hits zero is where the identity holds"
self.play(GrowFromCenter(zero_dot1), Write(zero_lbl1), Create(v_dash1), run_time=1.0)
self.play(Flash(zero_dot1, color=GOLD, flash_radius=0.45, line_length=0.20), run_time=0.6)
self.wait(1.5)   # AUDIO: "at a=1 the three variables are equal — equality case"
self.play(GrowFromCenter(zero_dot2), Write(zero_lbl2), Create(v_dash2), run_time=1.0)
self.play(Flash(zero_dot2, color=GOLD, flash_radius=0.45, line_length=0.20), run_time=0.6)
self.wait(2.5)   # AUDIO: "at a=-2 we have a+b+c=0 — that is the key condition"

# RIGHT HALF: factorization proof chain — one line at a time with waits
eq1 = Text("a^3+b^3+c^3 - 3abc",                   font_size=22, color=WHITE)
eq2 = Text("= (a+b+c)(a^2+b^2+c^2",                font_size=22, color=TEAL)
eq3 = Text("         - ab - bc - ca)",              font_size=22, color=TEAL)
eq4 = Text("When a + b + c = 0:",                   font_size=22, color=YELLOW)
eq5 = Text("= 0 * (a^2+b^2+c^2-ab-bc-ca)",         font_size=22, color=TEAL)
eq6 = Text("= 0",                                   font_size=22, color=TEAL)
eq7 = Text("=> a^3 + b^3 + c^3 = 3abc",            font_size=26, color=GOLD, weight="BOLD")

eq_stack = VGroup(eq1, eq2, eq3, eq4, eq5, eq6, eq7).arrange(DOWN, buff=0.30, aligned_edge=LEFT)
eq_stack.move_to(RIGHT*2.8 + UP*0.5)

self.play(Write(eq1), run_time=0.8)
self.wait(1.5)
self.play(Write(eq2), run_time=0.8)
self.play(Write(eq3), run_time=0.8)
self.play(Circumscribe(VGroup(eq2, eq3), color=TEAL, buff=0.08), run_time=0.8)
self.wait(2.0)   # AUDIO: "we factor using the standard factorization identity"
self.play(Write(eq4), run_time=0.8)
self.play(Indicate(zero_dot2, color=GOLD, scale_factor=1.5), run_time=0.6)
self.wait(2.0)   # AUDIO: "when a+b+c=0 the first factor is zero"
self.play(Write(eq5), run_time=0.8)
self.play(Write(eq6), run_time=0.6)
self.wait(1.5)
self.play(Write(eq7), run_time=1.0)
self.play(Circumscribe(eq7, color=GOLD, buff=0.10), run_time=0.8)
self.play(Indicate(zero_dot2, color=GOLD, scale_factor=1.3), run_time=0.6)
self.wait(3.5)   # AUDIO: "therefore a cubed plus b cubed plus c cubed equals 3abc — proved!"
```

### ALGEBRA -- THREE-VARIABLE SYSTEM: 2D AXES + CIRCLE (primary template)
```python
# Use for: ANY problem with 3 unknowns (x+y+z=S1, x^2+y^2+z^2=S2, find xy+yz+zx).
# Visual: GOLD circle growing from centroid on 2D axes + step-by-step algebra.
# Regular Scene (NOT ThreeDScene). Renders in ~45s at 720p30.
# Each self.wait() is calibrated for audio sync — do NOT reduce them.

import math as _math
import numpy as np

# Geometric values — replace S1/S2 with the actual problem constants
S1 = 6.0; S2 = 14.0
r_int = _math.sqrt(S2 - S1**2 / 3)   # intersection circle radius = sqrt(2)
cx, cy = S1/3, S1/3                   # centroid projected to xy-plane = (2, 2)

bg = Rectangle(width=16, height=9, fill_color=BLACK, fill_opacity=1)
self.add(bg)

# ── SCENE 1: Problem statement ───────────────────────────────────────────────
title = Text("3-Variable Algebra Identity", font_size=44)
title.set_color_by_gradient(YELLOW, ORANGE)
title.to_edge(UP, buff=0.4)
self.play(Write(title), run_time=1.2)

# NOTE: replace the string literals below with the actual constraint values from the problem
given1 = Text("Given:  x + y + z = 6",         font_size=28, color=TEAL)
given2 = Text("        x^2 + y^2 + z^2 = 14",  font_size=28, color=BLUE_C)
find_q = Text("Find:   xy + yz + zx = ?",       font_size=28, color=YELLOW)
prob_group = VGroup(given1, given2, find_q).arrange(DOWN, buff=0.38, aligned_edge=LEFT)
prob_group.move_to(ORIGIN)
self.play(FadeIn(given1), run_time=0.7)
self.play(FadeIn(given2), run_time=0.7)
self.play(FadeIn(find_q), run_time=0.7)
self.wait(4.0)   # AUDIO: narrator reads the two constraints and the question

# ── SCENE 2: Axes + constraint line + circle GROWS from centroid ─────────────
self.play(FadeOut(prob_group), run_time=0.6)

axes = Axes(
    x_range=[-0.5, 5.0, 1], y_range=[-0.5, 5.0, 1],
    x_length=5.5, y_length=5.5,
    axis_config={"color": GRAY_A, "stroke_width": 1.5, "include_ticks": False},
).shift(LEFT * 2.8 + DOWN * 0.3)
x_lbl = Text("x", font_size=22, color=GRAY_A).next_to(axes.x_axis.get_right(), RIGHT, buff=0.1)
y_lbl = Text("y", font_size=22, color=GRAY_A).next_to(axes.y_axis.get_top(), UP, buff=0.1)
x_ticks = VGroup(*[Text(str(v), font_size=16, color=GRAY_A).next_to(axes.c2p(v, 0), DOWN, buff=0.12)
                   for v in [1, 2, 3, 4]])
y_ticks = VGroup(*[Text(str(v), font_size=16, color=GRAY_A).next_to(axes.c2p(0, v), LEFT, buff=0.12)
                   for v in [1, 2, 3, 4]])
self.play(Create(axes), Write(x_lbl), Write(y_lbl), run_time=1.0)
self.play(FadeIn(x_ticks), FadeIn(y_ticks), run_time=0.5)

# Constraint line: x+y = 2*S1/3 (linear constraint cross-section at z = S1/3)
# NOTE: update the label string below if S1 changes from 6
plane_line = axes.plot(lambda x: 2*S1/3 - x, x_range=[0.0, 2*S1/3, 0.05], color=ORANGE, stroke_width=2.5)
plane_lbl  = Text("x+y = 4  (z fixed at 2)", font_size=18, color=ORANGE)
plane_lbl.next_to(axes.c2p(0.4, 2*S1/3 - 0.4), UR, buff=0.08)
self.play(Create(plane_line), run_time=1.2)
self.play(FadeIn(plane_lbl), run_time=0.5)
self.wait(2.5)   # AUDIO: "the orange line shows the linear constraint x+y+z=6"

# Centroid dot appears
center_dot = Dot(axes.c2p(cx, cy), radius=0.12, color=YELLOW)
center_lbl = Text("centroid (2, 2, 2)", font_size=17, color=YELLOW)
center_lbl.next_to(center_dot, UR, buff=0.08)
self.play(GrowFromCenter(center_dot), run_time=0.6)
self.play(FadeIn(center_lbl), run_time=0.4)
self.wait(2.0)   # AUDIO: "the symmetric point is x = y = z = 2"

# Circle GROWS from centroid — visual: both constraints together determine this radius
final_radius = r_int * axes.get_x_unit_size()
circle_2d = Circle(radius=final_radius, color=GOLD, stroke_width=4)
circle_2d.move_to(axes.c2p(cx, cy))
self.play(GrowFromCenter(circle_2d), run_time=1.5)
self.play(circle_2d.animate.set_stroke(width=8, color=WHITE), run_time=0.25)
self.play(circle_2d.animate.set_stroke(width=4, color=GOLD),  run_time=0.25)
# NOTE: update r label if r_int changes
r_lbl = Text("r = sqrt(2)", font_size=18, color=GOLD)
r_lbl.next_to(axes.c2p(cx + 0.6, cy + 0.9), RIGHT, buff=0.05)
self.play(FadeIn(r_lbl), run_time=0.4)
self.wait(3.0)   # AUDIO: "the gold circle is the solution set; radius = sqrt(S2 - S1^2/3)"

# RIGHT HALF: key identity appears
identity_hdr = Text("Key Identity:", font_size=22, color=YELLOW).move_to(RIGHT*2.8 + UP*2.8)
identity     = Text("(x+y+z)^2 = x^2+y^2+z^2 + 2(xy+yz+zx)", font_size=19, color=WHITE)
identity.move_to(RIGHT*2.8 + UP*2.1)
self.play(FadeIn(identity_hdr), Write(identity), run_time=1.2)
self.play(Circumscribe(identity, color=TEAL, buff=0.08), run_time=0.8)
self.wait(2.5)   # AUDIO: "we expand (x+y+z)^2 using this identity"

# ── SCENE 3: Step-by-step substitution with highlights ───────────────────────
sub_hdr = Text("Substitute known values:", font_size=22, color=YELLOW).move_to(RIGHT*2.8 + UP*1.2)
self.play(FadeIn(sub_hdr), run_time=0.5)

# NOTE: replace the hardcoded numbers below with the actual values for the problem
# S1=6  ->  S1^2 = 36
# S2=14 ->  S1^2 - S2 = 22  ->  answer = 22/2 = 11
step1 = Text("(6)^2 = 14 + 2(xy+yz+zx)", font_size=22, color=WHITE)
step2 = Text("36    = 14 + 2(xy+yz+zx)", font_size=22, color=WHITE)
step3 = Text("36 - 14 = 2(xy+yz+zx)",   font_size=22, color=WHITE)
step4 = Text("22 = 2(xy+yz+zx)",         font_size=22, color=WHITE)
step5 = Text("xy + yz + zx = 11",        font_size=26, color=GOLD, weight="BOLD")
steps = VGroup(step1, step2, step3, step4, step5).arrange(DOWN, buff=0.28, aligned_edge=LEFT)
steps.move_to(RIGHT*2.8 + DOWN*0.2)

self.play(Write(step1), run_time=1.0)
self.play(Indicate(plane_line, color=TEAL, scale_factor=1.03), run_time=0.6)
self.wait(2.0)   # AUDIO: "x+y+z = 6, so the left side is 6 squared = 36"

self.play(Write(step2), run_time=0.8)
self.wait(2.0)   # AUDIO: "that gives us 36 on the left, 14 plus the expression on the right"

self.play(Write(step3), run_time=0.8)
self.wait(1.5)   # AUDIO: "move 14 to the left side"

self.play(Write(step4), run_time=0.8)
self.wait(1.5)   # AUDIO: "36 minus 14 = 22"

self.play(Write(step5), run_time=1.0)
self.play(Circumscribe(step5, color=GOLD, buff=0.1), run_time=0.8)
self.play(Indicate(circle_2d, color=GOLD, scale_factor=1.06), run_time=0.6)
self.wait(3.5)   # AUDIO: "divide both sides by 2 — xy+yz+zx = 11!"

# ── SCENE 4: Answer reveal ───────────────────────────────────────────────────
self.play(FadeOut(Group(*self.mobjects)), run_time=0.8)
self.add(bg.copy())
# NOTE: replace "11" below with the actual answer = (S1^2 - S2) / 2
ans_lbl = Text("xy + yz + zx = 11", font_size=96)
ans_lbl.set_color_by_gradient(YELLOW, ORANGE)
ans_box = SurroundingRectangle(ans_lbl, color=GOLD, buff=0.4, corner_radius=0.1)
VGroup(ans_lbl, ans_box).center()
self.play(GrowFromCenter(ans_lbl), Create(ans_box), run_time=1.2)
self.play(Flash(ans_lbl.get_center(), color=GOLD, flash_radius=3.0, num_lines=22), run_time=1.5)
self.wait(8.0)   # AUDIO: final narration finishes here — must keep at 8.0 minimum
```

### BINOMIAL THEOREM -- SCATTER-LINE TERM CHART (mandatory pattern)
CRITICAL RULES:
- x-axis = integer k values 0,1,...,n ONLY. NO fractional ticks. NO include_numbers.
- Add Text labels for every integer k using a loop (see code below).
- Use Dot + VMobject polyline (scatter-line), NOT bars/Rectangles.
- Target term (k where net x-power == target): gold Dot + gold dashed vertical line.
```python
# --- compute net x-power for each k in (a*x^p + b*x^q)^n ---
# Example: (2x - 1/x)^8 => p=1, q=-1, n=8, target_power=5
n_val = 8; a_pow = 1; b_pow = -1; target_power = 5
k_vals  = list(range(n_val + 1))
x_pows  = [a_pow*(n_val - k) + b_pow*k for k in k_vals]
target_k = next(k for k, p in zip(k_vals, x_pows) if p == target_power)

# --- axes: NO include_numbers, NO add_coordinates ---
axes = Axes(
    x_range=[-0.5, n_val + 0.5, 1],
    y_range=[min(x_pows) - 1, max(x_pows) + 1, 1],
    x_length=8, y_length=5,
    axis_config={"color": GRAY_A, "stroke_width": 2, "include_ticks": False},
).shift(DOWN*0.2)
x_lbl = Text("k (term index)", font_size=22, color=GRAY_A).next_to(
    axes.x_axis.get_right(), RIGHT, buff=0.12)
y_lbl = Text("power of x", font_size=22, color=GRAY_A).rotate(PI/2).next_to(
    axes.y_axis.get_top(), UP, buff=0.12)
# Integer k labels on x-axis
k_labels = VGroup(*[
    Text(str(k), font_size=17, color=GRAY_A).next_to(axes.c2p(k, 0), DOWN, buff=0.15)
    for k in k_vals
])
# Integer power labels on y-axis
y_labels = VGroup(*[
    Text(str(p), font_size=17, color=GRAY_A).next_to(axes.c2p(0, p), LEFT, buff=0.15)
    for p in sorted(set(x_pows))
])

# --- scatter-line: dots + connecting polyline ---
dot_pts = [axes.c2p(k, p) for k, p in zip(k_vals, x_pows)]
line_path = VMobject(color=BLUE_B, stroke_width=2.5)
line_path.set_points_as_corners(dot_pts)
dots = VGroup(*[
    Dot(axes.c2p(k, p), radius=0.14,
        color=GOLD if k == target_k else BLUE_C, fill_opacity=1)
    for k, p in zip(k_vals, x_pows)
])

# --- target highlight ---
v_line = DashedLine(
    axes.c2p(target_k, min(x_pows) - 0.5), axes.c2p(target_k, target_power),
    color=GOLD, stroke_width=2.5)
k_tag = Text("k=" + str(target_k), font_size=20, color=GOLD).next_to(
    axes.c2p(target_k, 0), DOWN, buff=0.38)

self.play(Create(axes), Write(x_lbl), Write(y_lbl),
          FadeIn(k_labels), FadeIn(y_labels))
self.play(Create(line_path), run_time=1.8)
self.play(LaggedStart(*[GrowFromCenter(d) for d in dots], lag_ratio=0.12), run_time=1.5)
self.play(Create(v_line), Indicate(dots[target_k], scale_factor=1.7, color=GOLD))
self.play(Write(k_tag))
```

### SLOPE BETWEEN TWO POINTS
```python
x1, y1, x2, y2 = 2, 3, 4, 7
m_num = y2 - y1
m_den = x2 - x1
m_val = m_num / m_den
axes = Axes(
    x_range=[0, 6, 1], y_range=[0, 9, 1],
    x_length=6.5, y_length=5.5,
    axis_config={"color": GRAY_A, "stroke_width": 2},
).shift(LEFT*0.8 + DOWN*0.4)
for xv in range(0, 7):
    Text(str(xv), font_size=16, color=GRAY_A).next_to(axes.c2p(xv,0), DOWN, buff=0.12)
for yv in range(0, 10, 2):
    Text(str(yv), font_size=16, color=GRAY_A).next_to(axes.c2p(0,yv), LEFT, buff=0.12)
p1_dot = Dot(axes.c2p(x1, y1), radius=0.14, color=YELLOW)
p2_dot = Dot(axes.c2p(x2, y2), radius=0.14, color=ORANGE)
the_line = Line(axes.c2p(x1, y1), axes.c2p(x2, y2), color=BLUE_C, stroke_width=3)
run_line  = Line(axes.c2p(x1, y1), axes.c2p(x2, y1), color=GREEN_C, stroke_width=4)
rise_line = Line(axes.c2p(x2, y1), axes.c2p(x2, y2), color=RED, stroke_width=4)
run_lbl   = Text("run=" + str(m_den), font_size=24, color=GREEN_C).next_to(run_line, DOWN, buff=0.14)
rise_lbl  = Text("rise=" + str(m_num), font_size=24, color=RED).next_to(rise_line, RIGHT, buff=0.12)
eq_steps = VGroup(
    Text("m = rise/run", font_size=36, color=WHITE),
    Text("m = " + str(m_num) + "/" + str(m_den), font_size=36, color=YELLOW),
    Text("m = " + str(int(m_val) if m_val == int(m_val) else m_val), font_size=52, color=GOLD, weight="BOLD"),
).arrange(DOWN, buff=0.4, aligned_edge=LEFT).to_edge(RIGHT).shift(LEFT*0.3)
```

### BALANCE SCALE (Algebra escape-room style)
```python
def make_scale(self):
    pole  = Line(DOWN*1.5, UP*0.5, color=GRAY_A, stroke_width=6)
    beam  = Line(LEFT*2, RIGHT*2, color=GRAY_A, stroke_width=4).shift(UP*0.5)
    pan_l = RoundedRectangle(width=1.4, height=0.15, corner_radius=0.05,
                              color=GOLD, fill_color=GOLD, fill_opacity=1).move_to(beam.get_left()+DOWN*0.08)
    pan_r = pan_l.copy().move_to(beam.get_right()+DOWN*0.08)
    base  = RoundedRectangle(width=0.6, height=0.2, corner_radius=0.05,
                              color=GRAY_D, fill_color=GRAY_D, fill_opacity=1).move_to(pole.get_bottom())
    return VGroup(pole, beam, pan_l, pan_r, base), pan_l, pan_r
```

### ALGEBRA -- 3D SURFACE PLOT (ThreeDScene for richer algebra visualization)
```python
# Use for: 3-variable algebra, surface plots, "find critical points of f(x,y)",
#          "minimize f(x,y)", "show the constraint surface x^2+y^2+z^2=R^2"
# CRITICAL: ALL Text() MUST use self.add_fixed_in_frame_mobjects() — otherwise
#           text rotates with the camera and becomes unreadable.
# Class: MathAnimationScene(ThreeDScene)   ← NOT Scene!

import numpy as np

class MathAnimationScene(ThreeDScene):
    def construct(self):
        self.camera.background_color = BLACK
        self.set_camera_orientation(phi=70*DEGREES, theta=-50*DEGREES)

        # Fixed-frame title (must be added BEFORE or just after creation)
        title = Text("Surface Plot", font_size=38, color=YELLOW)
        title.to_corner(UL).shift(RIGHT*0.3 + DOWN*0.1)
        self.add_fixed_in_frame_mobjects(title)
        self.play(FadeIn(title), run_time=0.6)

        # 3D axes (occupies left/center — camera angle naturally frames this)
        axes = ThreeDAxes(
            x_range=[-2.5, 2.5, 1],
            y_range=[-2.5, 2.5, 1],
            z_range=[-0.5, 7.0, 1],
            x_length=5.0, y_length=5.0, z_length=4.5,
            axis_config={"color": GRAY_A, "stroke_width": 1.5},
        )
        # Axis labels (3D objects — they move with the axes, always readable)
        x_lbl = Text("x", font_size=22, color=GRAY_A)
        x_lbl.next_to(axes.x_axis.get_right(), RIGHT, buff=0.1)
        y_lbl = Text("y", font_size=22, color=GRAY_A)
        y_lbl.next_to(axes.y_axis.get_end(), UP, buff=0.1)
        z_lbl = Text("z", font_size=22, color=GRAY_A)
        z_lbl.next_to(axes.z_axis.get_top(), UP, buff=0.1)

        # Color-mapped surface — replace lambda with actual problem function
        def f(u, v):
            return u**2 + v**2   # example: z = x^2 + y^2 (paraboloid)

        surface = Surface(
            lambda u, v: axes.c2p(u, v, f(u, v)),
            u_range=[-2.2, 2.2], v_range=[-2.2, 2.2],
            resolution=(28, 28),
            stroke_color=WHITE, stroke_width=0.3,
        )
        surface.set_fill_by_value(
            axes=axes,
            colorscale=[(BLUE_C, -0.5), (TEAL, 2.5), (YELLOW, 5.0), (RED, 7.0)],
            axis=2,
        )

        # Equation steps on RIGHT side — ALL must be fixed_in_frame
        step1 = Text("f(x,y) = x^2 + y^2",   font_size=24, color=WHITE)
        step2 = Text("Min at (0, 0, 0)",       font_size=24, color=GREEN_C)
        step3 = Text("All z >= 0",             font_size=24, color=TEAL)
        answer = Text("Min value = 0",         font_size=30, color=GOLD, weight="BOLD")
        steps = VGroup(step1, step2, step3, answer).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        steps.move_to(RIGHT*4.0 + UP*0.3)
        self.add_fixed_in_frame_mobjects(steps)   # MANDATORY for all text in ThreeDScene

        # Animate
        self.play(Create(axes), Write(x_lbl), Write(y_lbl), Write(z_lbl), run_time=1.5)
        self.wait(1.0)
        self.begin_ambient_camera_rotation(rate=0.08)
        self.play(Create(surface), run_time=3.0)
        self.wait(2.0)
        self.play(Write(step1), run_time=0.8); self.wait(1.5)
        self.play(Write(step2), run_time=0.8); self.wait(1.5)
        self.play(Write(step3), run_time=0.8); self.wait(1.5)
        self.play(Write(answer), run_time=1.0)
        self.play(Circumscribe(answer, color=GOLD, buff=0.1), run_time=0.8)
        self.wait(4.0)
        self.stop_ambient_camera_rotation()
        self.wait(2.0)
```

### ALGEBRA -- 3D SPHERE + PLANE (for x+y+z=S1, x^2+y^2+z^2=S2 type problems)
```python
# Use for: 3-variable systems where showing the sphere and cutting plane is illuminating.
# Shows: sphere x^2+y^2+z^2=S2 (BLUE_C) + plane x+y+z=S1 (TEAL, semi-transparent)
# The intersection circle is where solutions live — connects 3D geometry to algebra.
# Class: MathAnimationScene(ThreeDScene)

import numpy as np

class MathAnimationScene(ThreeDScene):
    def construct(self):
        self.camera.background_color = BLACK
        self.set_camera_orientation(phi=65*DEGREES, theta=-40*DEGREES)

        S1, S2 = 6.0, 14.0   # replace with actual problem values
        R = np.sqrt(S2)       # sphere radius = sqrt(14) ≈ 3.74

        # Fixed-frame title
        title = Text("3D Constraint Visualization", font_size=34, color=YELLOW)
        title.to_corner(UL).shift(RIGHT*0.2 + DOWN*0.1)
        self.add_fixed_in_frame_mobjects(title)
        self.play(FadeIn(title), run_time=0.5)

        # 3D axes
        axes = ThreeDAxes(
            x_range=[-5, 5, 1], y_range=[-5, 5, 1], z_range=[-5, 5, 1],
            x_length=6.0, y_length=6.0, z_length=6.0,
            axis_config={"color": GRAY_A, "stroke_width": 1.5},
        )

        # Sphere: x^2 + y^2 + z^2 = S2
        sphere = Surface(
            lambda u, v: axes.c2p(
                R * np.sin(v) * np.cos(u),
                R * np.sin(v) * np.sin(u),
                R * np.cos(v),
            ),
            u_range=[0, TAU], v_range=[0, PI],
            resolution=(24, 24),
            fill_color=BLUE_C, fill_opacity=0.22,
            stroke_color=BLUE_C, stroke_width=0.5,
        )

        # Plane: x + y + z = S1  (rendered as a square patch tilted to the plane)
        n = np.array([1, 1, 1]) / np.sqrt(3)   # unit normal to x+y+z=S1
        d = S1 / np.sqrt(3)                     # distance from origin
        # Two tangent vectors in the plane
        t1 = np.array([1, -1, 0]) / np.sqrt(2)
        t2 = np.cross(n, t1)
        half = R * 1.3   # patch half-width
        plane = Surface(
            lambda u, v: axes.c2p(*(d * n + u * half * t1 + v * half * t2)),
            u_range=[-1, 1], v_range=[-1, 1],
            resolution=(8, 8),
            fill_color=TEAL, fill_opacity=0.30,
            stroke_color=TEAL, stroke_width=0.5,
        )

        # Fixed-frame equation steps
        s1 = Text("Given: x+y+z = 6",         font_size=22, color=TEAL)
        s2 = Text("       x^2+y^2+z^2 = 14",  font_size=22, color=BLUE_C)
        s3 = Text("Sphere radius = sqrt(14)",   font_size=22, color=BLUE_C)
        s4 = Text("Plane: x+y+z = 6",          font_size=22, color=TEAL)
        s5 = Text("(x+y+z)^2 = 36",            font_size=22, color=WHITE)
        s6 = Text("36 = 14 + 2(xy+yz+zx)",     font_size=22, color=YELLOW)
        s7 = Text("xy + yz + zx = 11",         font_size=28, color=GOLD, weight="BOLD")
        steps = VGroup(s1, s2, s3, s4, s5, s6, s7).arrange(DOWN, buff=0.38, aligned_edge=LEFT)
        steps.move_to(RIGHT*4.2 + UP*0.5)
        self.add_fixed_in_frame_mobjects(steps)  # ALL text must be fixed_in_frame

        # Animate
        self.play(Create(axes), run_time=1.2)
        self.begin_ambient_camera_rotation(rate=0.07)
        self.play(Create(sphere), run_time=2.5)
        self.wait(1.5)
        self.play(Create(plane), run_time=1.5)
        self.wait(2.0)
        for s in steps:
            self.play(Write(s), run_time=0.8)
            self.wait(1.8)
        self.play(Circumscribe(s7, color=GOLD, buff=0.1), run_time=0.8)
        self.wait(4.0)
        self.stop_ambient_camera_rotation()
        self.wait(2.0)
```

### ALGEBRA -- LOGARITHMIC EQUATIONS: log function plot + domain boundary + RHS line + solution dot
# Use for: "solve log_b(x)+log_b(x-a)=c", "log(x+3)=2", "ln(x)+ln(x-1)=0", any log equation.
# MANDATORY VISUAL: plot the combined log function on LEFT half — NEVER text-only.
# CRITICAL BUG TO AVOID: NEVER use Line(p1,p2,p3,p4) for shading — Line() takes EXACTLY 2 points.
#   Use DashedLine for the domain boundary and RHS line; use Polygon() if shading is needed.
# LAYOUT: LEFT half = log curve + RED domain line + ORANGE RHS line + GOLD solution dot
#         RIGHT half = algebra steps (domain → combine logs → exponential → quadratic → reject)
```python
import numpy as np
import math as _math

# --- Problem-specific constants — adapt all of these to the actual problem ---
LOG_BASE  = 2      # base: 2 for log₂, np.e for ln, 10 for log₁₀
SHIFT     = 2.0    # second log term shift: log(x) + log(x - SHIFT) = RHS_VAL
RHS_VAL   = 3.0    # right-hand side constant
SOL_X     = 4.0    # the valid solution (solve x(x-SHIFT)=LOG_BASE^RHS_VAL, pick x > DOM_BOUND)
DOM_BOUND = SHIFT  # domain boundary: x > SHIFT (both log arguments must be positive)

def log_b(x):
    if x <= 0: return float('nan')
    if LOG_BASE == np.e: return np.log(x)
    if LOG_BASE == 10:   return np.log10(x)
    return np.log(x) / np.log(LOG_BASE)

def f_log(x):
    if x <= 0 or (x - SHIFT) <= 0: return float('nan')
    return log_b(x) + log_b(x - SHIFT)

# LEFT HALF: axes shifted to left half of screen
axes = Axes(
    x_range=[max(0, DOM_BOUND - 0.5), SOL_X + 2.5, 1],
    y_range=[-3.5, RHS_VAL + 2.0, 1],
    x_length=5.5, y_length=5.2,
    axis_config={"color": GRAY_A, "stroke_width": 1.5, "include_ticks": False},
).shift(LEFT*2.5 + DOWN*0.3)

# Axis labels — always use loops, NEVER include_numbers
for xv in range(int(DOM_BOUND), int(SOL_X + 3)):
    Text(str(xv), font_size=16, color=GRAY_B).next_to(axes.c2p(xv, 0), DOWN, buff=0.10)
for yv in range(-3, int(RHS_VAL) + 2):
    Text(str(yv), font_size=16, color=GRAY_B).next_to(axes.c2p(DOM_BOUND + 0.05, yv), LEFT, buff=0.10)
x_lbl = Text("x", font_size=20, color=GRAY_A).next_to(axes.x_axis.get_right(), RIGHT, buff=0.08)
y_lbl = Text("f(x)", font_size=18, color=GREEN_C).next_to(axes.y_axis.get_top(), UP, buff=0.08)

# Log function curve (GREEN_C) — only defined for x > DOM_BOUND
log_curve = axes.plot(f_log, x_range=[DOM_BOUND + 0.05, SOL_X + 2.3, 0.02],
                      color=GREEN_C, stroke_width=3)

# Domain boundary: vertical DashedLine at x=DOM_BOUND in RED
# !! NEVER use Line(p1,p2,p3,p4) — Line() takes exactly 2 points. Use DashedLine. !!
dom_line = DashedLine(
    axes.c2p(DOM_BOUND, -3.3), axes.c2p(DOM_BOUND, RHS_VAL + 1.8),
    color=RED, stroke_width=2.0, dash_length=0.14)
dom_lbl  = Text("x > " + str(int(DOM_BOUND)), font_size=17, color=RED)
dom_lbl.next_to(axes.c2p(DOM_BOUND, RHS_VAL + 1.4), RIGHT, buff=0.10)

# RHS horizontal DashedLine at y=RHS_VAL (ORANGE) — shows the equation graphically
rhs_line = DashedLine(
    axes.c2p(DOM_BOUND + 0.05, RHS_VAL), axes.c2p(SOL_X + 2.3, RHS_VAL),
    color=ORANGE, stroke_width=2.5, dash_length=0.14)
rhs_lbl  = Text("y = " + str(int(RHS_VAL)), font_size=20, color=ORANGE)
rhs_lbl.next_to(axes.c2p(SOL_X + 1.5, RHS_VAL), UR, buff=0.08)

# GOLD dot at the solution point (where f(SOL_X) == RHS_VAL)
sol_dot = Dot(axes.c2p(SOL_X, RHS_VAL), radius=0.18, color=GOLD, z_index=4)
v_sol   = DashedLine(axes.c2p(SOL_X, 0), axes.c2p(SOL_X, RHS_VAL),
                     color=GOLD, stroke_width=2.0, dash_length=0.12)
sol_lbl = Text("x = " + str(int(SOL_X)), font_size=22, color=GOLD)
sol_lbl.next_to(axes.c2p(SOL_X, 0), DOWN, buff=0.18)

self.play(Create(axes), Write(x_lbl), Write(y_lbl), run_time=1.0)
self.play(Create(dom_line), Write(dom_lbl), run_time=0.8)
self.wait(1.5)
self.play(Create(log_curve), run_time=2.5)
self.play(Create(rhs_line), Write(rhs_lbl), run_time=0.8)
self.wait(1.5)
self.play(GrowFromCenter(sol_dot), Create(v_sol), Write(sol_lbl), run_time=1.2)
self.play(Flash(sol_dot, color=GOLD, flash_radius=0.5, line_length=0.22), run_time=0.6)

# RIGHT HALF: algebra step chain (adapt strings to actual problem)
eq1  = Text("Domain: x > 0 and x-2 > 0",  font_size=22, color=TEAL)
eq2  = Text("  =>  x > 2",                 font_size=22, color=TEAL)
eq3  = Text("log2(x) + log2(x-2) = 3",     font_size=22, color=WHITE)
eq4  = Text("log2(x(x-2)) = 3",            font_size=22, color=WHITE)
eq5  = Text("x(x-2) = 2^3 = 8",            font_size=22, color=YELLOW)
eq6  = Text("x^2 - 2x - 8 = 0",            font_size=22, color=WHITE)
eq7  = Text("(x-4)(x+2) = 0",              font_size=22, color=WHITE)
eq8  = Text("x = 4  or  x = -2",           font_size=22, color=WHITE)
eq9  = Text("x = -2 < 2  (rejected)",       font_size=22, color=RED)
eq10 = Text("x = 4",                        font_size=28, color=GOLD, weight="BOLD")

eq_stack = VGroup(eq1, eq2, eq3, eq4, eq5, eq6, eq7, eq8, eq9, eq10)
eq_stack.arrange(DOWN, buff=0.28, aligned_edge=LEFT)
eq_stack.move_to(RIGHT*2.8 + UP*0.3)
for eq in eq_stack:
    self.play(Write(eq), run_time=0.8)
    self.wait(1.8)
```

### ALGEBRA -- DIOPHANTINE EQUATION: solve x^2+y^2+z^2=2xyz in integers
```python
# Use for: "solve in integers" multi-variable polynomial equations.
# MANDATORY VISUAL: 2D parity grid on LEFT HALF — ALWAYS include this, no exceptions.
# Proof: parity argument (mod 4) + infinite descent → only x=y=z=0.

# ---------------------------------------------------------------
# LEFT HALF: 2D parity grid (MANDATORY — include even if story plan is text-only)
# ---------------------------------------------------------------
axes = Axes(
    x_range=[-4, 4, 1], y_range=[-4, 4, 1],
    x_length=5.5, y_length=5.5,
    axis_config={"color": GRAY_A, "stroke_width": 1.5, "include_ticks": False},
).shift(LEFT*2.5 + DOWN*0.3)

# Integer axis labels (always use loops, never include_numbers)
x_labels = VGroup(*[
    Text(str(i), font_size=16, color=GRAY_B).next_to(axes.c2p(i, 0), DOWN, buff=0.10)
    for i in range(-3, 4)
])
y_labels = VGroup(*[
    Text(str(i), font_size=16, color=GRAY_B).next_to(axes.c2p(0, i), LEFT, buff=0.10)
    for i in range(-3, 4) if i != 0
])
x_lbl = Text("x", font_size=20, color=GRAY_A).next_to(axes.x_axis.get_right(), RIGHT, buff=0.1)
y_lbl = Text("y", font_size=20, color=GRAY_A).next_to(axes.y_axis.get_top(), UP, buff=0.1)

# PARITY GRID: BLUE_C = (even,even) "candidate" zone; GRAY_B = parity contradiction
even_dots = VGroup()   # both even — these are candidates for solutions
odd_dots  = VGroup()   # one or both odd — parity contradiction

for xi in range(-3, 4):
    for yi in range(-3, 4):
        if xi == 0 and yi == 0:
            continue  # handled separately as GOLD
        if xi % 2 == 0 and yi % 2 == 0:
            even_dots.add(Dot(axes.c2p(xi, yi), radius=0.10, color=BLUE_C, fill_opacity=0.80))
        else:
            odd_dots.add(Dot(axes.c2p(xi, yi), radius=0.07, color=GRAY_B, fill_opacity=0.50))

# GOLD dot at origin — the only final integer solution
origin_dot = Dot(axes.c2p(0, 0), radius=0.22, color=GOLD, z_index=5)
origin_lbl = Text("only solution", font_size=17, color=GOLD).next_to(origin_dot, DR, buff=0.12)

# Parity grid caption
grid_caption = Text("BLUE = both even (candidate zone)", font_size=16, color=BLUE_C)
grid_caption.next_to(axes, DOWN, buff=0.18)

# Animate grid: first odd dots (immediate), then even dots (flash in), then origin
self.play(Create(axes), Write(x_labels), Write(y_labels), Write(x_lbl), Write(y_lbl), run_time=1.5)
self.play(FadeIn(odd_dots), run_time=0.8)
self.play(FadeIn(even_dots), Write(grid_caption), run_time=1.2)
self.play(FadeIn(origin_dot), Write(origin_lbl), run_time=0.8)
self.play(Flash(axes.c2p(0, 0), color=GOLD, flash_radius=0.5, num_lines=12, line_length=0.18))
self.wait(2.0)

# ---------------------------------------------------------------
# RIGHT HALF: parity argument + descent (strictly to the right of x=0)
# ---------------------------------------------------------------
r_title  = Text("Parity Argument:", font_size=22, color=YELLOW)
r_s1     = Text("RHS = 2xyz is even", font_size=21, color=WHITE)
r_s2     = Text("=> x²+y²+z² is even", font_size=21, color=WHITE)
r_s3     = Text("If any var is odd:", font_size=21, color=YELLOW)
r_s4     = Text("  LHS ≡ 2 (mod 4)", font_size=20, color=WHITE)
r_s5     = Text("  RHS ≡ 0 (mod 4)  Contradiction!", font_size=19, color=RED_C)
r_s6     = Text("All x, y, z must be even", font_size=21, color=TEAL)
r_title2 = Text("Infinite Descent:", font_size=22, color=YELLOW)
r_s7     = Text("x=2x_1, y=2y_1, z=2z_1", font_size=20, color=WHITE)
r_s8     = Text("=> x_1²+y_1²+z_1²=4x_1y_1z_1", font_size=20, color=WHITE)
r_s9     = Text("x_1,y_1,z_1 also all even", font_size=20, color=TEAL)
r_s10    = Text("=> divisible by 2^k for all k", font_size=20, color=WHITE)
r_concl  = Text("x = y = z = 0", font_size=24, color=GOLD, weight="BOLD")

eq_stack = VGroup(r_title, r_s1, r_s2, r_s3, r_s4, r_s5, r_s6,
                  r_title2, r_s7, r_s8, r_s9, r_s10, r_concl
                  ).arrange(DOWN, buff=0.24, aligned_edge=LEFT)
eq_stack.move_to(RIGHT*2.8 + UP*0.2)
```\
"""
