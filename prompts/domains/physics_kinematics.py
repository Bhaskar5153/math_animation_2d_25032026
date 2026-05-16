PHYSICS_KINEMATICS_HELPERS = """\
### PHYSICS -- VERTICAL FREE FALL (ball/object dropping straight down under gravity)
```python
# Use for: "object falls from height h, find v at ground", "find time to reach ground"
# Replace h_m, g_m, u_m with actual values from the problem.
import math as _math

h_m = 20.0   # height in metres (from problem)
g_m = 9.8    # gravity acceleration (from problem; may be 10.0)
u_m = 0.0    # initial velocity (0 = dropped from rest; from problem)

# -- Layout: LEFT half = physical scene, RIGHT half = equation panel --

# Ground line across full width
ground_line = Line(LEFT*5.5, RIGHT*5.5, color=GREEN_C, stroke_width=4).shift(DOWN*2.5)
ground_lbl  = Text("Ground", font_size=22, color=GREEN_C).shift(LEFT*2.5 + DOWN*2.85)

# Vertical dashed height axis on LEFT half
height_axis = DashedLine(DOWN*2.5, UP*2.5,
                         color=GRAY_A, stroke_width=2, dash_length=0.18).shift(LEFT*2.8)

# Height brace arrow (double-headed) on the side
h_brace = DoubleArrow(LEFT*3.3 + DOWN*2.5, LEFT*3.3 + UP*2.5,
                      color=YELLOW, buff=0, stroke_width=3,
                      tip_length=0.18, max_tip_length_to_length_ratio=0.08)
h_lbl   = Text("h = " + str(int(h_m)) + " m", font_size=28, color=YELLOW)
h_lbl.next_to(h_brace, LEFT, buff=0.15)

# Ball at top of height axis
ball = Circle(radius=0.3, color=BLUE_C, fill_color=BLUE_C, fill_opacity=1)
ball.move_to(LEFT*2.8 + UP*2.5)
mass_lbl = Text("m = 2 kg", font_size=22, color=WHITE).next_to(ball, RIGHT, buff=0.18)
u_lbl    = Text("u = " + str(int(u_m)) + " m/s", font_size=20, color=GRAY_A)
u_lbl.next_to(ball, UP, buff=0.14)

# Gravity arrow -- starts at ball position, points DOWN
g_arrow = Arrow(ball.get_center(), ball.get_center() + DOWN*1.1,
                color=RED, buff=0, stroke_width=5, max_tip_length_to_length_ratio=0.22)
g_lbl   = Text("g = " + str(g_m) + " m/s²", font_size=22, color=RED)
g_lbl.next_to(g_arrow, RIGHT, buff=0.15)

# -- Build the scene --
self.play(Create(ground_line), Write(ground_lbl))
self.play(Create(height_axis), GrowArrow(h_brace), Write(h_lbl))
self.play(GrowFromCenter(ball), Write(mass_lbl), Write(u_lbl))
self.play(GrowArrow(g_arrow), Write(g_lbl))

# -- Ball falls (animate from start to ground) --
# Gravity arrow and labels shift with the ball:
fall_dist = UP*2.5 - DOWN*2.5  # vector from start to end is DOWN*5
self.play(
    ball.animate.move_to(LEFT*2.8 + DOWN*2.5),
    g_arrow.animate.shift(DOWN*5),
    mass_lbl.animate.shift(DOWN*5),
    u_lbl.animate.shift(DOWN*5),
    g_lbl.animate.shift(DOWN*5),
    run_time=2.5, rate_func=smooth,
)
# Impact flash
self.play(Flash(ball, color=YELLOW, flash_radius=0.7, line_length=0.3))
```

### PHYSICS -- PROJECTILE MOTION (ball launched at angle, parabolic arc LEFT→RIGHT)
```python
# Use for: "ball projected at angle θ, find max height / time of flight / range"
# Layout: stadium background; boy at FAR LEFT edge; ball arcs across; equations on screen.
import math as _math

# Problem parameters -- replace with actual values from the problem
u_ms      = 20.0          # initial speed m/s
theta_deg = 30.0          # launch angle degrees
g_ms2     = 9.8           # gravitational acceleration m/s²

theta = _math.radians(theta_deg)
ux    = u_ms * _math.cos(theta)            # horizontal component (17.32 m/s)
uy    = u_ms * _math.sin(theta)            # vertical component   (10.0 m/s)
T_fl  = 2 * uy / g_ms2                    # time of flight        (2.04 s)
R_m   = ux * T_fl                          # horizontal range      (35.35 m)
Hmax  = uy**2 / (2 * g_ms2)               # maximum height        (5.10 m)

# -- Screen coordinate mapping --
# Launch at FAR LEFT, land at FAR RIGHT; peak maps to top of usable screen.
x_launch = -5.5;  x_land = 5.5
y_ground  = -2.0; y_peak = 2.8
sx = (x_land - x_launch) / R_m
sy = (y_peak - y_ground) / Hmax

def proj_pt(t_phys):
    xp = ux * t_phys
    yp = uy * t_phys - 0.5 * g_ms2 * t_phys**2
    return np.array([x_launch + xp * sx, y_ground + yp * sy, 0])

launch_pt = proj_pt(0)
peak_t    = uy / g_ms2
peak_pt   = proj_pt(peak_t)
land_pt   = proj_pt(T_fl)

# -- Stadium background --
sky   = Rectangle(width=16, height=5.5, fill_color="#1a3a5c", fill_opacity=1, stroke_width=0)
sky.shift(UP*1.25)
grass = Rectangle(width=16, height=2.0, fill_color="#2a6e2a", fill_opacity=1, stroke_width=0)
grass.shift(DOWN*3.0)
ground_line = Line(LEFT*7, RIGHT*7, color=GREEN_E, stroke_width=3).move_to(np.array([0, y_ground, 0]))
self.add(sky, grass, ground_line)

# -- Angle arc at launch --
angle_arc = Arc(radius=0.55, start_angle=0, angle=theta, color=YELLOW, stroke_width=2,
                arc_center=launch_pt)
angle_lbl = Text(str(int(theta_deg)) + "°", font_size=18, color=YELLOW)
angle_lbl.move_to(launch_pt + RIGHT*0.72 + UP*0.22)

# -- Dashed parabolic arc --
arc_curve = ParametricFunction(
    lambda s: proj_pt(s * T_fl),
    t_range=[0, 1, 0.008],
    color=YELLOW, stroke_width=2.5,
).set_stroke(dash_lengths=[0.12, 0.06])

# -- Ball (the HERO of the animation) --
ball = Circle(radius=0.22, color=RED, fill_color="#cc2200", fill_opacity=1)
ball.move_to(launch_pt)

# -- Animate ball along arc with ValueTracker --
t_trk = ValueTracker(0.0)
ball.add_updater(lambda m: m.move_to(proj_pt(t_trk.get_value() * T_fl)))
self.add(ball)
self.play(
    Create(arc_curve),
    t_trk.animate.set_value(1.0),
    run_time=3.0, rate_func=smooth,
)
ball.clear_updaters()
self.play(Flash(ball, color=YELLOW, flash_radius=0.55, line_length=0.22))  # landing impact

# -- Velocity vectors at launch point --
tip_u  = launch_pt + np.array([ux, uy, 0]) * sx * 0.7
tip_ux = launch_pt + np.array([ux, 0,  0]) * sx * 0.7
tip_uy = tip_ux    + np.array([0,  uy, 0]) * sy * 0.7
vec_u  = Arrow(launch_pt, tip_u,  color=WHITE,  buff=0, stroke_width=4,
               max_tip_length_to_length_ratio=0.18)
vec_ux = Arrow(launch_pt, tip_ux, color=TEAL,   buff=0, stroke_width=4,
               max_tip_length_to_length_ratio=0.18)
vec_uy = Arrow(tip_ux,    tip_uy, color=ORANGE, buff=0, stroke_width=4,
               max_tip_length_to_length_ratio=0.18)
lbl_u  = Text("u=" + str(int(u_ms)) + "m/s",       font_size=18, color=WHITE ).next_to(vec_u,  UL, buff=0.08)
lbl_ux = Text("ux=" + "{:.2f}".format(ux) + "m/s", font_size=16, color=TEAL  ).next_to(vec_ux, DOWN, buff=0.08)
lbl_uy = Text("uy=" + str(int(uy)) + "m/s",        font_size=16, color=ORANGE).next_to(vec_uy, RIGHT, buff=0.08)

# -- Peak height marker --
peak_dashed = DashedLine(np.array([peak_pt[0], y_ground, 0]), peak_pt,
                         color=WHITE, stroke_width=2, dash_length=0.14)
hmax_lbl    = Text("Hmax", font_size=20, color=YELLOW)
hmax_lbl.next_to(peak_pt, UP, buff=0.1)
vy0_lbl     = Text("vy=0 here", font_size=18, color=TEAL)
vy0_lbl.next_to(peak_pt, RIGHT, buff=0.18)

# -- Three answer boxes (side by side, bottom of screen) --
ans_hmax = Text("Hmax = " + "{:.2f}".format(Hmax) + " m",  font_size=26, color=GREEN_C)
ans_T    = Text("T = "    + "{:.2f}".format(T_fl)  + " s",  font_size=26, color=TEAL)
ans_R    = Text("R = "    + "{:.2f}".format(R_m)   + " m",  font_size=26, color=ORANGE)
ans_row  = VGroup(ans_hmax, ans_T, ans_R).arrange(RIGHT, buff=0.5)
ans_row.move_to(DOWN*1.2)
box_hmax = SurroundingRectangle(ans_hmax, color=GOLD, corner_radius=0.1, buff=0.12)
box_T    = SurroundingRectangle(ans_T,    color=GOLD, corner_radius=0.1, buff=0.12)
box_R    = SurroundingRectangle(ans_R,    color=GOLD, corner_radius=0.1, buff=0.12)
self.play(
    LaggedStart(
        AnimationGroup(FadeIn(ans_hmax), Create(box_hmax)),
        AnimationGroup(FadeIn(ans_T),    Create(box_T)),
        AnimationGroup(FadeIn(ans_R),    Create(box_R)),
        lag_ratio=0.35,
    ), run_time=1.5
)
```\
"""
