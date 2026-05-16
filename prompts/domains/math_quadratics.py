QUADRATICS_HELPERS = """\
### QUADRATIC -- BOUNCING BALL ARC
```python
# Ball follows parabolic arc -- use ValueTracker for interactive feel
t = ValueTracker(0)
ball = Dot(radius=0.25, color=RED, fill_opacity=1)
# Parabola: y = a*(x-h)**2 + k  with x from 0 to land_x
a_val, h_val, k_val = -0.4, 3.0, 2.5
land_x = h_val + _math.sqrt(-k_val / a_val)
def ball_pos(tracker_val):
    x = tracker_val * land_x
    y = a_val * (x - h_val)**2 + k_val
    return axes.c2p(x, max(0, y))
ball.add_updater(lambda m: m.move_to(ball_pos(t.get_value())))
self.add(ball)
# Trail: leave a path
path = TracedPath(ball.get_center, stroke_color=ORANGE, stroke_width=3, dissipating_time=0.5)
self.add(path)
self.play(t.animate.set_value(1.0), run_time=3.0, rate_func=smooth)
ball.clear_updaters()
```\
"""
