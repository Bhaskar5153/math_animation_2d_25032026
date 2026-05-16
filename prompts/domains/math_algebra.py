ALGEBRA_HELPERS = """\
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
```\
"""
