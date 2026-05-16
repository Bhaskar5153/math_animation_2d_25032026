STATISTICS_HELPERS = """\
### GAUSSIAN / BELL CURVE -- FILLED INTEGRAL (mathematisa style)
CRITICAL RULES:
- Pure BLACK background. No characters.
- Blue bell curve on black; gradient fill under curve.
- Formula below at font_size=42.
- Histogram bars optional (use Rectangle, lower opacity).
```python
# Gaussian: f(x) = exp(-x^2)  plotted on axes
axes_g = Axes(
    x_range=[-3.5, 3.5, 1], y_range=[-0.2, 1.3, 0.5],
    x_length=8.5, y_length=4.5,
    axis_config={"color": GRAY_A, "stroke_width": 2, "tip_length": 0.2},
).shift(DOWN*0.3)
for xv in range(-3, 4):
    Text(str(xv), font_size=16, color=GRAY_A).next_to(axes_g.c2p(xv, 0), DOWN, buff=0.12)

bell = axes_g.plot(lambda x: _math.exp(-x*x), x_range=[-3.3, 3.3, 0.05], color=BLUE_B, stroke_width=3)

# Gradient fill: create rectangles from -3 to 3
fill_rects = VGroup()
for xi in range(-30, 30):
    xv = xi * 0.1
    yv = _math.exp(-xv*xv)
    r = Rectangle(width=0.1, height=yv * axes_g.y_length / 1.3,
                  fill_opacity=0.45, stroke_width=0)
    r.set_fill(color=[BLUE_D, PURPLE], opacity=0.45)
    r.move_to(axes_g.c2p(xv + 0.05, yv / 2))
    fill_rects.add(r)

func_lbl = Text("f(x) = e^-x^2", font_size=30, color=WHITE)
func_lbl.next_to(bell, UR, buff=0.25).shift(LEFT*0.5)

formula = Text("I = integral(-inf to inf) e^-x^2 dx", font_size=34, color=WHITE)
formula.set_color_by_gradient(BLUE_C, PURPLE)
formula.to_edge(DOWN, buff=0.55)

self.play(Create(axes_g))
self.play(FadeIn(fill_rects), run_time=1.5)
self.play(Create(bell), Write(func_lbl), run_time=2.0)
self.play(Write(formula))
```

### STATISTICS -- BAR CHART GROWING
```python
def make_growing_bar(self, height, x_pos, width=0.7, color=BLUE_C, label=""):
    bar = Rectangle(width=width, height=0.01, color=color, fill_color=color, fill_opacity=0.85)
    bar.move_to(RIGHT*x_pos + DOWN*1.5)
    bar_final = Rectangle(width=width, height=height, color=color, fill_color=color, fill_opacity=0.85)
    bar_final.move_to(RIGHT*x_pos + UP*(height/2 - 1.5))
    lbl = Text(label, font_size=20, color=WHITE).next_to(bar_final, DOWN, buff=0.12)
    self.add(bar)
    self.play(bar.animate.become(bar_final), run_time=1.0, rate_func=smooth)
    self.play(FadeIn(lbl, shift=DOWN*0.1))
    return bar, lbl
```

### PIE SLICE (Probability)
```python
def make_pie_slice(self, start_angle, angle, color, label_str):
    sector = AnnularSector(inner_radius=0, outer_radius=2,
                            angle=angle, start_angle=start_angle,
                            color=color, fill_color=color, fill_opacity=0.85,
                            stroke_width=2, stroke_color=WHITE)
    mid_angle = start_angle + angle/2
    lbl_pos = 1.3 * np.array([np.cos(mid_angle), np.sin(mid_angle), 0])
    lbl = Text(label_str, font_size=22, color=WHITE).move_to(lbl_pos)
    return VGroup(sector, lbl)
```

### PEOPLE SCENE (word problems with human characters)
```python
def make_person_with_badge(self, age, color=BLUE_C, badge_color=GOLD, pos=ORIGIN):
    person = self.make_human(color=color, scale=1.0)
    person.move_to(pos)
    badge_bg  = RoundedRectangle(width=0.9, height=0.5, corner_radius=0.08,
                                  color=badge_color, fill_color=badge_color, fill_opacity=1,
                                  stroke_width=2).next_to(person, UP, buff=0.12)
    badge_lbl = Text(str(age), font_size=26, color=BLACK, weight="BOLD").move_to(badge_bg.get_center())
    return VGroup(person, badge_bg, badge_lbl)
```\
"""
