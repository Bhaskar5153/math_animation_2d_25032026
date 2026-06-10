GEOMETRY_HELPERS = """\
### GEOMETRY -- GLOW & BLOOM HELPERS (include at top of every geometry scene)
# make_glow(shape): concentric translucent halos behind any shape → glow effect
# Add the glow VGroup to the scene BEFORE the main shape so it sits behind it.
# bloom_flash: Flash + Circumscribe combo for dramatic answer reveal.

```python
# ---- GLOW & BLOOM HELPERS ----
def _glow(shape, gc=None, layers=3):
    \"\"\"Return VGroup of glow halos. self.add(glow) BEFORE self.play(Create(shape)).\"\"\"
    gc = gc if gc else shape.get_color()
    group = VGroup()
    for i in range(layers, 0, -1):
        copy = shape.copy().scale(1.0 + i * 0.07)
        copy.set_stroke(gc, width=3 + i * 5, opacity=0.10 * i)
        copy.set_fill(gc, opacity=0.04 * i)
        group.add(copy)
    return group

# Usage:
# glow = _glow(my_shape, TEAL_A)
# self.add(glow)
# self.play(Create(my_shape))
# self.play(Flash(my_shape.get_center(), color=TEAL_A, flash_radius=1.2, num_lines=12))
```

### GEOMETRY TYPE 1: 2D SHAPES -- AREA & PERIMETER with GLOW & BLOOM
# Use for: "find area / perimeter of triangle / rectangle / circle / polygon"
# VISUAL:  Shape with glow on LEFT half. Step-by-step formulas on RIGHT half.
#          Final answer revealed with bloom Flash + Circumscribe.
# COLORS:  Shape fill gradient (e.g. TEAL → BLUE). Dimensions in CYAN/ORANGE.
# LAYOUT:  shape.move_to(LEFT*2.8)   equations on RIGHT*2.8

```python
import numpy as np
from manim import *

# ---- Glow helper (copy this into your scene) ----
def _glow(shape, gc=None, layers=3):
    gc = gc if gc else shape.get_color()
    group = VGroup()
    for i in range(layers, 0, -1):
        copy = shape.copy().scale(1.0 + i * 0.07)
        copy.set_stroke(gc, width=3 + i * 5, opacity=0.10 * i)
        copy.set_fill(gc, opacity=0.04 * i)
        group.add(copy)
    return group

# ---- Adapt values ----
width_val  = 6
height_val = 4
area_val   = width_val * height_val
perim_val  = 2 * (width_val + height_val)
w_str = str(width_val);  h_str = str(height_val)
a_str = str(area_val);   p_str = str(perim_val)

# ---- Shape (LEFT HALF) ----
rect = Rectangle(
    width=3.8, height=2.5,
    fill_color=TEAL, fill_opacity=0.40,
    stroke_color=TEAL_A, stroke_width=3,
)
rect.set_color_by_gradient(TEAL_A, BLUE_B)   # gradient fill
rect.move_to(LEFT * 2.8)

glow = _glow(rect, TEAL_A)
self.add(glow)
self.play(Create(rect), run_time=1.2)
self.play(Flash(rect.get_center(), color=TEAL_A, flash_radius=1.5, num_lines=12, run_time=0.7))
self.wait(0.5)

# Dimension arrows
w_arrow = DoubleArrow(
    rect.get_corner(DL) + DOWN * 0.45,
    rect.get_corner(DR) + DOWN * 0.45,
    color=CYAN, stroke_width=2.5, buff=0,
)
h_arrow = DoubleArrow(
    rect.get_corner(DR) + RIGHT * 0.45,
    rect.get_corner(UR) + RIGHT * 0.45,
    color=ORANGE, stroke_width=2.5, buff=0,
)
w_lbl = Text("w = " + w_str, font_size=22, color=CYAN).next_to(w_arrow, DOWN, buff=0.1)
h_lbl = Text("h = " + h_str, font_size=22, color=ORANGE).next_to(h_arrow, RIGHT, buff=0.1)
self.play(GrowArrow(w_arrow), GrowArrow(h_arrow), Write(w_lbl), Write(h_lbl))
self.wait(1.5)

# ---- Equations (RIGHT HALF) ----
eq1 = Text("Area  =  w x h",                    font_size=28, color=WHITE)
eq2 = Text("      =  " + w_str + " x " + h_str, font_size=28, color=YELLOW)
eq3 = Text("      =  " + a_str,                  font_size=36, color=GOLD, weight="BOLD")
eq4 = Text("Perimeter  =  2(w + h)",              font_size=28, color=WHITE)
eq5 = Text("           =  2(" + w_str + " + " + h_str + ")", font_size=28, color=YELLOW)
eq6 = Text("           =  " + p_str,              font_size=36, color=GREEN_C, weight="BOLD")

top_stack = VGroup(eq1, eq2, eq3).arrange(DOWN, buff=0.30, aligned_edge=LEFT)
bot_stack = VGroup(eq4, eq5, eq6).arrange(DOWN, buff=0.30, aligned_edge=LEFT)
eq_column = VGroup(top_stack, bot_stack).arrange(DOWN, buff=0.55, aligned_edge=LEFT)
eq_column.move_to(RIGHT * 2.8 + UP * 0.2)

for eq in [eq1, eq2, eq3, eq4, eq5, eq6]:
    self.play(Write(eq), run_time=0.6)
    self.wait(1.2)

# Bloom reveal on answers
self.play(
    Circumscribe(eq3, color=GOLD,    buff=0.15),
    Circumscribe(eq6, color=GREEN_C, buff=0.15),
)
self.play(
    Flash(eq3.get_center(), color=GOLD,    flash_radius=1.2, num_lines=10),
    Flash(eq6.get_center(), color=GREEN_C, flash_radius=1.2, num_lines=10),
)
self.wait(3.0)
```

### GEOMETRY TYPE 2: SHAPE TRANSFORMATIONS -- ROTATE, REFLECT, TRANSLATE
# Use for: "reflect shape across x/y axis", "rotate by angle", "translate by vector"
# VISUAL:  Original shape (TEAL) → ghost copy (faded) → transformed shape (GOLD).
#          Mirror line shown as dashed YELLOW line for reflections.
#          Arrow path shown for translations.
# LAYOUT:  Shapes centered in LEFT half. Step labels on RIGHT half.
# KEY ANIMATIONS:
#   Rotate:    self.play(Rotate(shape, angle=PI/3, about_point=..., run_time=2))
#   Reflect:   shape.copy().flip(UP)   # flip(UP) = mirror across vertical axis
#              shape.copy().flip(RIGHT) # flip(RIGHT) = mirror across horizontal axis
#   Translate: shape.animate.shift(RIGHT*2 + UP*1)

```python
import numpy as np
from manim import *

def _glow(shape, gc=None, layers=3):
    gc = gc if gc else shape.get_color()
    group = VGroup()
    for i in range(layers, 0, -1):
        copy = shape.copy().scale(1.0 + i * 0.07)
        copy.set_stroke(gc, width=3 + i * 5, opacity=0.10 * i)
        copy.set_fill(gc, opacity=0.04 * i)
        group.add(copy)
    return group

# ---- Base shape ----
base_tri = Polygon(
    np.array([-0.8, -0.8, 0]),
    np.array([ 0.8, -0.8, 0]),
    np.array([ 0.0,  1.0, 0]),
    fill_color=TEAL_B, fill_opacity=0.55,
    stroke_color=TEAL_A, stroke_width=3,
)
base_tri.move_to(LEFT * 3.5)

glow_orig = _glow(base_tri, TEAL_A)
self.add(glow_orig)
self.play(Create(base_tri))
self.play(Flash(base_tri.get_center(), color=TEAL_A, flash_radius=1.0, num_lines=10))
orig_lbl = Text("Original", font_size=20, color=TEAL_A)
orig_lbl.next_to(base_tri, DOWN, buff=0.2)
self.play(Write(orig_lbl))
self.wait(1.5)

# ---- ROTATION ----
step_rotate = Text("Step 1: Rotate 90° anticlockwise", font_size=28, color=WHITE)
step_rotate.move_to(RIGHT * 2.8 + UP * 2.0)
self.play(Write(step_rotate))

rotated = base_tri.copy()
rotated.set_color(GOLD)
rotated.set_fill(GOLD, opacity=0.45)
glow_rot = _glow(rotated, GOLD)
self.add(glow_rot)
self.add(rotated)
self.play(
    Rotate(rotated, angle=PI / 2, about_point=base_tri.get_center(), run_time=2.0),
    Rotate(glow_rot, angle=PI / 2, about_point=base_tri.get_center(), run_time=2.0),
)
rot_lbl = Text("Rotated 90°", font_size=20, color=GOLD)
rot_lbl.next_to(rotated, RIGHT, buff=0.2)
self.play(Write(rot_lbl))
self.play(Flash(rotated.get_center(), color=GOLD, flash_radius=1.0, num_lines=10))
self.wait(2.0)
self.play(FadeOut(rotated), FadeOut(glow_rot), FadeOut(rot_lbl), FadeOut(step_rotate))

# ---- REFLECTION ----
step_reflect = Text("Step 2: Reflect across y-axis", font_size=28, color=WHITE)
step_reflect.move_to(RIGHT * 2.8 + UP * 2.0)
mirror_line = DashedLine(UP * 2.8, DOWN * 2.8, color=YELLOW_A, stroke_width=2, dash_length=0.18)
mirror_lbl  = Text("mirror line", font_size=18, color=YELLOW_A)
mirror_lbl.next_to(mirror_line, UP, buff=0.1)
self.play(Write(step_reflect), Create(mirror_line), Write(mirror_lbl))
self.wait(0.8)

# Reflected shape: flip(UP) = mirror across the vertical (y) axis
reflected = base_tri.copy()
reflected.flip(UP)
reflected.set_color(PINK)
reflected.set_fill(PINK, opacity=0.45)
# Position mirror image on the opposite side
reflected.move_to(RIGHT * 0.5 + base_tri.get_center()[1] * UP)
glow_ref = _glow(reflected, PINK)
# Ghost of original at its reflected position
ghost = base_tri.copy().set_fill(opacity=0.15).set_stroke(opacity=0.3)
self.add(ghost)
self.play(
    FadeIn(glow_ref),
    TransformFromCopy(base_tri, reflected),
    run_time=1.8,
)
ref_lbl = Text("Reflected", font_size=20, color=PINK)
ref_lbl.next_to(reflected, DOWN, buff=0.2)
self.play(Write(ref_lbl))
self.play(Flash(reflected.get_center(), color=PINK, flash_radius=1.0, num_lines=10))
self.wait(2.0)
self.play(
    FadeOut(reflected), FadeOut(glow_ref), FadeOut(ref_lbl),
    FadeOut(mirror_line), FadeOut(mirror_lbl), FadeOut(ghost), FadeOut(step_reflect),
)

# ---- TRANSLATION ----
step_trans = Text("Step 3: Translate right 3, up 2", font_size=28, color=WHITE)
step_trans.move_to(RIGHT * 2.8 + UP * 2.0)
self.play(Write(step_trans))

translated = base_tri.copy()
translated.set_color(GREEN_C)
translated.set_fill(GREEN_C, opacity=0.45)
glow_tr = _glow(translated, GREEN_C)
self.add(glow_tr)
self.add(translated)
# Arrow showing translation vector
t_arrow = Arrow(
    base_tri.get_center(),
    base_tri.get_center() + RIGHT * 1.8 + UP * 1.2,
    color=GREEN_C, stroke_width=3, buff=0,
)
vec_lbl = Text("(3, 2)", font_size=20, color=GREEN_C)
vec_lbl.next_to(t_arrow, UR, buff=0.1)
self.play(GrowArrow(t_arrow), Write(vec_lbl))
self.play(
    translated.animate.shift(RIGHT * 1.8 + UP * 1.2),
    glow_tr.animate.shift(RIGHT * 1.8 + UP * 1.2),
    run_time=1.8,
)
self.play(Flash(translated.get_center(), color=GREEN_C, flash_radius=1.0, num_lines=10))
self.wait(3.0)
```

### GEOMETRY TYPE 3: TRIANGLES -- ANGLES, SIDES, PYTHAGOREAN THEOREM
# Use for: "find missing side of right triangle", "find angle", "classify triangle"
# VISUAL:  Large right-angle triangle on LEFT. Animated arc angles + tick marks.
#          Hypotenuse highlighted with glow. Pythagoras equation on RIGHT.

```python
import numpy as np
from manim import *

def _glow(shape, gc=None, layers=3):
    gc = gc if gc else shape.get_color()
    group = VGroup()
    for i in range(layers, 0, -1):
        copy = shape.copy().scale(1.0 + i * 0.07)
        copy.set_stroke(gc, width=3 + i * 5, opacity=0.10 * i)
        copy.set_fill(gc, opacity=0.04 * i)
        group.add(copy)
    return group

# ---- Adapt values ----
a_val = 3    # one leg
b_val = 4    # other leg
c_val = 5    # hypotenuse  (a² + b² = c²)
a_str = str(a_val);  b_str = str(b_val);  c_str = str(c_val)

# ---- Triangle vertices (LEFT HALF, generous size) ----
A = np.array([-4.5, -1.8, 0])   # right angle vertex
B = np.array([-0.5, -1.8, 0])   # end of horizontal leg
C = np.array([-4.5,  1.8, 0])   # end of vertical leg

tri = Polygon(A, B, C,
              fill_color=BLUE_D, fill_opacity=0.30,
              stroke_color=BLUE_B, stroke_width=3)

glow_tri = _glow(tri, BLUE_B)
self.add(glow_tri)
self.play(Create(tri))
self.wait(0.5)

# Right-angle box at A
sq_size = 0.22
right_sq = Polygon(
    A + RIGHT * sq_size,
    A + RIGHT * sq_size + UP * sq_size,
    A + UP * sq_size,
    A,
    color=WHITE, stroke_width=2,
)
self.play(Create(right_sq))

# Side labels
lbl_a = Text("a = " + a_str, font_size=24, color=CYAN)
lbl_b = Text("b = " + b_str, font_size=24, color=ORANGE)
lbl_c = Text("c = ?", font_size=24, color=GOLD)
lbl_a.move_to((A + C) / 2 + LEFT * 0.55)     # left leg label
lbl_b.move_to((A + B) / 2 + DOWN * 0.35)     # bottom leg label
lbl_c.move_to((B + C) / 2 + RIGHT * 0.55)    # hypotenuse label
self.play(Write(lbl_a), Write(lbl_b), Write(lbl_c))
self.wait(1.5)

# Highlight hypotenuse with glow
hyp = Line(B, C, color=GOLD, stroke_width=5)
glow_hyp = _glow(hyp, GOLD)
self.add(glow_hyp)
self.play(Create(hyp))
self.play(Flash(hyp.get_midpoint(), color=GOLD, flash_radius=0.8, num_lines=8))
self.wait(1.0)

# Arc angle at B
angle_arc = Arc(
    radius=0.50,
    start_angle=PI - np.arctan2(C[1]-B[1], C[0]-B[0]),
    angle=np.arctan2(C[1]-B[1], C[0]-B[0]),
    arc_center=B, color=YELLOW_A, stroke_width=2,
)
self.play(Create(angle_arc))
self.wait(0.5)

# ---- Pythagoras steps (RIGHT HALF) ----
eq1 = Text("Pythagoras Theorem:", font_size=26, color=WHITE)
eq2 = Text("c² = a² + b²",       font_size=30, color=WHITE)
eq3 = Text("c² = " + a_str + "² + " + b_str + "²",
                                   font_size=30, color=YELLOW)
eq4 = Text("c² = " + str(a_val**2) + " + " + str(b_val**2),
                                   font_size=30, color=YELLOW)
eq5 = Text("c² = " + str(a_val**2 + b_val**2),
                                   font_size=30, color=TEAL)
eq6 = Text("c  = " + c_str,       font_size=40, color=GOLD, weight="BOLD")

eq_stack = VGroup(eq1, eq2, eq3, eq4, eq5, eq6)
eq_stack.arrange(DOWN, buff=0.35, aligned_edge=LEFT)
eq_stack.move_to(RIGHT * 2.8 + UP * 0.3)

for eq in eq_stack:
    self.play(Write(eq), run_time=0.7)
    self.wait(1.5)

ans_box = SurroundingRectangle(eq6, color=GOLD, buff=0.18, corner_radius=0.10)
self.play(Create(ans_box))
self.play(
    Flash(eq6.get_center(), color=GOLD, flash_radius=1.3, num_lines=12),
    Circumscribe(eq6, color=GOLD, buff=0.15),
)
# Update label c→value
self.play(Transform(lbl_c, Text("c = " + c_str, font_size=24, color=GOLD)
                    .move_to(lbl_c.get_center())))
self.wait(4.0)
```

### GEOMETRY TYPE 4: CIRCLES -- AREA, CIRCUMFERENCE, ARC, SECTOR
# Use for: "find area / circumference of circle", "arc length", "sector area"
# VISUAL:  Animated circle build-up with rotating radius. Sector shaded GOLD.
#          Pi symbol glows. Equations appear step by step on RIGHT.
# KEY TRICK: ValueTracker drives a sweeping arc → looks like circle drawing itself.

```python
import numpy as np
from manim import *

def _glow(shape, gc=None, layers=3):
    gc = gc if gc else shape.get_color()
    group = VGroup()
    for i in range(layers, 0, -1):
        copy = shape.copy().scale(1.0 + i * 0.07)
        copy.set_stroke(gc, width=3 + i * 5, opacity=0.10 * i)
        copy.set_fill(gc, opacity=0.04 * i)
        group.add(copy)
    return group

# ---- Adapt values ----
r_val    = 7      # radius
theta    = PI / 3 # sector angle (60°) -- adapt or remove if not needed
r_str    = str(r_val)
area_val = round(3.14159 * r_val * r_val, 2)
circ_val = round(2 * 3.14159 * r_val, 2)

# ---- Circle center in LEFT HALF ----
cx = LEFT * 2.8
circ = Circle(radius=2.0, color=PURPLE_A, stroke_width=4,
              fill_color=PURPLE, fill_opacity=0.20)
circ.move_to(cx)
circ.set_color_by_gradient(PURPLE_A, BLUE_D)

glow_c = _glow(circ, PURPLE_A)
self.add(glow_c)
self.play(Create(circ), run_time=1.5)
self.play(Flash(cx, color=PURPLE_A, flash_radius=2.5, num_lines=16))
self.wait(0.5)

# Center dot + radius line
center_dot = Dot(cx, radius=0.10, color=WHITE)
self.play(FadeIn(center_dot))

r_line = Line(cx, cx + RIGHT * 2.0, color=CYAN, stroke_width=3)
r_lbl  = Text("r = " + r_str, font_size=22, color=CYAN)
r_lbl.next_to(r_line, UP, buff=0.12)
self.play(Create(r_line), Write(r_lbl))

# Spinning radius (full rotation to show circumference concept)
spin_line = r_line.copy()
self.play(Rotate(spin_line, angle=TAU, about_point=cx, run_time=2.5, rate_func=linear))
self.remove(spin_line)
self.wait(0.5)

# Sector (shaded arc slice)
sector = Sector(
    outer_radius=2.0, angle=theta,
    start_angle=0, color=GOLD, fill_opacity=0.55,
)
sector.move_to(cx)
glow_sec = _glow(sector, GOLD, layers=2)
self.add(glow_sec)
self.play(FadeIn(sector))
self.play(Flash(cx + RIGHT * 1.0, color=GOLD, flash_radius=0.7, num_lines=8))
self.wait(1.0)

# ---- Equations (RIGHT HALF) ----
eq1 = Text("Area of circle:",             font_size=26, color=WHITE)
eq2 = Text("A = π r²",                    font_size=30, color=WHITE)
eq3 = Text("A = π x " + r_str + "²",     font_size=30, color=YELLOW)
eq4 = Text("A = π x " + str(r_val**2),   font_size=30, color=YELLOW)
eq5 = Text("A ≈ " + str(area_val),        font_size=36, color=GOLD, weight="BOLD")
eq6 = Text("Circumference:",              font_size=26, color=WHITE)
eq7 = Text("C = 2πr = " + str(circ_val), font_size=30, color=GREEN_C, weight="BOLD")

top_block = VGroup(eq1, eq2, eq3, eq4, eq5).arrange(DOWN, buff=0.28, aligned_edge=LEFT)
bot_block = VGroup(eq6, eq7).arrange(DOWN, buff=0.28, aligned_edge=LEFT)
eq_col    = VGroup(top_block, bot_block).arrange(DOWN, buff=0.50, aligned_edge=LEFT)
eq_col.move_to(RIGHT * 2.8 + UP * 0.3)

for eq in [eq1, eq2, eq3, eq4, eq5, eq6, eq7]:
    self.play(Write(eq), run_time=0.6)
    self.wait(1.2)

self.play(
    Circumscribe(eq5, color=GOLD,    buff=0.15),
    Circumscribe(eq7, color=GREEN_C, buff=0.15),
)
self.play(
    Flash(eq5.get_center(), color=GOLD,    flash_radius=1.2, num_lines=10),
    Flash(eq7.get_center(), color=GREEN_C, flash_radius=1.2, num_lines=10),
)
self.wait(4.0)
```

### GEOMETRY TYPE 5: 3D SOLIDS -- ISOMETRIC SHADING (cube, cuboid, cylinder, cone, sphere)
# Use for: "find volume / surface area of cube / cuboid / cylinder / cone / sphere"
# VISUAL:  Isometric 3D solid with 3-face shading (top=light, front=mid, right=dark).
#          Shape rotates gently (simulated by morph). Glow on top face.
#          Equations on RIGHT half. NEVER use ThreeDScene.
#
# ISOMETRIC BASIS VECTORS (use these for ALL 3D geometry):
#   ISO_X = right-forward direction
#   ISO_Y = left-forward direction
#   ISO_Z = straight up

```python
import numpy as np
from manim import *

def _glow(shape, gc=None, layers=3):
    gc = gc if gc else shape.get_color()
    group = VGroup()
    for i in range(layers, 0, -1):
        copy = shape.copy().scale(1.0 + i * 0.07)
        copy.set_stroke(gc, width=3 + i * 5, opacity=0.10 * i)
        copy.set_fill(gc, opacity=0.04 * i)
        group.add(copy)
    return group

# ---- Isometric basis ----
ISO_X = np.array([ 0.866, -0.50, 0])
ISO_Y = np.array([-0.866, -0.50, 0])
ISO_Z = np.array([ 0.0,    1.0,  0])

def iso(x, y, z):
    return x * ISO_X + y * ISO_Y + z * ISO_Z

# Offset so cube sits in LEFT HALF
ORIGIN_OFFSET = LEFT * 2.8 + DOWN * 0.8

def iso_pt(x, y, z):
    return iso(x, y, z) + ORIGIN_OFFSET

# ---- CUBE example (side = s) ----
s = 1.8   # cube side length (screen units -- adapt)
s_val = 4  # real-world side length (for labels)
s_str = str(s_val)
vol_val = s_val ** 3
sa_val  = 6 * s_val ** 2

# 8 vertices
v = {
    'A': iso_pt(0, 0, 0), 'B': iso_pt(s, 0, 0), 'C': iso_pt(s, s, 0), 'D': iso_pt(0, s, 0),
    'E': iso_pt(0, 0, s), 'F': iso_pt(s, 0, s), 'G': iso_pt(s, s, s), 'H': iso_pt(0, s, s),
}

# Three visible faces — lighter top, medium front, darker right
top_face   = Polygon(v['E'], v['F'], v['G'], v['H'],
                     fill_color=BLUE_B,  fill_opacity=0.88, stroke_color=WHITE, stroke_width=1.8)
front_face = Polygon(v['A'], v['E'], v['H'], v['D'],
                     fill_color=BLUE_D,  fill_opacity=0.80, stroke_color=WHITE, stroke_width=1.8)
right_face = Polygon(v['D'], v['H'], v['G'], v['C'],
                     fill_color=BLUE_E,  fill_opacity=0.72, stroke_color=WHITE, stroke_width=1.8)

# Hidden edge (optional, dashed)
hidden_AB = DashedLine(v['A'], v['B'], color=GRAY_B, stroke_width=1.2, dash_length=0.12)
hidden_BC = DashedLine(v['B'], v['C'], color=GRAY_B, stroke_width=1.2, dash_length=0.12)
hidden_BF = DashedLine(v['B'], v['F'], color=GRAY_B, stroke_width=1.2, dash_length=0.12)

cube_group = VGroup(top_face, front_face, right_face)
glow_cube  = _glow(top_face, BLUE_B, layers=2)

self.add(glow_cube)
self.play(
    FadeIn(front_face), FadeIn(right_face), FadeIn(top_face),
    Create(hidden_AB), Create(hidden_BC), Create(hidden_BF),
    run_time=1.5,
)
self.play(Flash(ORIGIN_OFFSET + UP * s * 0.6, color=BLUE_A, flash_radius=1.2, num_lines=12))
self.wait(0.5)

# Side length label on one visible edge
edge_lbl = Text("s = " + s_str, font_size=22, color=WHITE)
mid_front_edge = (v['A'] + v['E']) / 2 + LEFT * 0.4
edge_lbl.move_to(mid_front_edge)
self.play(Write(edge_lbl))
self.wait(1.5)

# Gentle "rotation" effect — slightly scale the top face to simulate perspective shift
self.play(top_face.animate.set_fill(BLUE_A, opacity=0.95), run_time=0.8)
self.play(top_face.animate.set_fill(BLUE_B, opacity=0.88), run_time=0.8)

# ---- Volume & Surface Area (RIGHT HALF) ----
eq1 = Text("Volume of cube:",            font_size=26, color=WHITE)
eq2 = Text("V = s³",                     font_size=30, color=WHITE)
eq3 = Text("V = " + s_str + "³",         font_size=30, color=YELLOW)
eq4 = Text("V = " + str(vol_val),        font_size=38, color=GOLD, weight="BOLD")
eq5 = Text("Surface area:",              font_size=26, color=WHITE)
eq6 = Text("SA = 6s²",                   font_size=30, color=WHITE)
eq7 = Text("SA = 6 x " + s_str + "²",   font_size=30, color=YELLOW)
eq8 = Text("SA = " + str(sa_val),        font_size=38, color=GREEN_C, weight="BOLD")

blk1 = VGroup(eq1, eq2, eq3, eq4).arrange(DOWN, buff=0.28, aligned_edge=LEFT)
blk2 = VGroup(eq5, eq6, eq7, eq8).arrange(DOWN, buff=0.28, aligned_edge=LEFT)
eq_col = VGroup(blk1, blk2).arrange(DOWN, buff=0.50, aligned_edge=LEFT)
eq_col.move_to(RIGHT * 2.8 + UP * 0.2)

for eq in [eq1, eq2, eq3, eq4, eq5, eq6, eq7, eq8]:
    self.play(Write(eq), run_time=0.6)
    self.wait(1.2)

self.play(
    Circumscribe(eq4, color=GOLD,    buff=0.15),
    Circumscribe(eq8, color=GREEN_C, buff=0.15),
)
self.play(
    Flash(eq4.get_center(), color=GOLD,    flash_radius=1.2, num_lines=10),
    Flash(eq8.get_center(), color=GREEN_C, flash_radius=1.2, num_lines=10),
)
self.wait(4.0)
```

### GEOMETRY TYPE 6: 3D SOLIDS -- CYLINDER
# Use for: "volume / surface area of cylinder", radius r and height h given.
# VISUAL: Isometric cylinder = top ellipse + rectangle body + bottom ellipse (darker).
#         Shaded body TEAL_D, top face TEAL_A (lightest), bottom TEAL_E (darkest).

```python
import numpy as np
from manim import *

# ---- Adapt values ----
r_val = 3;   h_val = 7
r_str = str(r_val);  h_str = str(h_val)
import math as _math
vol_cyl = round(_math.pi * r_val**2 * h_val, 2)
csa_cyl = round(2 * _math.pi * r_val * h_val, 2)
tsa_cyl = round(2 * _math.pi * r_val * (h_val + r_val), 2)

cx = LEFT * 2.8   # cylinder screen center

# Ellipse parameters for top/bottom faces
ew = 1.8   # ellipse horizontal radius (screen)
eh = 0.55  # ellipse vertical radius  (screen, < ew for iso look)
body_h = 2.5  # screen height of cylinder body

top_center = cx + UP * (body_h / 2)
bot_center = cx + DOWN * (body_h / 2)

# Cylinder body (rectangle with gradient)
body = Rectangle(width=ew * 2, height=body_h,
                 fill_color=TEAL_D, fill_opacity=0.80,
                 stroke_color=TEAL_B, stroke_width=2)
body.set_color_by_gradient(TEAL_D, DARK_BLUE)
body.move_to(cx)

# Top ellipse (light)
top_ell = Ellipse(width=ew * 2, height=eh * 2,
                  fill_color=TEAL_A, fill_opacity=0.92,
                  stroke_color=TEAL_A, stroke_width=2)
top_ell.move_to(top_center)

# Bottom ellipse (dark — partially hidden)
bot_ell = Ellipse(width=ew * 2, height=eh * 2,
                  fill_color=TEAL_E, fill_opacity=0.70,
                  stroke_color=TEAL_D, stroke_width=2)
bot_ell.move_to(bot_center)

# Glow on top face
glow_top = _glow(top_ell, TEAL_A, layers=2)

self.play(FadeIn(body))
self.add(glow_top)
self.play(FadeIn(bot_ell), FadeIn(top_ell))
self.play(Flash(top_center, color=TEAL_A, flash_radius=1.0, num_lines=10))

# Dimension lines
r_line = Line(cx, cx + RIGHT * ew, color=CYAN, stroke_width=2.5)
r_lbl  = Text("r = " + r_str, font_size=20, color=CYAN)
r_lbl.next_to(r_line, UP, buff=0.1)
h_brace = Brace(body, RIGHT, buff=0.15, color=ORANGE)
h_lbl   = Text("h = " + h_str, font_size=20, color=ORANGE)
h_lbl.next_to(h_brace, RIGHT, buff=0.1)
self.play(Create(r_line), Write(r_lbl), GrowFromEdge(h_brace, UP), Write(h_lbl))
self.wait(1.5)

# Equations on RIGHT half
eq1 = Text("Volume:",                         font_size=26, color=WHITE)
eq2 = Text("V = πr²h",                        font_size=30, color=WHITE)
eq3 = Text("V = π x " + r_str + "² x " + h_str, font_size=30, color=YELLOW)
eq4 = Text("V ≈ " + str(vol_cyl),             font_size=36, color=GOLD, weight="BOLD")
eq5 = Text("Total Surface Area:",             font_size=26, color=WHITE)
eq6 = Text("TSA = 2πr(h + r)",               font_size=28, color=WHITE)
eq7 = Text("TSA ≈ " + str(tsa_cyl),           font_size=36, color=GREEN_C, weight="BOLD")

blk1 = VGroup(eq1, eq2, eq3, eq4).arrange(DOWN, buff=0.28, aligned_edge=LEFT)
blk2 = VGroup(eq5, eq6, eq7).arrange(DOWN, buff=0.28, aligned_edge=LEFT)
eq_col = VGroup(blk1, blk2).arrange(DOWN, buff=0.50, aligned_edge=LEFT)
eq_col.move_to(RIGHT * 2.8 + UP * 0.2)

for eq in [eq1, eq2, eq3, eq4, eq5, eq6, eq7]:
    self.play(Write(eq), run_time=0.6)
    self.wait(1.2)

self.play(
    Flash(eq4.get_center(), color=GOLD,    flash_radius=1.2, num_lines=10),
    Flash(eq7.get_center(), color=GREEN_C, flash_radius=1.2, num_lines=10),
)
self.wait(4.0)
```

### GEOMETRY TYPE 7: 3D SOLIDS -- CONE & SPHERE
# Use for: "volume / surface area of cone or sphere"
# CONE VISUAL: Isometric cone = filled triangle body + bottom ellipse + apex dot.
# SPHERE VISUAL: Circle with radial gradient shading (bright spot upper-left).

```python
import numpy as np
from manim import *
import math as _math

def _glow(shape, gc=None, layers=3):
    gc = gc if gc else shape.get_color()
    group = VGroup()
    for i in range(layers, 0, -1):
        copy = shape.copy().scale(1.0 + i * 0.07)
        copy.set_stroke(gc, width=3 + i * 5, opacity=0.10 * i)
        copy.set_fill(gc, opacity=0.04 * i)
        group.add(copy)
    return group

# ---- CONE (LEFT HALF) ----
r_val = 3;  h_val = 8
r_str = str(r_val);  h_str = str(h_val)
slant = round(_math.sqrt(r_val**2 + h_val**2), 2)
vol_cone = round(_math.pi * r_val**2 * h_val / 3, 2)
csa_cone = round(_math.pi * r_val * slant, 2)

cx = LEFT * 2.8
ew = 1.6; eh = 0.50; ch = 2.8   # screen ellipse and cone height

apex = cx + UP * (ch / 2)
bot  = cx + DOWN * (ch / 2)

# Cone body (two triangular sides)
left_side  = Polygon(apex, bot + LEFT * ew, bot,
                     fill_color=ORANGE_D, fill_opacity=0.78,
                     stroke_color=ORANGE_A, stroke_width=2)
right_side = Polygon(apex, bot, bot + RIGHT * ew,
                     fill_color=ORANGE_E, fill_opacity=0.68,
                     stroke_color=ORANGE_A, stroke_width=2)
right_side.set_color_by_gradient(ORANGE_C, ORANGE_E)

bot_ell = Ellipse(width=ew * 2, height=eh * 2,
                  fill_color=ORANGE_E, fill_opacity=0.85,
                  stroke_color=ORANGE_A, stroke_width=2)
bot_ell.move_to(bot)

apex_dot = Dot(apex, radius=0.14, color=YELLOW)
glow_apex = _glow(apex_dot, YELLOW, layers=2)

self.play(FadeIn(left_side), FadeIn(right_side))
self.play(FadeIn(bot_ell))
self.add(glow_apex)
self.play(FadeIn(apex_dot))
self.play(Flash(apex, color=YELLOW, flash_radius=0.8, num_lines=10))
self.wait(1.0)

# Slant-height arrow
slant_line = DashedLine(apex, bot + RIGHT * ew,
                        color=CYAN, stroke_width=2.5, dash_length=0.15)
sl_lbl = Text("l = " + str(slant), font_size=20, color=CYAN)
sl_lbl.next_to(slant_line, RIGHT, buff=0.1)
self.play(Create(slant_line), Write(sl_lbl))
self.wait(1.5)

# ---- SPHERE -- shaded circle with highlight spot ----
# (Show after FadeOut of cone, or in separate scene)
# Sphere = large Circle + inner highlight ellipse
sphere = Circle(radius=2.0, fill_color=PURPLE_D, fill_opacity=0.80,
                stroke_color=PURPLE_A, stroke_width=3)
sphere.set_color_by_gradient(PURPLE_A, PURPLE_E)
sphere.move_to(cx)

# Highlight spot (top-left) simulates light reflection (bloom-like)
highlight = Ellipse(width=0.7, height=0.45,
                    fill_color=WHITE, fill_opacity=0.55,
                    stroke_width=0)
highlight.move_to(cx + UP * 1.1 + LEFT * 0.7)

# Outer glow
glow_sph = _glow(sphere, PURPLE_A, layers=3)

self.add(glow_sph)
self.play(Create(sphere))
self.play(FadeIn(highlight))
self.play(Flash(cx, color=PURPLE_A, flash_radius=2.5, num_lines=16))
self.wait(1.5)

# Radius line
r_line = Line(cx, cx + RIGHT * 2.0, color=CYAN, stroke_width=3)
r_lbl2 = Text("r = " + r_str, font_size=22, color=CYAN)
r_lbl2.next_to(r_line, UP, buff=0.12)
self.play(Create(r_line), Write(r_lbl2))
self.wait(1.0)

# Equations right half (example for cone)
vol_str = str(vol_cone);  csa_str = str(csa_cone)
eq1 = Text("Volume of cone:",             font_size=26, color=WHITE)
eq2 = Text("V = (1/3)πr²h",              font_size=30, color=WHITE)
eq3 = Text("V = (1/3)π x " + r_str + "² x " + h_str, font_size=26, color=YELLOW)
eq4 = Text("V ≈ " + vol_str,              font_size=36, color=GOLD, weight="BOLD")

eq_stack = VGroup(eq1, eq2, eq3, eq4).arrange(DOWN, buff=0.32, aligned_edge=LEFT)
eq_stack.move_to(RIGHT * 2.8 + UP * 0.5)

for eq in eq_stack:
    self.play(Write(eq), run_time=0.7)
    self.wait(1.3)

self.play(Circumscribe(eq4, color=GOLD, buff=0.15))
self.play(Flash(eq4.get_center(), color=GOLD, flash_radius=1.2, num_lines=10))
self.wait(4.0)
```

### GEOMETRY TYPE 8: COORDINATE DISTANCE (coordinate grid + bouncing ball)
```python
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
    y_length=5.5,
    axis_config={"color": GRAY_A, "stroke_width": 1.5, "include_ticks": False},
).shift(LEFT*2.5 + DOWN*0.9)

for val in range(int(min(x1,x2))-1, int(max(x1,x2))+2, 2):
    Text(str(val), font_size=15, color=GRAY_B).next_to(axes.c2p(val, 0), DOWN, buff=0.1)
for val in range(int(min(y1,y2))-1, int(max(y1,y2))+2, 2):
    Text(str(val), font_size=15, color=GRAY_B).next_to(axes.c2p(0, val), LEFT, buff=0.1)

dot1 = Dot(axes.c2p(x1, y1), radius=0.16, color=ORANGE)
dot2 = Dot(axes.c2p(x2, y2), radius=0.16, color=ORANGE)
lbl1 = Text("P1(" + str(x1) + ", " + str(y1) + ")", font_size=20, color=ORANGE)
lbl2 = Text("P2(" + str(x2) + ", " + str(y2) + ")", font_size=20, color=ORANGE)
lbl1.next_to(dot1, RIGHT, buff=0.14)
lbl2.next_to(dot2, LEFT,  buff=0.14)

dist_line = Line(axes.c2p(x1, y1), axes.c2p(x2, y2), color=ORANGE, stroke_width=3)

# Bouncing ball
ball = Circle(radius=0.18, color=YELLOW, fill_color=YELLOW, fill_opacity=1)
ball.move_to(axes.c2p(x1, y1))
p1_s = np.array(axes.c2p(x1, y1))
p2_s = np.array(axes.c2p(x2, y2))
line_vec = p2_s - p1_s
line_len  = float(np.linalg.norm(line_vec))
perp_dir = np.array([-line_vec[1], line_vec[0], 0]) / line_len

t_ball = ValueTracker(0.0)
def _ball_upd(m):
    t = t_ball.get_value()
    pos = p1_s + t * line_vec
    bounce = 0.45 * abs(_math.sin(t * _math.pi * 4)) * (1.0 - t * 0.75)
    m.move_to(pos + perp_dir * bounce)

ball.add_updater(_ball_upd)
self.add(dot1, lbl1, ball)
self.play(
    Create(dist_line),
    t_ball.animate.set_value(1.0),
    run_time=2.5, rate_func=linear,
)
ball.clear_updaters()
self.play(Flash(ball, color=YELLOW_A, flash_radius=0.55, line_length=0.25), run_time=0.5)
self.play(Transform(ball, dot2), Write(lbl2), run_time=0.5)

corner_pt = axes.c2p(x2, y1)
h_leg = DashedLine(axes.c2p(x1, y1), corner_pt,         color=TEAL, stroke_width=2, dash_length=0.14)
v_leg = DashedLine(corner_pt,         axes.c2p(x2, y2), color=TEAL, stroke_width=2, dash_length=0.14)
dx_lbl = Text("Dx = " + str(abs(dx)), font_size=18, color=TEAL)
dy_lbl = Text("Dy = " + str(abs(dy)), font_size=18, color=TEAL)
dx_lbl.next_to(h_leg, DOWN, buff=0.10)
dy_lbl.next_to(v_leg, LEFT, buff=0.10)

eq0 = Text("d = sqrt[(x2-x1)^2 + (y2-y1)^2]", font_size=25, color=WHITE)
eq1 = Text("d = sqrt[(" + str(dx) + ")^2 + (" + str(dy) + ")^2]", font_size=25, color=WHITE)
eq2 = Text("d = sqrt[" + str(dx**2) + " + " + str(dy**2) + "]",   font_size=25, color=YELLOW)
eq3 = Text("d = sqrt[" + str(dx**2 + dy**2) + "]",                 font_size=25, color=YELLOW)
eq_ans = Text("d = " + str(round(dist_val, 2)) + " units",          font_size=38, color=GREEN_C)

eq_stack = VGroup(eq0, eq1, eq2, eq3).arrange(DOWN, buff=0.38, aligned_edge=LEFT)
eq_stack.move_to(RIGHT*2.8 + UP*0.8)
eq_ans.next_to(eq_stack, DOWN, buff=0.50)
ans_box = SurroundingRectangle(eq_ans, color=GOLD, corner_radius=0.12, buff=0.18)
```

### GEOMETRY TYPE 9: 3D GEOMETRY ISOMETRIC -- QUICK REFERENCE
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
```

### GEOMETRY TYPE 10: BPT / SIMILAR TRIANGLES (Basic Proportionality Theorem)
# TRIGGER: "DE || BC", "LM || AB", "PQ || XY" inside a triangle, find missing length or x.
# VISUAL: Large triangle ABC on LEFT half. Parallel line DE (or LM etc.) drawn in YELLOW.
#         Segment labels (AD, DB, AE, EC or AL, LC, BM, MC) with DashedLine+Dot.
#         Algebra substitution on RIGHT half.
# KEY RULE: BPT says  AD/DB = AE/EC  (or equivalently  AD/AB = AE/AC).
#           If segments are algebraic (x-3, 2x, etc.) set up a cross-multiply equation → solve for x.
#
# !! CRITICAL: Use the EXACT segment values from the MATH SOLUTION — never invent numeric values !!

```python
import numpy as np
from manim import *

# ---- Adapt these values from the ACTUAL problem ----
# Example: LM || AB, AL = x-3, AC = 2x, BM = x-2, BC = 2x+3
# BPT gives  AL/LC = BM/MC  →  (x-3)/(x+3) = (x-2)/(x+5)  →  x = 9
seg_lbl_parallel = "LM || AB"        # the parallel-line statement
# Segment expressions (copy VERBATIM from the problem / math solution)
AL_expr  = "x-3";   AC_expr  = "2x"
BM_expr  = "x-2";   BC_expr  = "2x+3"
LC_expr  = "x+3"    # AC - AL = 2x - (x-3)
MC_expr  = "x+5"    # BC - BM = (2x+3)-(x-2)
answer_x = 9        # final numeric answer

# ---- Triangle vertices in LEFT HALF ----
A = np.array([-3.8,  2.2, 0])
B = np.array([-5.8, -1.8, 0])
C = np.array([-1.2, -1.8, 0])
t_ratio  = 0.48    # where L (on AC) and M (on BC) sit; adapt if diagram specifies otherwise
L = A + t_ratio * (C - A)
M = B + t_ratio * (C - B)

tri  = Polygon(A, B, C, stroke_color=BLUE_C, stroke_width=2.5,
               fill_color=BLUE_E, fill_opacity=0.18)
lm   = Line(L, M, color=YELLOW, stroke_width=2.8)
lm_g = lm.copy().set_stroke(YELLOW, width=8, opacity=0.18)

lbl_A = Text("A", font_size=22, color=WHITE).next_to(A, UP,    buff=0.12)
lbl_B = Text("B", font_size=22, color=WHITE).next_to(B, DL,    buff=0.12)
lbl_C = Text("C", font_size=22, color=WHITE).next_to(C, DR,    buff=0.12)
lbl_L = Text("L", font_size=20, color=YELLOW).next_to(L, LEFT, buff=0.12)
lbl_M = Text("M", font_size=20, color=YELLOW).next_to(M, RIGHT,buff=0.12)
par_note = Text(seg_lbl_parallel, font_size=20, color=YELLOW)
par_note.move_to(np.array([-3.5, -2.4, 0]))

# Dashed segment lengths  (AL on AC side, BM on BC side)
dash_AL  = DashedLine(A, L, color=GOLD,    stroke_width=2, dash_length=0.14)
dash_LC  = DashedLine(L, C, color=GREEN_C, stroke_width=2, dash_length=0.14)
dash_BM  = DashedLine(B, M, color=GOLD,    stroke_width=2, dash_length=0.14)
dash_MC  = DashedLine(M, C, color=GREEN_C, stroke_width=2, dash_length=0.14)
lbl_AL   = Text("AL="+AL_expr,  font_size=18, color=GOLD).next_to(dash_AL.get_midpoint(),  LEFT,  buff=0.1)
lbl_LC   = Text("LC="+LC_expr,  font_size=18, color=GREEN_C).next_to(dash_LC.get_midpoint(), LEFT, buff=0.1)
lbl_BM   = Text("BM="+BM_expr,  font_size=18, color=GOLD).next_to(dash_BM.get_midpoint(),  RIGHT, buff=0.1)
lbl_MC   = Text("MC="+MC_expr,  font_size=18, color=GREEN_C).next_to(dash_MC.get_midpoint(), RIGHT,buff=0.1)

self.play(Create(tri), run_time=1.2)
self.play(FadeIn(lbl_A), FadeIn(lbl_B), FadeIn(lbl_C))
self.play(Create(lm_g), Create(lm), FadeIn(lbl_L), FadeIn(lbl_M), FadeIn(par_note), run_time=0.9)
self.play(Create(dash_AL), Create(dash_LC), Create(dash_BM), Create(dash_MC), run_time=0.9)
self.play(FadeIn(lbl_AL), FadeIn(lbl_LC), FadeIn(lbl_BM), FadeIn(lbl_MC), run_time=0.7)
self.wait(2.0)

# ---- BPT algebra on RIGHT HALF ----
eq1 = Text("BPT: AL / LC = BM / MC",          font_size=30, color=WHITE)
eq2 = Text("("+AL_expr+") / ("+LC_expr+") = ("+BM_expr+") / ("+MC_expr+")",
                                                font_size=28, color=YELLOW)
eq3 = Text("Cross multiply:",                  font_size=26, color=WHITE)
# show cross-multiply result — derive from the actual expressions
cross_lhs = "("+AL_expr+")("+MC_expr+")"
cross_rhs = "("+BM_expr+")("+LC_expr+")"
eq4 = Text(cross_lhs + " = " + cross_rhs,      font_size=26, color=YELLOW)
eq5 = Text("Solve for x:",                     font_size=26, color=WHITE)
eq6 = Text("x  =  " + str(answer_x),           font_size=42, color=GOLD, weight="BOLD")

steps = VGroup(eq1, eq2, eq3, eq4, eq5, eq6).arrange(DOWN, buff=0.38, aligned_edge=LEFT)
steps.move_to(RIGHT*2.8 + UP*0.3)

for eq in steps:
    self.play(Write(eq), run_time=0.7)
    self.wait(1.8)

ans_box = SurroundingRectangle(eq6, color=GOLD, buff=0.20, corner_radius=0.12)
self.play(Create(ans_box))
self.play(
    Circumscribe(eq6, color=GOLD, buff=0.15),
    Flash(eq6.get_center(), color=GOLD, flash_radius=1.3, num_lines=12),
)
self.wait(2.0)
```

### GEOMETRY TYPE 11: VOLUME CONSERVATION (cone/cylinder → sphere and similar reshaping)
# TRIGGER: "cone made of clay reshaped into sphere", "find radius of sphere",
#          "melted and recast", "cylinder converted to sphere", "volume conserved"
# VISUAL:  Act 1 — isometric 2D cone on LEFT, volume formula on RIGHT.
#          Act 2 — sphere on LEFT (after FadeOut), solve V1=V2 on RIGHT.
#          NEVER use ThreeDScene — isometric 2D renders faster and is clearer.
# NOTE:    Adapt r_cone, h_cone, r_sphere from the ACTUAL problem values.

```python
import numpy as np
import math as _math
from manim import *

def _glow(shape, gc=None, layers=3):
    gc = gc if gc else shape.get_color()
    group = VGroup()
    for i in range(layers, 0, -1):
        copy = shape.copy().scale(1.0 + i * 0.07)
        copy.set_stroke(gc, width=3 + i * 5, opacity=0.10 * i)
        copy.set_fill(gc, opacity=0.04 * i)
        group.add(copy)
    return group

# ---- Adapt these values from the ACTUAL problem ----
r_cone   = 6      # radius of cone base (cm)
h_cone   = 24     # height of cone (cm)
r_sphere = 6      # answer: cube_root(3 * r_cone^2 * h_cone / 4)
# Intermediate values (recalculate from problem data):
vol_num  = r_cone**2 * h_cone // 3          # = 288  (without π)
r3_val   = vol_num * 3 // 4                 # = 216  (R³)
# ---- End of adapted values ----

cx = LEFT * 2.8
ew = 1.4; eh = 0.45; ch = 2.6

class MathAnimationScene(Scene):
    def construct(self):
        bg = Rectangle(width=16, height=9, fill_color="#0d0d0d", fill_opacity=1)
        self.add(bg)

        title = Text("Volume Conservation", font_size=32, color=YELLOW)
        title.to_edge(UP, buff=0.25)
        self.play(Write(title), run_time=0.6)
        self.wait(0.5)

        # ── ACT 1: CONE ────────────────────────────────────────────────────────
        apex = cx + UP * (ch / 2)
        bot  = cx + DOWN * (ch / 2)

        cone_L = Polygon(apex, bot + LEFT * ew, bot,
                         fill_color=ORANGE_D, fill_opacity=0.80,
                         stroke_color=ORANGE_A, stroke_width=2)
        cone_R = Polygon(apex, bot, bot + RIGHT * ew,
                         fill_color=ORANGE_E, fill_opacity=0.70,
                         stroke_color=ORANGE_A, stroke_width=2)
        bot_ell = Ellipse(width=ew * 2, height=eh * 2,
                          fill_color=ORANGE_E, fill_opacity=0.85,
                          stroke_color=ORANGE_A, stroke_width=2)
        bot_ell.move_to(bot)
        apex_dot = Dot(apex, radius=0.12, color=YELLOW)

        r_lbl = Text("r = 6 cm", font_size=22, color=CYAN)
        r_lbl.next_to(bot + RIGHT * ew, RIGHT, buff=0.12)
        h_dash = DashedLine(apex + RIGHT*0.2, bot + RIGHT*0.2,
                            color=GREEN_C, stroke_width=2)
        h_lbl = Text("h = 24 cm", font_size=22, color=GREEN_C)
        h_lbl.next_to(h_dash, RIGHT, buff=0.10)
        cone_tag = Text("Cone (clay)", font_size=22, color=ORANGE_A)
        cone_tag.move_to(cx + DOWN * 2.1)

        self.play(FadeIn(cone_L), FadeIn(cone_R))
        self.play(FadeIn(bot_ell), FadeIn(apex_dot))
        self.play(Write(r_lbl), Create(h_dash), Write(h_lbl), Write(cone_tag))
        self.wait(0.8)

        # Right half: volume of cone
        e1 = Text("Volume of cone",                    font_size=26, color=WHITE)
        e2 = Text("V = (1/3) π r² h",                 font_size=28, color=WHITE)
        e3 = Text("  = (1/3) π × 6² × 24", font_size=25, color=YELLOW)
        e4 = Text("  = 288π  cm³",                     font_size=28, color=GOLD, weight="BOLD")
        rhs1 = VGroup(e1, e2, e3, e4).arrange(DOWN, buff=0.30, aligned_edge=LEFT)
        rhs1.move_to(RIGHT * 2.8 + UP * 0.8)

        for s in rhs1:
            self.play(Write(s), run_time=0.55)
            self.wait(0.8)
        self.play(Circumscribe(e4, color=GOLD, buff=0.10))
        self.wait(0.8)

        # ── TRANSITION ─────────────────────────────────────────────────────────
        trans = Text("Clay reshaped into a sphere →", font_size=22, color=WHITE)
        trans.move_to(cx + UP * 3.4)
        self.play(Write(trans), run_time=0.5)
        self.wait(0.5)
        self.play(FadeOut(VGroup(cone_L, cone_R, bot_ell, apex_dot,
                                  r_lbl, h_dash, h_lbl, cone_tag, trans)))
        self.play(FadeOut(rhs1))

        # ── ACT 2: SPHERE ──────────────────────────────────────────────────────
        sphere = Circle(radius=1.9, fill_color=PURPLE_D, fill_opacity=0.80,
                        stroke_color=PURPLE_A, stroke_width=3)
        sphere.set_color_by_gradient(PURPLE_A, PURPLE_E)
        sphere.move_to(cx)
        hi = Ellipse(width=0.60, height=0.38,
                     fill_color=WHITE, fill_opacity=0.55, stroke_width=0)
        hi.move_to(cx + UP * 1.05 + LEFT * 0.60)
        r_line = Line(cx, cx + RIGHT * 1.9, color=CYAN, stroke_width=3)
        r_unk  = Text("R = ?", font_size=24, color=CYAN)
        r_unk.next_to(r_line, UP, buff=0.10)
        sph_tag = Text("Sphere (same clay)", font_size=22, color=PURPLE_A)
        sph_tag.move_to(cx + DOWN * 2.5)

        self.play(Create(sphere))
        self.play(FadeIn(hi), Create(r_line), Write(r_unk), Write(sph_tag))
        self.wait(0.8)

        # Right half: solve for R
        s1 = Text("Volume conserved:",               font_size=26, color=WHITE)
        s2 = Text("(4/3) π R³ = V_cone",            font_size=26, color=WHITE)
        s3 = Text("(4/3) π R³ = 288π",                font_size=26, color=YELLOW)
        s4 = Text("R³ = 288 × 3/4 = 216",              font_size=26, color=YELLOW)
        s5 = Text("R = ³√216 = 6 cm",                   font_size=30, color=GOLD, weight="BOLD")
        rhs2 = VGroup(s1, s2, s3, s4, s5).arrange(DOWN, buff=0.30, aligned_edge=LEFT)
        rhs2.move_to(RIGHT * 2.8 + UP * 0.5)

        for s in rhs2:
            self.play(Write(s), run_time=0.55)
            self.wait(0.8)

        # Final answer celebration
        ans_box = SurroundingRectangle(s5, color=GOLD, buff=0.15, corner_radius=0.10)
        self.play(Create(ans_box))
        r_final = Text("R = 6 cm", font_size=24, color=GOLD, weight="BOLD")
        r_final.next_to(r_line, UP, buff=0.10)
        self.play(Transform(r_unk, r_final))
        self.play(
            Circumscribe(s5, color=GOLD, buff=0.12),
            Flash(s5.get_center(), color=GOLD, flash_radius=1.5, num_lines=12),
        )
        self.wait(2.0)
```

### GEOMETRY TYPE 12: HOLLOW HEMISPHERE → CYLINDER (volume conservation)
# TRIGGER: "hollow hemispherical shell", "internal/external diameter", "hollow hemisphere melted",
#          "recast into solid cylinder", "find height of cylinder", "melted and recast"
# VISUAL:  Act 1 — isometric hollow hemisphere on LEFT (outer arc + inner arc), formulas on RIGHT.
#          Act 2 — cylinder outline on LEFT (after FadeOut), solve V_shell = V_cyl on RIGHT.
#          NEVER use ThreeDScene — 2D arcs render correctly and faster.
# NOTE:    Adapt R, r, r_cyl, h_answer from the ACTUAL problem values.

```python
import numpy as np
import math as _math
from manim import *

# ---- Adapt these values from the ACTUAL problem ----
R_outer  = 5      # external radius of hemisphere (cm)
r_inner  = 3      # internal radius of hemisphere (cm)
r_cyl    = 7      # radius of cylinder (cm)
h_answer = "4/3"  # height answer as string (cm)
# Intermediate values:
R3_val   = R_outer**3              # = 125
r3_val   = r_inner**3              # = 27
diff3    = R3_val - r3_val         # = 98
v_num    = 2 * diff3               # = 196 (numerator of (2/3)*diff3 with 3 in denom)
# ---- End of adapted values ----

SCALE = 0.42   # visual scale for arcs

class MathAnimationScene(Scene):
    def construct(self):
        bg = Rectangle(width=16, height=9, fill_color="#0d0d0d", fill_opacity=1)
        self.add(bg)

        title = Text("Hollow Hemisphere → Cylinder", font_size=30, color=YELLOW)
        title.to_edge(UP, buff=0.25)
        self.play(Write(title), run_time=0.6)
        self.wait(0.4)

        # ── ACT 1: HOLLOW HEMISPHERE ────────────────────────────────────────
        cx = LEFT * 3.0 + DOWN * 0.3

        # Arcs open downward: start_angle=0 (right), sweep PI to left = top dome
        outer_arc = Arc(radius=R_outer * SCALE, start_angle=0, angle=PI,
                        stroke_color=ORANGE, stroke_width=4)
        outer_arc.move_to(cx)
        outer_base = Line(
            cx + LEFT  * (R_outer * SCALE),
            cx + RIGHT * (R_outer * SCALE),
            stroke_color=ORANGE, stroke_width=4
        )

        inner_arc = Arc(radius=r_inner * SCALE, start_angle=0, angle=PI,
                        stroke_color=ORANGE, stroke_width=3)
        inner_arc.move_to(cx)
        inner_base = Line(
            cx + LEFT  * (r_inner * SCALE),
            cx + RIGHT * (r_inner * SCALE),
            stroke_color=ORANGE, stroke_width=3
        )

        R_lbl = Text("R = 5 cm", font_size=22, color=ORANGE)
        R_lbl.next_to(cx + RIGHT * (R_outer * SCALE), RIGHT, buff=0.12)
        r_lbl = Text("r = 3 cm", font_size=22, color=ORANGE)
        r_lbl.move_to(cx + UP * (r_inner * SCALE * 0.6) + LEFT * 0.5)
        hem_tag = Text("Hollow Shell (clay)", font_size=20, color=ORANGE)
        hem_tag.move_to(cx + DOWN * 1.5)

        self.play(Create(outer_arc), Create(outer_base), run_time=0.8)
        self.play(Create(inner_arc), Create(inner_base), run_time=0.6)
        self.play(Write(R_lbl), Write(r_lbl), Write(hem_tag), run_time=0.7)
        self.wait(0.6)

        # Right: volume formula steps
        e1 = Text("Volume of hollow shell:", font_size=25, color=WHITE)
        e2 = Text("V = (2/3)π(R³ − r³)",    font_size=26, color=WHITE)
        e3 = Text("  = (2/3)π(5³ − 3³)",    font_size=25, color=YELLOW)
        e4 = Text("  = (2/3)π(125 − 27)",   font_size=25, color=YELLOW)
        e5 = Text("  = (196/3)π  cm³",       font_size=27, color=GOLD, weight="BOLD")
        rhs1 = VGroup(e1, e2, e3, e4, e5).arrange(DOWN, buff=0.28, aligned_edge=LEFT)
        rhs1.move_to(RIGHT * 2.5 + UP * 0.7)

        for s in rhs1:
            self.play(Write(s), run_time=0.55)
            self.wait(0.7)
        self.play(Circumscribe(e5, color=GOLD, buff=0.10))
        self.wait(0.6)

        # ── TRANSITION ──────────────────────────────────────────────────────
        trans = Text("Shell melted → solid cylinder →", font_size=21, color=WHITE)
        trans.move_to(cx + UP * 2.5)
        self.play(Write(trans), run_time=0.5)
        self.wait(0.4)
        self.play(FadeOut(VGroup(outer_arc, outer_base, inner_arc, inner_base,
                                  R_lbl, r_lbl, hem_tag, trans)))
        self.play(FadeOut(rhs1))

        # ── ACT 2: CYLINDER ─────────────────────────────────────────────────
        cyl_w = 2 * r_cyl * SCALE * 1.0
        cyl_h = 0.9   # visual height (not proportional)
        cyl_rect = Rectangle(width=cyl_w, height=cyl_h,
                              stroke_color=TEAL_A, stroke_width=4,
                              fill_color=TEAL_E, fill_opacity=0.20)
        cyl_rect.move_to(cx)
        cyl_top_ell = Ellipse(width=cyl_w, height=0.30,
                              stroke_color=TEAL_A, stroke_width=3,
                              fill_color=TEAL_A, fill_opacity=0.12)
        cyl_top_ell.move_to(cx + UP * (cyl_h / 2))

        rc_lbl = Text("r_cyl = 7 cm", font_size=22, color=TEAL_A)
        rc_lbl.next_to(cyl_rect.get_bottom(), DOWN, buff=0.18)
        h_unk = Text("h = ?", font_size=24, color=YELLOW)
        h_unk.next_to(cyl_rect, RIGHT, buff=0.20)
        cyl_tag = Text("Solid Cylinder", font_size=20, color=TEAL_A)
        cyl_tag.move_to(cx + DOWN * 1.5)

        self.play(Create(cyl_rect), FadeIn(cyl_top_ell), run_time=0.8)
        self.play(Write(rc_lbl), Write(h_unk), Write(cyl_tag), run_time=0.7)
        self.wait(0.6)

        # Right: equate and solve
        s1 = Text("Volume of cylinder:",               font_size=25, color=WHITE)
        s2 = Text("V_cyl = π × 7² × h",               font_size=26, color=WHITE)
        s3 = Text("      = 49πh",                      font_size=26, color=YELLOW)
        s4 = Text("Volume conserved  →  V_shell = V_cyl", font_size=23, color=WHITE)
        s5 = Text("(196/3)π = 49πh",                  font_size=26, color=YELLOW)
        s6 = Text("h = 196 / (3 × 49)",               font_size=26, color=YELLOW)
        s7 = Text("h = 4/3 cm",                        font_size=32, color=GOLD, weight="BOLD")
        rhs2 = VGroup(s1, s2, s3, s4, s5, s6, s7).arrange(DOWN, buff=0.24, aligned_edge=LEFT)
        rhs2.move_to(RIGHT * 2.5 + UP * 0.4)

        for s in rhs2:
            self.play(Write(s), run_time=0.50)
            self.wait(0.65)

        # Answer celebration
        ans_box = SurroundingRectangle(s7, color=GOLD, buff=0.15, corner_radius=0.10)
        self.play(Create(ans_box))
        h_final = Text("h = 4/3 cm", font_size=24, color=GOLD, weight="BOLD")
        h_final.next_to(cyl_rect, RIGHT, buff=0.20)
        self.play(Transform(h_unk, h_final))
        self.play(
            Circumscribe(s7, color=GOLD, buff=0.12),
            Flash(s7.get_center(), color=GOLD, flash_radius=1.5, num_lines=12),
        )
        self.wait(2.0)
```\
"""
