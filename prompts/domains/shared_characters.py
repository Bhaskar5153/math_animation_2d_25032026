CHARACTER_LIBRARY = """\
==============================================================================
CHARACTER LIBRARY (define ALL as methods on MathAnimationScene)
==============================================================================

### CARTOON HUMAN (multi-colour: skin tone head, coloured shirt, dark navy pants)
```python
def make_human(self, shirt_color=BLUE_C, scale=1.0, emotion="neutral", pose="neutral"):
    SKIN_C  = "#FDBCB4"   # warm peach skin
    HAIR_C  = "#1a0f00"   # dark brown hair
    PANTS_C = "#1e2d5a"   # dark navy trousers
    SHOE_C  = "#0d0a05"   # dark shoes
    # Hair: dark circle shifted slightly up so it peeks above the skin-tone head
    hair_bg = Circle(radius=0.35, color=HAIR_C, fill_color=HAIR_C, fill_opacity=1)
    hair_bg.shift(UP*0.08)
    # Skin-tone head (drawn over hair_bg so hair only shows at top)
    head = Circle(radius=0.32, color=SKIN_C, fill_color=SKIN_C, fill_opacity=1)
    l_eye   = Dot(LEFT*0.12  + UP*0.07, radius=0.055, color=WHITE,    fill_opacity=1)
    r_eye   = Dot(RIGHT*0.12 + UP*0.07, radius=0.055, color=WHITE,    fill_opacity=1)
    l_pupil = Dot(LEFT*0.12  + UP*0.07, radius=0.030, color="#1a1a1a", fill_opacity=1)
    r_pupil = Dot(RIGHT*0.12 + UP*0.07, radius=0.030, color="#1a1a1a", fill_opacity=1)
    l_brow  = Line(LEFT*0.19+UP*0.20, LEFT*0.06+UP*0.22, color=HAIR_C, stroke_width=2.5)
    r_brow  = Line(RIGHT*0.06+UP*0.22, RIGHT*0.19+UP*0.20, color=HAIR_C, stroke_width=2.5)
    if emotion == "happy":
        mouth = Arc(radius=0.12, start_angle=-PI*0.75, angle=PI*0.5,
                    color="#cc4444", stroke_width=2.5).move_to(DOWN*0.10)
    elif emotion == "shocked":
        mouth = Circle(radius=0.06, color="#cc4444", fill_color="#cc4444", fill_opacity=1).move_to(DOWN*0.10)
    elif emotion == "thinking":
        mouth = Arc(radius=0.10, start_angle=-PI*0.5, angle=PI*0.28,
                    color="#cc4444", stroke_width=2.5).move_to(RIGHT*0.04+DOWN*0.11)
    else:
        mouth = Line(LEFT*0.09+DOWN*0.10, RIGHT*0.09+DOWN*0.10, color="#cc4444", stroke_width=2.5)
    face = VGroup(hair_bg, head, l_eye, r_eye, l_pupil, r_pupil, l_brow, r_brow, mouth)
    # Shirt (shirt_color) torso
    torso = RoundedRectangle(width=0.52, height=0.68, corner_radius=0.10,
                              color=shirt_color, fill_color=shirt_color, fill_opacity=1)
    torso.next_to(head, DOWN, buff=0.0)
    # BOTH arms controlled by pose so the whole body tells the story:
    #   "neutral"   : both arms hang relaxed
    #   "thinking"  : left arm crosses body (elbow support); right elbow up, hand near chin
    #   "excited"   : both arms shoot up in a V (eureka! / celebrating)
    #   "explaining": right arm extended forward; left arm slightly raised for balance
    if pose == "thinking":
        l_arm_u = Line(torso.get_left()+UP*0.18, torso.get_left()+RIGHT*0.05+UP*0.22,
                       color=shirt_color, stroke_width=6)
        l_arm_d = Line(l_arm_u.get_end(), l_arm_u.get_end()+RIGHT*0.18+UP*0.08,
                       color=SKIN_C, stroke_width=5)
        r_arm_u = Line(torso.get_right()+UP*0.18, torso.get_right()+RIGHT*0.12+UP*0.36,
                       color=shirt_color, stroke_width=6)
        r_arm_d = Line(r_arm_u.get_end(), r_arm_u.get_end()+LEFT*0.28+UP*0.06,
                       color=SKIN_C, stroke_width=5)
    elif pose == "excited":
        l_arm_u = Line(torso.get_left()+UP*0.18, torso.get_left()+LEFT*0.10+UP*0.36,
                       color=shirt_color, stroke_width=6)
        l_arm_d = Line(l_arm_u.get_end(), l_arm_u.get_end()+LEFT*0.06+UP*0.30,
                       color=SKIN_C, stroke_width=5)
        r_arm_u = Line(torso.get_right()+UP*0.18, torso.get_right()+RIGHT*0.10+UP*0.36,
                       color=shirt_color, stroke_width=6)
        r_arm_d = Line(r_arm_u.get_end(), r_arm_u.get_end()+UP*0.30,
                       color=SKIN_C, stroke_width=5)
    elif pose == "explaining":
        l_arm_u = Line(torso.get_left()+UP*0.18, torso.get_left()+LEFT*0.20+UP*0.15,
                       color=shirt_color, stroke_width=6)
        l_arm_d = Line(l_arm_u.get_end(), l_arm_u.get_end()+DOWN*0.22,
                       color=SKIN_C, stroke_width=5)
        r_arm_u = Line(torso.get_right()+UP*0.18, torso.get_right()+RIGHT*0.30+UP*0.10,
                       color=shirt_color, stroke_width=6)
        r_arm_d = Line(r_arm_u.get_end(), r_arm_u.get_end()+RIGHT*0.28,
                       color=SKIN_C, stroke_width=5)
    else:  # neutral
        l_arm_u = Line(torso.get_left()+UP*0.18, torso.get_left()+LEFT*0.30+DOWN*0.03,
                       color=shirt_color, stroke_width=6)
        l_arm_d = Line(l_arm_u.get_end(), l_arm_u.get_end()+DOWN*0.30, color=SKIN_C, stroke_width=5)
        r_arm_u = Line(torso.get_right()+UP*0.18, torso.get_right()+RIGHT*0.30+DOWN*0.03,
                       color=shirt_color, stroke_width=6)
        r_arm_d = Line(r_arm_u.get_end(), r_arm_u.get_end()+DOWN*0.30, color=SKIN_C, stroke_width=5)
    l_hand  = Circle(radius=0.08, color=SKIN_C, fill_color=SKIN_C, fill_opacity=1).move_to(l_arm_d.get_end())
    r_hand  = Circle(radius=0.08, color=SKIN_C, fill_color=SKIN_C, fill_opacity=1).move_to(r_arm_d.get_end())
    # Dark navy trousers + dark shoes
    l_leg   = Line(torso.get_bottom()+LEFT*0.12,  torso.get_bottom()+LEFT*0.15+DOWN*0.55,
                   color=PANTS_C, stroke_width=7)
    r_leg   = Line(torso.get_bottom()+RIGHT*0.12, torso.get_bottom()+RIGHT*0.15+DOWN*0.55,
                   color=PANTS_C, stroke_width=7)
    l_foot  = Ellipse(width=0.28, height=0.12, color=SHOE_C, fill_color=SHOE_C, fill_opacity=1).move_to(l_leg.get_end()+DOWN*0.06)
    r_foot  = Ellipse(width=0.28, height=0.12, color=SHOE_C, fill_color=SHOE_C, fill_opacity=1).move_to(r_leg.get_end()+DOWN*0.06)
    return VGroup(face, torso, l_arm_u, l_arm_d, l_hand,
                  r_arm_u, r_arm_d, r_hand,
                  l_leg, l_foot, r_leg, r_foot).scale(scale)
```

### ATHLETE (physics / sports scenes -- throwing pose, sports cap)
```python
def make_athlete(self, shirt_color=BLUE_C, scale=1.0):
    SKIN_C  = "#FDBCB4"
    HAIR_C  = "#1a0f00"
    PANTS_C = "#1e4a2a"   # dark green sports shorts
    SHOE_C  = "#0d0a05"
    CAP_C   = "#1a1a6a"   # dark navy sports cap
    # Hair behind head
    hair_bg  = Circle(radius=0.35, color=HAIR_C, fill_color=HAIR_C, fill_opacity=1)
    hair_bg.shift(UP*0.06)
    # Sports cap: oval dome + forward brim
    cap_dome = Ellipse(width=0.68, height=0.24, color=CAP_C, fill_color=CAP_C, fill_opacity=1)
    cap_dome.shift(UP*0.26)
    cap_brim = RoundedRectangle(width=0.40, height=0.09, corner_radius=0.02,
                                  color=CAP_C, fill_color=CAP_C, fill_opacity=1)
    cap_brim.shift(RIGHT*0.28+UP*0.10)
    head = Circle(radius=0.32, color=SKIN_C, fill_color=SKIN_C, fill_opacity=1)
    l_eye   = Dot(LEFT*0.12  + UP*0.07, radius=0.050, color=WHITE,    fill_opacity=1)
    r_eye   = Dot(RIGHT*0.12 + UP*0.07, radius=0.050, color=WHITE,    fill_opacity=1)
    l_pupil = Dot(LEFT*0.12  + UP*0.07, radius=0.028, color="#1a1a1a", fill_opacity=1)
    r_pupil = Dot(RIGHT*0.12 + UP*0.07, radius=0.028, color="#1a1a1a", fill_opacity=1)
    l_brow  = Line(LEFT*0.19+UP*0.20, LEFT*0.06+UP*0.22, color=HAIR_C, stroke_width=2.5)
    r_brow  = Line(RIGHT*0.06+UP*0.22, RIGHT*0.19+UP*0.20, color=HAIR_C, stroke_width=2.5)
    mouth   = Arc(radius=0.10, start_angle=-PI*0.65, angle=PI*0.30,
                  color="#cc4444", stroke_width=2.5).move_to(DOWN*0.10)
    face = VGroup(hair_bg, cap_dome, cap_brim, head,
                  l_eye, r_eye, l_pupil, r_pupil, l_brow, r_brow, mouth)
    torso = RoundedRectangle(width=0.52, height=0.65, corner_radius=0.10,
                              color=shirt_color, fill_color=shirt_color, fill_opacity=1)
    torso.next_to(head, DOWN, buff=0.0)
    # Left arm: relaxed/back
    l_arm_u = Line(torso.get_left()+UP*0.18, torso.get_left()+LEFT*0.22+DOWN*0.05,
                   color=shirt_color, stroke_width=6)
    l_arm_d = Line(l_arm_u.get_end(), l_arm_u.get_end()+LEFT*0.06+DOWN*0.28, color=SKIN_C, stroke_width=5)
    l_hand  = Circle(radius=0.08, color=SKIN_C, fill_color=SKIN_C, fill_opacity=1).move_to(l_arm_d.get_end())
    # Right arm: RAISED FORWARD (throwing pose -- goes UP+RIGHT)
    r_arm_u = Line(torso.get_right()+UP*0.22, torso.get_right()+RIGHT*0.12+UP*0.32,
                   color=shirt_color, stroke_width=6)
    r_arm_d = Line(r_arm_u.get_end(), r_arm_u.get_end()+RIGHT*0.24+UP*0.14, color=SKIN_C, stroke_width=5)
    r_hand  = Circle(radius=0.08, color=SKIN_C, fill_color=SKIN_C, fill_opacity=1).move_to(r_arm_d.get_end())
    # Sports shorts -- one leg forward (running stance)
    l_leg = Line(torso.get_bottom()+LEFT*0.12,  torso.get_bottom()+LEFT*0.28+DOWN*0.48,
                 color=PANTS_C, stroke_width=7)
    r_leg = Line(torso.get_bottom()+RIGHT*0.12, torso.get_bottom()+RIGHT*0.10+DOWN*0.55,
                 color=PANTS_C, stroke_width=7)
    l_foot = Ellipse(width=0.30, height=0.12, color=SHOE_C, fill_color=SHOE_C, fill_opacity=1).move_to(l_leg.get_end()+DOWN*0.06)
    r_foot = Ellipse(width=0.30, height=0.12, color=SHOE_C, fill_color=SHOE_C, fill_opacity=1).move_to(r_leg.get_end()+DOWN*0.06)
    return VGroup(face, torso, l_arm_u, l_arm_d, l_hand,
                  r_arm_u, r_arm_d, r_hand,
                  l_leg, l_foot, r_leg, r_foot).scale(scale)
```

### EMOJI FACE
```python
def make_emoji(self, emotion="happy", size=0.65):
    face  = Circle(radius=size, color=YELLOW, fill_color=YELLOW, fill_opacity=1)
    l_eye = Dot(LEFT*size*0.35 + UP*size*0.2,  radius=size*0.1, color=BLACK)
    r_eye = Dot(RIGHT*size*0.35 + UP*size*0.2, radius=size*0.1, color=BLACK)
    if emotion == "shocked":
        mouth = Circle(radius=size*0.18, color=BLACK, fill_color=BLACK, fill_opacity=1).move_to(DOWN*size*0.25)
        brow_l = Line(LEFT*size*0.5+UP*size*0.55, LEFT*size*0.2+UP*size*0.45, color=BLACK, stroke_width=4)
        brow_r = Line(RIGHT*size*0.2+UP*size*0.45, RIGHT*size*0.5+UP*size*0.55, color=BLACK, stroke_width=4)
        return VGroup(face, l_eye, r_eye, mouth, brow_l, brow_r)
    else:
        mouth = Arc(radius=size*0.45, start_angle=-PI*0.75, angle=PI*0.5,
                    color=BLACK, stroke_width=4).move_to(DOWN*size*0.15)
        return VGroup(face, l_eye, r_eye, mouth)
```

### ROBOT CHARACTER
```python
def make_robot(self, color=TEAL, scale=1.0):
    body = RoundedRectangle(width=0.68, height=0.82, corner_radius=0.08,
                             color=color, fill_color=color, fill_opacity=1)
    head = RoundedRectangle(width=0.58, height=0.46, corner_radius=0.06,
                             color=color, fill_color=color, fill_opacity=1)
    head.next_to(body, UP, buff=0.05)
    ant_pole = Line(head.get_top(), head.get_top()+UP*0.24, color=GRAY_A, stroke_width=3)
    ant_ball = Dot(ant_pole.get_end(), radius=0.08, color=YELLOW, fill_opacity=1)
    l_eye = RoundedRectangle(width=0.15, height=0.12, corner_radius=0.03,
                              color=YELLOW, fill_color=YELLOW, fill_opacity=1)
    l_eye.move_to(head.get_center()+LEFT*0.15+UP*0.08)
    r_eye = l_eye.copy().move_to(head.get_center()+RIGHT*0.15+UP*0.08)
    m_dots = VGroup(*[Dot(head.get_center()+RIGHT*(i-1)*0.1+DOWN*0.1,
                          radius=0.025, color=GREEN_C, fill_opacity=1) for i in range(3)])
    l_arm = RoundedRectangle(width=0.2, height=0.52, corner_radius=0.05,
                              color=GRAY_A, fill_color=GRAY_A, fill_opacity=1)
    l_arm.next_to(body, LEFT, buff=0.04).shift(UP*0.14)
    r_arm = l_arm.copy().next_to(body, RIGHT, buff=0.04).shift(UP*0.14)
    l_leg = RoundedRectangle(width=0.22, height=0.48, corner_radius=0.05,
                              color=GRAY_D, fill_color=GRAY_D, fill_opacity=1)
    l_leg.next_to(body, DOWN, buff=0.04).shift(LEFT*0.18)
    r_leg = l_leg.copy().next_to(body, DOWN, buff=0.04).shift(RIGHT*0.18)
    panel = RoundedRectangle(width=0.36, height=0.28, corner_radius=0.04,
                              color=GRAY_A, fill_color=GRAY_A, fill_opacity=0.65)
    panel.move_to(body.get_center()+UP*0.1)
    p_dot = Dot(panel.get_center(), radius=0.06, color=RED, fill_opacity=1)
    return VGroup(l_leg, r_leg, body, l_arm, r_arm,
                  head, ant_pole, ant_ball, l_eye, r_eye, m_dots,
                  panel, p_dot).scale(scale)
```

### SPEECH BUBBLE / DIALOGUE
```python
def make_bubble(self, txt, fsize=22, color=WHITE):
    lbl  = Text(txt, font_size=fsize, color=BLACK)
    rect = SurroundingRectangle(lbl, color=color, fill_color=color,
                                fill_opacity=1, buff=0.2, corner_radius=0.15)
    tail = Triangle(color=color, fill_color=color, fill_opacity=1).scale(0.15)
    tail.next_to(rect, DL, buff=-0.12).rotate(PI/5)
    return VGroup(rect, lbl, tail)

# CHARACTER DIALOGUE PATTERN (two characters talking):
# char1 at LEFT edge, char2 at RIGHT edge -- they exchange lines one at a time
#
# b1 = self.make_bubble("Wait, the derivative is zero here!", fsize=18)
# b1.next_to(char1, UR, buff=0.15)
# self.play(FadeIn(b1, shift=UP*0.2)); self.wait(1.5)
# self.play(FadeOut(b1))
# b2 = self.make_bubble("That means a critical point -- local max or min!", fsize=18)
# b2.next_to(char2, UL, buff=0.15)
# self.play(FadeIn(b2, shift=UP*0.2)); self.wait(1.5)
# self.play(FadeOut(b2))
```

### DECORATION OBJECTS
```python
def make_star(self, color=YELLOW, size=0.4):
    pts = []
    for i in range(10):
        r = size if i%2==0 else size*0.45
        a = PI/2 + i*TAU/10
        pts.append([r*_math.cos(a), r*_math.sin(a), 0])
    return Polygon(*pts, color=color, fill_color=color, fill_opacity=1, stroke_width=0)

def make_heart(self, color=RED, size=0.6):
    left_bump  = Arc(radius=size*0.5, start_angle=0, angle=PI,
                     color=color, fill_color=color, fill_opacity=1, stroke_width=0)
    left_bump.shift(LEFT*size*0.5 + UP*size*0.3)
    right_bump = Arc(radius=size*0.5, start_angle=0, angle=PI,
                     color=color, fill_color=color, fill_opacity=1, stroke_width=0)
    right_bump.shift(RIGHT*size*0.5 + UP*size*0.3)
    body = Triangle(color=color, fill_color=color, fill_opacity=1, stroke_width=0)
    body.scale(size*0.88).rotate(PI).shift(DOWN*size*0.12)
    return VGroup(left_bump, right_bump, body)

def make_flower(self, color=PINK, center_color=YELLOW, scale=1.0, n_petals=6):
    stem   = Line(DOWN*0.65, ORIGIN, color=GREEN_C, stroke_width=4)
    leaf_l = Ellipse(width=0.34, height=0.17, color=GREEN_C, fill_color=GREEN_C, fill_opacity=1)
    leaf_l.move_to(LEFT*0.2+DOWN*0.32).rotate(PI/5)
    leaf_r = leaf_l.copy().move_to(RIGHT*0.2+DOWN*0.32).rotate(-PI/5)
    petals = VGroup()
    for i in range(n_petals):
        ang   = i * TAU / n_petals
        petal = Ellipse(width=0.22, height=0.44, color=color,
                        fill_color=color, fill_opacity=0.88, stroke_width=0)
        petal.rotate(ang).shift(_math.cos(ang)*RIGHT*0.28 + _math.sin(ang)*UP*0.28)
        petals.add(petal)
    center = Circle(radius=0.22, color=center_color, fill_color=center_color, fill_opacity=1)
    return VGroup(stem, leaf_l, leaf_r, petals, center).scale(scale)

def confetti(self, origin=ORIGIN, n=20):
    dots   = VGroup()
    colors = [RED, YELLOW, GREEN_C, BLUE_C, ORANGE, PINK, PURPLE, TEAL]
    for i in range(n):
        dots.add(Dot(point=origin, radius=0.13,
                     color=colors[i%len(colors)], fill_opacity=1))
    self.play(LaggedStart(*[
        d.animate.move_to(origin + RIGHT*_math.cos(TAU*i/n)*3.0
                                  + UP   *_math.sin(TAU*i/n)*2.5)
        for i, d in enumerate(dots)
    ], lag_ratio=0.03, run_time=1.3))
    self.play(FadeOut(dots), run_time=0.4)
```\
"""
