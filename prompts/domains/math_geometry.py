GEOMETRY_HELPERS = """\
### GEOMETRY -- DISTANCE BETWEEN TWO POINTS (coordinate grid + bouncing ball)
```python
# Use for: "find distance between P1(x1,y1) and P2(x2,y2)"
# LAYOUT: LEFT half (-7 to 0) = coordinate grid   RIGHT half (0 to +7) = equations
# BALL:   yellow ball bounces along the distance line from P1 → P2 (fun visual)
import math as _math

x1, y1 = -2,  5    # P1 -- replace with actual problem values
x2, y2 =  4, -3    # P2 -- replace with actual problem values
dist_val = _math.sqrt((x2-x1)**2 + (y2-y1)**2)
dx, dy = x2-x1, y2-y1

# -- LEFT HALF: compact axes clipped to contain both points + padding --
pad = 1.5
axes = Axes(
    x_range=[min(x1,x2)-pad, max(x1,x2)+pad, 1],
    y_range=[min(y1,y2)-pad, max(y1,y2)+pad, 1],
    x_length=5.8,
    y_length=5.5,   # shorter height keeps upper point below title zone
    axis_config={"color": GRAY_A, "stroke_width": 1.5, "include_ticks": False},
).shift(LEFT*2.5 + DOWN*0.9)   # shifted DOWN so even y=5 dots stay below title

# Integer tick labels (step 2 to avoid crowding)
for val in range(int(min(x1,x2))-1, int(max(x1,x2))+2, 2):
    Text(str(val), font_size=15, color=GRAY_B).next_to(axes.c2p(val, 0), DOWN, buff=0.1)
for val in range(int(min(y1,y2))-1, int(max(y1,y2))+2, 2):
    Text(str(val), font_size=15, color=GRAY_B).next_to(axes.c2p(0, val), LEFT, buff=0.1)

# -- Two point dots --
dot1 = Dot(axes.c2p(x1, y1), radius=0.16, color=ORANGE)
dot2 = Dot(axes.c2p(x2, y2), radius=0.16, color=ORANGE)

# EDGE-SAFE labels: always point TOWARD the screen center, never off-screen.
# P1 is upper-left corner → label goes RIGHT (not LEFT which would clip)
# P2 is lower-right corner → label goes LEFT (not RIGHT which would clip)
lbl1 = Text("P1(" + str(x1) + ", " + str(y1) + ")", font_size=20, color=ORANGE)
lbl2 = Text("P2(" + str(x2) + ", " + str(y2) + ")", font_size=20, color=ORANGE)
lbl1.next_to(dot1, RIGHT, buff=0.14)   # RIGHT keeps label on-screen even at left edge
lbl2.next_to(dot2, LEFT,  buff=0.14)   # LEFT keeps label on-screen even at right edge

# -- The orange distance line (drawn alongside ball) --
dist_line = Line(axes.c2p(x1, y1), axes.c2p(x2, y2), color=ORANGE, stroke_width=3)

# -- BOUNCING BALL from P1 to P2 --
# Ball rolls along the line with 4 decaying bounces (perpendicular to the line)
ball = Circle(radius=0.18, color=YELLOW, fill_color=YELLOW, fill_opacity=1)
ball.move_to(axes.c2p(x1, y1))
p1_s = np.array(axes.c2p(x1, y1))
p2_s = np.array(axes.c2p(x2, y2))
line_vec = p2_s - p1_s
line_len  = float(np.linalg.norm(line_vec))
# Perpendicular unit vector (always points to the "upper" side for visibility)
perp_dir = np.array([-line_vec[1], line_vec[0], 0]) / line_len

t_ball = ValueTracker(0.0)
def _ball_upd(m):
    t = t_ball.get_value()
    pos = p1_s + t * line_vec
    bounce = 0.45 * abs(_math.sin(t * _math.pi * 4)) * (1.0 - t * 0.75)
    m.move_to(pos + perp_dir * bounce)

ball.add_updater(_ball_upd)
self.add(dot1, lbl1, ball)
# Ball rolls while the distance line is drawn
self.play(
    Create(dist_line),
    t_ball.animate.set_value(1.0),
    run_time=2.5, rate_func=linear,
)
ball.clear_updaters()
self.play(Flash(ball, color=YELLOW_A, flash_radius=0.55, line_length=0.25), run_time=0.5)
self.play(Transform(ball, dot2), Write(lbl2), run_time=0.5)  # ball becomes dot2

# -- Right-angle legs (dashed TEAL) --
# corner = (x2, y1) gives the 90-degree corner of the Pythagorean triangle
corner_pt = axes.c2p(x2, y1)
h_leg = DashedLine(axes.c2p(x1, y1), corner_pt,            color=TEAL, stroke_width=2, dash_length=0.14)
v_leg = DashedLine(corner_pt,         axes.c2p(x2, y2),    color=TEAL, stroke_width=2, dash_length=0.14)
# Labels INSIDE the triangle (toward the triangle interior to avoid collisions)
dx_lbl = Text("Δx = " + str(abs(dx)), font_size=18, color=TEAL)
dy_lbl = Text("Δy = " + str(abs(dy)), font_size=18, color=TEAL)
dx_lbl.next_to(h_leg, DOWN, buff=0.10)   # below the horizontal leg (into triangle)
dy_lbl.next_to(v_leg, LEFT, buff=0.10)   # left of the vertical leg (into triangle)

# -- RIGHT HALF: step-by-step equations (x in 1.5..6.5) --
# font_size=25 keeps every line within the right panel even on long formulae
eq0 = Text("d = √[(x2-x1)² + (y2-y1)²]",             font_size=25, color=WHITE)
eq1 = Text("d = √[(" + str(dx) + ")² + (" + str(dy) + ")²]", font_size=25, color=WHITE)
eq2 = Text(f"d = √[{dx**2} + {dy**2}]",               font_size=25, color=YELLOW)
eq3 = Text(f"d = √{dx**2 + dy**2}",                   font_size=25, color=YELLOW)
eq_ans = Text(f"d = {dist_val:.2f} units",             font_size=38, color=GREEN_C)

eq_stack = VGroup(eq0, eq1, eq2, eq3).arrange(DOWN, buff=0.38, aligned_edge=LEFT)
eq_stack.move_to(RIGHT*2.8 + UP*0.8)     # right half, above center (clear of answer)
eq_ans.next_to(eq_stack, DOWN, buff=0.50)
ans_box = SurroundingRectangle(eq_ans, color=GOLD, corner_radius=0.12, buff=0.18)
```

### 3D GEOMETRY (ISOMETRIC PROJECTION -- NEVER use ThreeDScene)
```python
ISO_X = np.array([0.7, -0.35, 0])
ISO_Y = np.array([0.7,  0.35, 0])
ISO_Z = np.array([0.0,  0.9,  0])
def iso(x, y, z): return x*ISO_X + y*ISO_Y + z*ISO_Z
# Plane as shaded Parallelogram:
p_origin = iso(2, 0, 0)
plane_shape = Polygon(
    p_origin, p_origin+ISO_X*2.5, p_origin+ISO_X*2.5+ISO_Y*2.5, p_origin+ISO_Y*2.5,
    color=TEAL, fill_color=TEAL, fill_opacity=0.25, stroke_width=2)
# Point as glowing Dot:
pt_screen = iso(1, 2, 3)
point_dot  = Dot(pt_screen, radius=0.12, color=YELLOW)
# Perpendicular dashed line:
foot = iso(2.0, 1.0, 1.5)
perp = DashedLine(pt_screen, foot, color=ORANGE, stroke_width=3)
```\
"""
