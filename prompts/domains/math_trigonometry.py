TRIGONOMETRY_HELPERS = """\
### TRIGONOMETRY -- UNIT CIRCLE + GRAPH (mathematisa dark-elegance style)
CRITICAL RULES for trig concept animations:
- Pure BLACK background. No characters.
- Unit circle on LEFT half (center ~x=-3.5), graph axes on RIGHT half.
- Dot travels around circle; dashed horizontal line traces to graph.
- TracedPath draws the trig curve in real time as dot moves.
- Label below circle: "sin θ" / "cos θ" / "tan θ" in curve color.
- For sin θ use CYAN; cos θ use PURPLE; tan θ use PINK.
- π and 2π tick labels on x-axis.
```python
import numpy as np as _np  # use _np to avoid conflicts

CURVE_COLOR = CYAN          # change per function: CYAN / PURPLE / PINK
circ_center = LEFT * 3.5    # unit circle center
radius = 1.4                # unit circle radius
g_origin = RIGHT * 0.8      # graph origin point
g_width = 5.5               # graph spans 0 -> 2π mapped to this pixel width

# -- unit circle --
circle = Circle(radius=radius, color=CURVE_COLOR, stroke_width=3)
circle.move_to(circ_center)
c_hax = Line(circ_center+LEFT*1.65, circ_center+RIGHT*1.65, color=GRAY_A, stroke_width=1.5)
c_vax = Line(circ_center+DOWN*1.65, circ_center+UP*1.65,   color=GRAY_A, stroke_width=1.5)
inner = Circle(radius=0.25, color=GRAY_D, fill_color=GRAY_D, fill_opacity=0.6)
inner.move_to(circ_center)

# -- graph axes --
g_xax = Line(g_origin+LEFT*0.2, g_origin+RIGHT*(g_width+0.3), color=GRAY_A, stroke_width=1.5)
g_yax = Line(g_origin+DOWN*1.65, g_origin+UP*1.65, color=GRAY_A, stroke_width=1.5)
pi_tick   = Line(g_origin+RIGHT*(g_width/2)+DOWN*0.09, g_origin+RIGHT*(g_width/2)+UP*0.09,
                 color=GRAY_A, stroke_width=1.5)
two_pi_tick = Line(g_origin+RIGHT*g_width+DOWN*0.09, g_origin+RIGHT*g_width+UP*0.09,
                   color=GRAY_A, stroke_width=1.5)
pi_lbl    = Text("π",  font_size=20, color=GRAY_A).next_to(pi_tick,     DOWN, buff=0.1)
two_pi_lbl = Text("2π", font_size=20, color=GRAY_A).next_to(two_pi_tick, DOWN, buff=0.1)

# -- moving dot and traced curve --
t_trk = ValueTracker(0.0)
def circ_pt(t):
    # sin θ: x=cos(t), y=sin(t)  |  cos θ: x=cos(t), y=cos(t)
    return circ_center + RIGHT*radius*_math.cos(t) + UP*radius*_math.sin(t)
def graph_pt(t):
    return g_origin + RIGHT*(t/(2*PI))*g_width + UP*radius*_math.sin(t)  # change sin->cos for cosθ

c_dot = Dot(radius=0.13, color=CURVE_COLOR, fill_opacity=1)
c_dot.add_updater(lambda m: m.move_to(circ_pt(t_trk.get_value())))
g_dot = Dot(radius=0.13, color=CURVE_COLOR, fill_opacity=1)
g_dot.add_updater(lambda m: m.move_to(graph_pt(t_trk.get_value())))
h_dash = always_redraw(lambda: DashedLine(
    circ_pt(t_trk.get_value()), graph_pt(t_trk.get_value()),
    color=CURVE_COLOR, stroke_width=1.4, dash_length=0.13))
sine_trace = TracedPath(g_dot.get_center, stroke_color=CURVE_COLOR, stroke_width=3)
radius_line = always_redraw(lambda: Line(circ_center, circ_pt(t_trk.get_value()),
                                         color=CURVE_COLOR, stroke_width=2))

self.play(Create(circle), Create(c_hax), Create(c_vax), GrowFromCenter(inner))
self.play(Create(g_xax), Create(g_yax), Write(pi_lbl), Write(two_pi_lbl),
          FadeIn(pi_tick), FadeIn(two_pi_tick))
self.add(radius_line, h_dash, sine_trace, c_dot, g_dot)
self.play(t_trk.animate.set_value(2*PI), run_time=5.0, rate_func=linear)
c_dot.clear_updaters(); g_dot.clear_updaters()

# label below circle
func_lbl = Text("sin θ", font_size=34, color=CURVE_COLOR)  # change for cos/tan
func_lbl.set_color_by_gradient(CYAN, BLUE_B)
func_lbl.next_to(circle, DOWN, buff=0.35)
self.play(Write(func_lbl))
```

### UNIT CIRCLE (Trigonometry)
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
