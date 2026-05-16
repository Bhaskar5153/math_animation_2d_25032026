SHARED_UI_HELPERS = """\
### FLOATING OBJECT (gentle up-down hover -- use on any mascot or label)
```python
# Add to any object to make it float continuously
def start_float(self, obj, amplitude=0.12, speed=1.0):
    start_y = obj.get_y()
    obj.t_float = 0
    def updater(m, dt):
        m.t_float = getattr(m, "t_float", 0) + dt * speed
        m.set_y(start_y + amplitude * _math.sin(m.t_float * TAU))
    obj.add_updater(updater)
    return obj
# Usage:
# mascot = self.make_human(shirt_color=TEAL, scale=0.8, emotion="happy").to_edge(RIGHT)
# self.add(mascot); self.start_float(mascot)
```

### PARTICLE TRAIL (objects leave sparks as they move)
```python
def particle_trail(self, origin, color=YELLOW, n=8):
    particles = VGroup(*[
        Dot(origin, radius=0.08, color=color, fill_opacity=0.9)
        for _ in range(n)
    ])
    directions = [RIGHT*_math.cos(i*TAU/n) + UP*_math.sin(i*TAU/n) for i in range(n)]
    self.play(LaggedStart(*[
        p.animate.move_to(origin + directions[i]*1.2).set_opacity(0)
        for i, p in enumerate(particles)
    ], lag_ratio=0.05, run_time=0.7))
    self.remove(particles)
```

### GAMING UI -- SCORE COUNTER
```python
class ScoreCounter:
    def __init__(self, scene, start=0, pos=None):
        self.scene = scene
        self.value = start
        pos = pos or (RIGHT*5.5 + UP*3.2)
        label = Text("SCORE", font_size=20, color=GOLD)
        label.set_color_by_gradient(GOLD, ORANGE)
        label.move_to(pos + DOWN*0.35)
        self.display = Text(str(self.value), font_size=34, color=GOLD, weight="BOLD")
        self.display.move_to(pos)
        self.bg = RoundedRectangle(width=1.8, height=1.0, corner_radius=0.1,
                                    color=GOLD, fill_color=GRAY_D, fill_opacity=0.8)
        self.bg.move_to(pos + DOWN*0.1)
        scene.add(self.bg, label, self.display)
    def add(self, pts, new_val=None):
        self.value = new_val if new_val is not None else self.value + pts
        new_disp = Text(str(self.value), font_size=34, color=GOLD, weight="BOLD")
        new_disp.move_to(self.display.get_center())
        self.scene.play(Transform(self.display, new_disp), run_time=0.4)
```

### GAMING UI -- LEVEL UP BURST
```python
def level_up(self, label="LEVEL UP!", color_from=RED, color_to=PURPLE):
    txt = Text(label, font_size=72, color=WHITE, weight="BOLD")
    txt.set_color_by_gradient(color_from, ORANGE, YELLOW, GREEN_C, BLUE, color_to)
    txt.move_to(ORIGIN)
    self.play(GrowFromCenter(txt), run_time=0.5)
    self.play(txt.animate.scale(1.4).set_opacity(0), run_time=0.8)
    self.remove(txt)
```

### GAMING UI -- PUZZLE LOCK (combination lock opening step by step)
```python
def make_lock(self, n_dials=3, unlocked=False, pos=ORIGIN):
    dials = VGroup()
    for i in range(n_dials):
        dial = Circle(radius=0.4, color=GRAY_A, fill_color=GRAY_D, fill_opacity=1, stroke_width=3)
        dial.shift(RIGHT * (i - (n_dials-1)/2) * 1.0 + pos)
        dot = Dot(dial.get_top(), radius=0.08, color=YELLOW if unlocked else RED)
        label = Text(str(i), font_size=24, color=WHITE).move_to(dial.get_center())
        dials.add(VGroup(dial, dot, label))
    body = RoundedRectangle(width=n_dials*1.1, height=1.6, corner_radius=0.12,
                             color=GRAY_D, fill_color=GRAY_D, fill_opacity=0.9)
    body.move_to(pos)
    shackle_color = GREEN_C if unlocked else RED
    shackle = Arc(radius=0.45, start_angle=0, angle=PI,
                  color=shackle_color, stroke_width=8).move_to(pos + UP*0.9)
    return VGroup(body, dials, shackle)
```\
"""
