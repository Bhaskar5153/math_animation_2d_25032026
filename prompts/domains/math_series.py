SERIES_HELPERS = """\
### INFINITE SERIES -- NESTED POLYGONS (geometric / converging series)
CRITICAL RULES:
- Pure BLACK background. No characters.
- Use RegularPolygon (hexagons work well). Each inner polygon is scaled by r < 1.
- For 1/n series: scale each inner polygon by 1/sqrt(n) of the outer side.
- Animate polygons appearing one by one with Create().
- Show the sum formula at top and the answer at bottom.
- Fill innermost polygon last to show convergence.
```python
# Nested hexagons for geometric series  1/7 + 1/7^2 + 1/7^3 + ...
# Visible convergence: each layer scaled by factor r (r < 1)
n_layers   = 6
r_scale    = 0.55          # side ratio between successive hexagons
outer_side = 2.4           # outer hexagon half-width
SERIES_COLOR = TEAL        # main color for hexagons

hexagons = VGroup()
for i in range(n_layers):
    side = outer_side * (r_scale ** i)
    h = RegularPolygon(n=6, start_angle=PI/6,
                       color=SERIES_COLOR, fill_opacity=0, stroke_width=2.5)
    h.scale(side).move_to(ORIGIN + DOWN*0.4)
    hexagons.add(h)

series_lbl = Text("1/7 + 1/7^2 + 1/7^3 + ... = ?", font_size=36, color=WHITE)
series_lbl.set_color_by_gradient(TEAL, GREEN_C)
series_lbl.to_edge(UP, buff=0.5)
self.play(Write(series_lbl))

for i, h in enumerate(hexagons):
    self.play(Create(h), run_time=0.55)
    if i == n_layers - 1:
        # fill innermost to show convergence
        self.play(h.animate.set_fill(SERIES_COLOR, opacity=0.7), run_time=0.4)

answer_lbl = Text("= 1/6", font_size=46, color=TEAL)
answer_lbl.set_color_by_gradient(TEAL, GREEN_C)
answer_lbl.to_edge(DOWN, buff=0.6)
self.play(Write(answer_lbl), Flash(hexagons[0], color=TEAL, flash_radius=2.8, line_length=0.4))

# Show filled convergence: lines from corners to center
for v in hexagons[0].get_vertices():
    diag = Line(v, hexagons[0].get_center(), color=SERIES_COLOR, stroke_width=0.8)
    self.add(diag)
self.wait(1.5)
```\
"""
