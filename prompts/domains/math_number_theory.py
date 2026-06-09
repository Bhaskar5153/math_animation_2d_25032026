NUMBER_THEORY_HELPERS = """\
### NUMBER THEORY TYPE 1: DIVISION ALGORITHM (a = bq + r)
# Use for: "Find q and r satisfying a = bq + r", "apply Euclid's division lemma",
#          "HCF using Euclid's algorithm", "express a in the form bq+r"
#
# VISUAL DESIGN: Wide horizontal BAR (not a number line) split into
#   - PURPLE section = q equal groups of b units each (with dashed dividers inside)
#   - GOLD section   = remainder r (always wide enough to be visible)
#   - Brace above PURPLE: "q=11 groups of b=11"
#   - Brace above GOLD:   "r=4"
#   - Brace below whole:  "a=125"
#   - First group annotated below bar with double arrow: "b=11"
#   - Group counter (1 → 2 → ... → q) animates inside the bar
#
# LAYOUT: Bar fills LEFT half (shift LEFT*1.5). Equation steps on RIGHT*2.8.
#
# CRITICAL: Use str() + concatenation for ALL Text labels.
#           NEVER use f-strings or variable placeholders in Text().
#
# Color scheme: PURPLE bar, PINK dividers/strokes, GOLD remainder, WHITE braces

```python
import numpy as np
from manim import *

# --- Adapt to actual problem values ---
a_val = 17   # dividend
b_val = 5    # divisor
q_val = 3    # quotient  = a_val // b_val
r_val = 2    # remainder = a_val %  b_val

# Pre-compute label strings -- no f-strings
a_str  = str(a_val)
b_str  = str(b_val)
q_str  = str(q_val)
r_str  = str(r_val)
bq_str = str(b_val * q_val)

# -------------------------------------------------------
# BAR LAYOUT CONSTANTS
# -------------------------------------------------------
bar_total_w   = 8.0       # fixed total width -- fills LEFT half
bar_h         = 1.3       # bar height (tall enough to read labels inside)
bar_left_edge = LEFT * 4.0  # left anchor of the bar

# Minimum visible width for the gold block (so r is ALWAYS visible)
gold_min_w  = 0.9
purple_w    = bar_total_w - (gold_min_w if r_val > 0 else 0)
gold_w      = gold_min_w if r_val > 0 else 0

bar_center_y = UP * 0.4   # vertical center of the bar

# -------------------------------------------------------
# PURPLE BAR (q groups of b)
# -------------------------------------------------------
purple_bar = Rectangle(
    width=purple_w, height=bar_h,
    fill_color=PURPLE, fill_opacity=0.82,
    stroke_color=PINK, stroke_width=2,
)
purple_bar.align_to(bar_left_edge, LEFT).move_to(
    np.array([bar_left_edge[0] + purple_w / 2, bar_center_y[1], 0])
)

# Dashed vertical dividers inside purple bar (one per group boundary)
group_w = purple_w / q_val   # width of one group on screen
dividers = VGroup()
for i in range(1, q_val):
    x_pos = bar_left_edge[0] + i * group_w
    div = DashedLine(
        start=np.array([x_pos, bar_center_y[1] - bar_h / 2, 0]),
        end=  np.array([x_pos, bar_center_y[1] + bar_h / 2, 0]),
        color=WHITE, stroke_width=1.2, dash_length=0.12,
    )
    dividers.add(div)

# Group number labels inside the bar
# For large q, label only first, middle, last -- and "..." in between
def make_group_labels(q_val, bar_left_edge, bar_center_y, group_w):
    labels = VGroup()
    show_idx = set([0, q_val - 1])
    if q_val > 4:
        show_idx.add(q_val // 2)
    for i in range(q_val):
        x_center = bar_left_edge[0] + (i + 0.5) * group_w
        if i in show_idx:
            lbl = Text(str(i + 1), font_size=15, color=WHITE)
            lbl.move_to(np.array([x_center, bar_center_y[1], 0]))
            labels.add(lbl)
    if q_val > 4:
        # add "..." between first visible and middle
        x_dots = bar_left_edge[0] + (1.5) * group_w
        dots = Text("...", font_size=18, color=WHITE)
        dots.move_to(np.array([x_dots, bar_center_y[1], 0]))
        labels.add(dots)
    return labels

group_num_labels = make_group_labels(q_val, bar_left_edge, bar_center_y, group_w)

# -------------------------------------------------------
# GOLD BAR (remainder r)
# -------------------------------------------------------
gold_bar = None
if r_val > 0:
    gold_bar = Rectangle(
        width=gold_w, height=bar_h,
        fill_color=GOLD, fill_opacity=0.90,
        stroke_color=YELLOW, stroke_width=2,
    )
    gold_bar.next_to(purple_bar, RIGHT, buff=0)
    gold_lbl = Text("r=" + r_str, font_size=18, color=BLACK, weight="BOLD")
    gold_lbl.move_to(gold_bar.get_center())

# -------------------------------------------------------
# BRACES AND LABELS
# -------------------------------------------------------
# Brace above PURPLE: "q=<q> groups of b=<b>"
purple_brace = Brace(purple_bar, UP, buff=0.08, color=PINK)
purple_brace_lbl = Text(
    "q=" + q_str + " groups  (each b=" + b_str + ")",
    font_size=19, color=PINK,
)
purple_brace_lbl.next_to(purple_brace, UP, buff=0.07)

# Brace above GOLD: "r=<r>"
if r_val > 0:
    gold_brace = Brace(gold_bar, UP, buff=0.08, color=GOLD)
    gold_brace_lbl = Text("r=" + r_str, font_size=19, color=GOLD)
    gold_brace_lbl.next_to(gold_brace, UP, buff=0.07)

# Brace below full bar: "a=<a>"
full_bar_group = VGroup(purple_bar, gold_bar) if r_val > 0 else VGroup(purple_bar)
a_brace = Brace(full_bar_group, DOWN, buff=0.08, color=WHITE)
a_brace_lbl = Text("a = " + a_str, font_size=22, color=WHITE)
a_brace_lbl.next_to(a_brace, DOWN, buff=0.07)

# Double-arrow annotation under FIRST group: "<-- b=5 -->"
first_left  = np.array([bar_left_edge[0],            bar_center_y[1] - bar_h / 2 - 0.55, 0])
first_right = np.array([bar_left_edge[0] + group_w,  bar_center_y[1] - bar_h / 2 - 0.55, 0])
b_arrow = DoubleArrow(first_left, first_right, color=CYAN, stroke_width=2.5, buff=0)
b_lbl = Text("b = " + b_str, font_size=17, color=CYAN)
b_lbl.next_to(b_arrow, DOWN, buff=0.07)

# -------------------------------------------------------
# EQUATION STEPS (RIGHT HALF)
# -------------------------------------------------------
eq1 = Text("Given: a=" + a_str + ",  b=" + b_str, font_size=30, color=WHITE)
eq2 = Text("How many groups of " + b_str + " fit in " + a_str + "?", font_size=22, color=GRAY_A)
eq3 = Text(a_str + " / " + b_str + " = " + q_str + " remainder " + r_str, font_size=26, color=CYAN)
eq4 = Text("Division Algorithm:", font_size=24, color=GRAY_A)
eq5 = Text("a  =  b * q  +  r", font_size=30, color=PURPLE)
eq6 = Text(a_str + " = " + b_str + " * " + q_str + " + " + r_str, font_size=30, color=TEAL)
eq7 = Text(a_str + " = " + bq_str + " + " + r_str + " [check]", font_size=26, color=TEAL)
ans = Text("q = " + q_str + ",   r = " + r_str, font_size=38, color=GOLD, weight="BOLD")

eq_stack = VGroup(eq1, eq2, eq3, eq4, eq5, eq6, eq7, ans)
eq_stack.arrange(DOWN, buff=0.30, aligned_edge=LEFT)
eq_stack.move_to(RIGHT * 2.8 + UP * 0.3)

# -------------------------------------------------------
# SCENE ANIMATION
# -------------------------------------------------------
# 1. Show the full bar (empty) with "a=..." label
self.play(Create(purple_bar))
if r_val > 0:
    self.play(FadeIn(gold_bar), Write(gold_lbl))
self.play(
    GrowFromEdge(a_brace, LEFT),
    Write(a_brace_lbl),
)
self.wait(2.5)

# 2. Show b-width annotation on first group
self.play(GrowArrow(b_arrow), Write(b_lbl))
self.wait(2.0)

# 3. Show dividers (group separators) appearing
self.play(Create(dividers), run_time=1.5)
self.play(FadeIn(group_num_labels))
self.wait(2.0)

# 4. Show braces labeling q groups and remainder
self.play(
    GrowFromEdge(purple_brace, LEFT),
    Write(purple_brace_lbl),
)
self.wait(1.5)
if r_val > 0:
    self.play(
        GrowFromEdge(gold_brace, RIGHT),
        Write(gold_brace_lbl),
    )
self.wait(2.0)

# 5. Equation steps on RIGHT HALF
for step in [eq1, eq2, eq3, eq4, eq5, eq6, eq7]:
    self.play(Write(step), run_time=0.7)
    self.wait(2.0)

# 6. Final answer
self.play(Write(ans))
self.play(Circumscribe(ans, color=GOLD, buff=0.18))
self.wait(4.0)
```

### NUMBER THEORY TYPE 2: EUCLID'S ALGORITHM FOR HCF
# Use for: "Find HCF of a and b using Euclid's algorithm", "find GCD using repeated division"
# VISUAL: Step-by-step division table on LEFT + final HCF highlighted GOLD on RIGHT.
# Each step: a = b*q + r  then use (b, r) as next pair. Stop when r=0.
# CRITICAL: Use str() + concatenation for ALL Text labels -- NO variable placeholders.

```python
import numpy as np
from manim import *

# --- Adapt these two numbers to the actual problem ---
num1, num2 = 56, 20

# Build steps automatically
steps = []
a_, b_ = max(num1, num2), min(num1, num2)
while b_ != 0:
    q_, r_ = divmod(a_, b_)
    steps.append((a_, b_, q_, r_))
    a_, b_ = b_, r_
hcf = a_

# Build one Text row per step using str() + concatenation
step_rows = VGroup()
for i, (sa, sb, sq, sr) in enumerate(steps):
    row_txt = ("Step " + str(i + 1) + ":   " +
               str(sa) + " = " + str(sb) + " x " + str(sq) + " + " + str(sr))
    row = Text(
        row_txt,
        font_size=30,
        color=GOLD if sr == 0 else WHITE,
    )
    step_rows.add(row)
step_rows.arrange(DOWN, buff=0.50, aligned_edge=LEFT)
step_rows.move_to(LEFT * 2.0 + UP * 0.5)

for i, row in enumerate(step_rows):
    self.play(Write(row), run_time=0.9)
    self.wait(2.0)
    if steps[i][3] == 0:
        self.play(Circumscribe(row, color=GOLD, buff=0.15))
        zero_note = Text("Remainder = 0  -->  HCF found!", font_size=22, color=GOLD)
        zero_note.next_to(row, DOWN, buff=0.25)
        self.play(Write(zero_note))
        self.wait(1.5)

# Final HCF answer on RIGHT half
hcf_label = Text("HCF  =", font_size=36, color=WHITE)
hcf_val   = Text(str(hcf), font_size=80, color=GOLD, weight="BOLD")
hcf_val.set_color_by_gradient(GOLD, YELLOW)
hcf_group = VGroup(hcf_label, hcf_val).arrange(DOWN, buff=0.25)
hcf_group.move_to(RIGHT * 2.8 + DOWN * 0.2)
self.play(Write(hcf_label), GrowFromCenter(hcf_val))
self.play(Flash(hcf_val.get_center(), color=GOLD, flash_radius=1.2, num_lines=12))
self.wait(3.0)
```

### NUMBER THEORY TYPE 3: HCF AND LCM BY PRIME FACTORIZATION
# Use for: "Find HCF and LCM by prime factorization method"
#
# VISUAL:
#   Scene 1 -- FACTOR TREES side by side (LEFT = num1, RIGHT = num2)
#              Branches drawn with Line(); nodes are Circle+Text.
#              Prime-leaf nodes glow CYAN/TEAL to stand out.
#   Scene 2 -- VENN DIAGRAM of prime factors
#              Left circle  = factors only in num1
#              Center       = common factors (product = HCF, highlighted GOLD)
#              Right circle = factors only in num2
#              ALL factors  = product = LCM (highlighted GREEN_C)
#   Scene 3 -- Final answer HCF and LCM, gold box, Flash.
#
# CRITICAL: str() + concatenation ONLY -- NO f-strings, NO variable placeholders.
# SCREEN: Trees fill full screen; Venn diagram centered full screen.
#
# Adapt the following values and positions to the actual problem numbers.

```python
import numpy as np
from manim import *

# --- Adapt to actual problem ---
num1 = 12
num2 = 18

# Label strings -- str() only, NO f-strings
num1_str = str(num1)
num2_str = str(num2)

# -------------------------------------------------------
# HELPER: draw one tree node as Circle + Text
# -------------------------------------------------------
def tree_node(val_str, pos, node_color, font_size=26):
    circ = Circle(radius=0.36, color=node_color, stroke_width=2.0)
    circ.set_fill(node_color, opacity=0.20)
    circ.move_to(pos)
    lbl = Text(val_str, font_size=font_size, color=node_color)
    lbl.move_to(pos)
    return VGroup(circ, lbl)

def branch(p_pos, c_pos):
    # Shorten line so it does not overlap the circles
    direction = c_pos - p_pos
    length = np.linalg.norm(direction)
    unit = direction / length
    start = p_pos + unit * 0.37
    end   = c_pos - unit * 0.37
    return Line(start, end, color=GRAY_B, stroke_width=1.8)

# -------------------------------------------------------
# SCENE 1: FACTOR TREES
# -------------------------------------------------------
# --- Tree for num1 = 12:  12 -> 2  and  6 -> 2  and  3 ---
# Positions (LEFT half)
t1_root = np.array([-4.2,  2.2, 0])
t1_L    = np.array([-5.4,  0.6, 0])   # prime "2"
t1_R    = np.array([-3.0,  0.6, 0])   # node  "6"
t1_RL   = np.array([-3.8, -0.9, 0])   # prime "2"
t1_RR   = np.array([-2.2, -0.9, 0])   # prime "3"

nd1_root = tree_node(num1_str, t1_root, WHITE,  30)
nd1_L    = tree_node("2",      t1_L,   CYAN,   26)
nd1_R    = tree_node("6",      t1_R,   WHITE,  26)
nd1_RL   = tree_node("2",      t1_RL,  CYAN,   26)
nd1_RR   = tree_node("3",      t1_RR,  TEAL,   26)

br1_L    = branch(t1_root, t1_L)
br1_R    = branch(t1_root, t1_R)
br1_RL   = branch(t1_R,    t1_RL)
br1_RR   = branch(t1_R,    t1_RR)

# Prime label rings (extra highlight on leaf nodes)
ring1_L  = Circle(radius=0.45, color=CYAN,  stroke_width=2.5).move_to(t1_L)
ring1_RL = Circle(radius=0.45, color=CYAN,  stroke_width=2.5).move_to(t1_RL)
ring1_RR = Circle(radius=0.45, color=TEAL,  stroke_width=2.5).move_to(t1_RR)

lbl_tree1 = Text(num1_str + " = 2 x 2 x 3 = 2^2 x 3", font_size=22, color=CYAN)
lbl_tree1.move_to(np.array([-4.0, -2.2, 0]))

# --- Tree for num2 = 18:  18 -> 2  and  9 -> 3  and  3 ---
# Positions (RIGHT half)
t2_root = np.array([ 3.2,  2.2, 0])
t2_L    = np.array([ 2.0,  0.6, 0])   # prime "2"
t2_R    = np.array([ 4.4,  0.6, 0])   # node  "9"
t2_RL   = np.array([ 3.6, -0.9, 0])   # prime "3"
t2_RR   = np.array([ 5.2, -0.9, 0])   # prime "3"

nd2_root = tree_node(num2_str, t2_root, WHITE,  30)
nd2_L    = tree_node("2",      t2_L,   CYAN,   26)
nd2_R    = tree_node("9",      t2_R,   WHITE,  26)
nd2_RL   = tree_node("3",      t2_RL,  TEAL,   26)
nd2_RR   = tree_node("3",      t2_RR,  TEAL,   26)

br2_L    = branch(t2_root, t2_L)
br2_R    = branch(t2_root, t2_R)
br2_RL   = branch(t2_R,    t2_RL)
br2_RR   = branch(t2_R,    t2_RR)

ring2_L  = Circle(radius=0.45, color=CYAN, stroke_width=2.5).move_to(t2_L)
ring2_RL = Circle(radius=0.45, color=TEAL, stroke_width=2.5).move_to(t2_RL)
ring2_RR = Circle(radius=0.45, color=TEAL, stroke_width=2.5).move_to(t2_RR)

lbl_tree2 = Text(num2_str + " = 2 x 3 x 3 = 2 x 3^2", font_size=22, color=TEAL)
lbl_tree2.move_to(np.array([ 3.5, -2.2, 0]))

# Divider line between the two trees
divider = DashedLine(UP * 3.0, DOWN * 2.5, color=GRAY_B, stroke_width=1.2, dash_length=0.18)

# Animate tree construction
self.play(FadeIn(nd1_root), FadeIn(nd2_root), Create(divider))
self.wait(1.5)
# First split
self.play(Create(br1_L), Create(br1_R), Create(br2_L), Create(br2_R), run_time=1.2)
self.play(FadeIn(nd1_L), FadeIn(nd1_R), FadeIn(nd2_L), FadeIn(nd2_R))
self.wait(2.0)
# Second split
self.play(Create(br1_RL), Create(br1_RR), Create(br2_RL), Create(br2_RR), run_time=1.2)
self.play(FadeIn(nd1_RL), FadeIn(nd1_RR), FadeIn(nd2_RL), FadeIn(nd2_RR))
self.wait(1.5)
# Highlight prime leaves
self.play(Create(ring1_L), Create(ring1_RL), Create(ring1_RR),
          Create(ring2_L), Create(ring2_RL), Create(ring2_RR), run_time=1.0)
self.play(Write(lbl_tree1), Write(lbl_tree2))
self.wait(3.0)

# -------------------------------------------------------
# SCENE 2: VENN DIAGRAM of prime factors
# -------------------------------------------------------
tree_group = VGroup(
    nd1_root, nd1_L, nd1_R, nd1_RL, nd1_RR,
    br1_L, br1_R, br1_RL, br1_RR,
    ring1_L, ring1_RL, ring1_RR, lbl_tree1,
    nd2_root, nd2_L, nd2_R, nd2_RL, nd2_RR,
    br2_L, br2_R, br2_RL, br2_RR,
    ring2_L, ring2_RL, ring2_RR, lbl_tree2,
    divider,
)
self.play(FadeOut(tree_group))
self.wait(0.4)

# !! LAYOUT: Venn circles stay in LEFT HALF. Equations go to RIGHT HALF. !!
# !! NEVER center a Venn/diagram on the full screen — it leaves no room for text. !!

# Venn circles — LEFT HALF only
# 12 = [2, 2, 3]  |  18 = [2, 3, 3]
# Only-in-12: [2]     Common: [2, 3]     Only-in-18: [3]
v_radius = 1.5
lc = LEFT * 3.0   # left circle center  — spans x: -4.5 to -1.5 (LEFT half)
rc = LEFT * 1.0   # right circle center — spans x: -2.5 to +0.5 (mostly LEFT)
# Overlap lens center is approximately LEFT*2.0

left_circ  = Circle(radius=v_radius, color=BLUE_B,  stroke_width=2.5)
right_circ = Circle(radius=v_radius, color=ORANGE,  stroke_width=2.5)
left_circ.set_fill(BLUE_B,  opacity=0.12)
right_circ.set_fill(ORANGE, opacity=0.12)
left_circ.move_to(lc)
right_circ.move_to(rc)

# Circle headings (above each circle — clear of the circles)
head_left  = Text("Factors of " + num1_str, font_size=19, color=BLUE_B)
head_left.move_to(lc + UP * 1.8)
head_right = Text("Factors of " + num2_str, font_size=19, color=ORANGE)
head_right.move_to(rc + UP * 1.8)

# Prime factor tokens placed in correct regions
# Left-only region (center of left non-overlap zone): x ≈ -3.8
tok_left = Text("2", font_size=48, color=BLUE_B, weight="BOLD")
tok_left.move_to(np.array([-3.8, 0.0, 0]))

# Center overlap region (lens center): x ≈ -2.0
tok_c2 = Text("2", font_size=42, color=TEAL, weight="BOLD")
tok_c2.move_to(np.array([-2.0, 0.38, 0]))
tok_c3 = Text("3", font_size=42, color=TEAL, weight="BOLD")
tok_c3.move_to(np.array([-2.0, -0.52, 0]))

# Right-only region (center of right non-overlap zone): x ≈ -0.3
tok_right = Text("3", font_size=48, color=ORANGE, weight="BOLD")
tok_right.move_to(np.array([-0.3, 0.0, 0]))

# HCF and LCM equations on RIGHT HALF — stacked vertically, NEVER overlapping
hcf_eq  = Text("HCF  =  2 x 3  =  6",          font_size=28, color=GOLD,    weight="BOLD")
hcf_sub = Text("(product of common factors)",    font_size=17, color=GOLD)
lcm_eq  = Text("LCM  =  2 x 2 x 3 x 3  =  36", font_size=26, color=GREEN_C, weight="BOLD")
lcm_sub = Text("(product of all factors)",       font_size=17, color=GREEN_C)

# Stack HCF block and LCM block vertically on RIGHT half
hcf_block = VGroup(hcf_eq, hcf_sub).arrange(DOWN, buff=0.10)
lcm_block = VGroup(lcm_eq, lcm_sub).arrange(DOWN, buff=0.10)
eq_column = VGroup(hcf_block, lcm_block).arrange(DOWN, buff=0.55)
eq_column.move_to(RIGHT * 2.8 + UP * 0.2)   # RIGHT half — NEVER overlaps Venn

# Build Venn diagram
self.play(Create(left_circ), Create(right_circ))
self.play(Write(head_left), Write(head_right))
self.wait(1.5)

# Fill in tokens one region at a time
self.play(FadeIn(tok_left))
self.wait(0.8)
self.play(FadeIn(tok_c2), FadeIn(tok_c3))
self.wait(0.8)
self.play(FadeIn(tok_right))
self.wait(2.0)

# Highlight center region = HCF
self.play(
    tok_c2.animate.set_color(GOLD),
    tok_c3.animate.set_color(GOLD),
)
self.play(Write(hcf_eq), Write(hcf_sub))
self.play(Flash(RIGHT * 2.8, color=GOLD, flash_radius=0.8, num_lines=10))
self.wait(2.5)

# Highlight all regions = LCM
self.play(
    tok_left.animate.set_color(GREEN_C),
    tok_c2.animate.set_color(GREEN_C),
    tok_c3.animate.set_color(GREEN_C),
    tok_right.animate.set_color(GREEN_C),
)
self.play(Write(lcm_eq), Write(lcm_sub))
self.play(Flash(RIGHT * 2.8 + DOWN * 1.0, color=GREEN_C, flash_radius=0.8, num_lines=10))
self.wait(3.0)

# -------------------------------------------------------
# SCENE 3: FINAL ANSWER -- stacked vertically, NEVER side by side
# !! CRITICAL: ALWAYS use VGroup.arrange(DOWN) for multiple answer boxes !!
# !! NEVER place two Text boxes at the same or adjacent positions manually !!
# -------------------------------------------------------
self.play(FadeOut(Group(*self.mobjects)))
self.wait(0.3)

ans_hcf = Text("HCF  =  6",  font_size=80, color=GOLD,    weight="BOLD")
ans_lcm = Text("LCM  =  36", font_size=80, color=GREEN_C, weight="BOLD")

# Arrange VERTICALLY with generous spacing — prevents all overlap
answer_stack = VGroup(ans_hcf, ans_lcm).arrange(DOWN, buff=1.0)
answer_stack.move_to(ORIGIN)   # centered on full screen (both boxes clear of each other)

rect_hcf = SurroundingRectangle(ans_hcf, color=GOLD,    buff=0.30, stroke_width=2.5)
rect_lcm = SurroundingRectangle(ans_lcm, color=GREEN_C, buff=0.30, stroke_width=2.5)

self.play(Write(ans_hcf), Create(rect_hcf))
self.play(Write(ans_lcm), Create(rect_lcm))
self.play(
    Flash(ans_hcf.get_center(), color=GOLD,    flash_radius=1.8, num_lines=12),
    Flash(ans_lcm.get_center(), color=GREEN_C, flash_radius=1.8, num_lines=12),
)
self.wait(4.0)
```\
"""
