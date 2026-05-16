PHYSICS_FORCES_HELPERS = """\
### PHYSICS -- INCLINED PLANE + ROLLING
```python
import math as _math
def make_incline(self, theta_deg=30, base=5.5, color=GRAY_A):
    theta = _math.radians(theta_deg)
    origin = LEFT*3.5 + DOWN*1.8
    base_pt = origin + RIGHT*base
    surface_end = origin + RIGHT*base*_math.cos(theta) + UP*base*_math.sin(theta)
    plane  = Polygon(origin, base_pt, surface_end,
                     color=color, fill_color=GRAY_D, fill_opacity=0.5, stroke_width=2)
    angle_arc = Arc(radius=0.5, start_angle=0, angle=theta,
                    color=YELLOW, stroke_width=3, arc_center=origin)
    angle_lbl = Text(str(theta_deg) + "\\u00b0", font_size=22, color=YELLOW)
    angle_lbl.next_to(angle_arc, RIGHT, buff=0.1)
    return VGroup(plane), angle_arc, angle_lbl, origin, surface_end, theta

def make_sphere_on_incline(self, origin, surface_end, theta, sphere_radius=0.35, color=BLUE_C):
    normal = np.array([-_math.sin(theta), _math.cos(theta), 0])
    start_pos = np.array([surface_end[0], surface_end[1], 0]) + normal * sphere_radius
    end_pos   = np.array([origin[0],      origin[1],      0]) + normal * sphere_radius
    sphere = Circle(radius=sphere_radius, color=color, fill_color=color, fill_opacity=0.85)
    sphere.move_to(start_pos)
    spoke = Line(sphere.get_center(), sphere.get_center() + RIGHT*sphere_radius,
                 color=WHITE, stroke_width=3)
    return VGroup(sphere, spoke), start_pos, end_pos

def roll_sphere(self, sphere_group, start_pos, end_pos, anim_time=2.5):
    dist = np.linalg.norm(end_pos - start_pos)
    self.play(
        sphere_group.animate.move_to(end_pos),
        Rotating(sphere_group[1], angle=-dist/0.35,
                 about_point=sphere_group[0].get_center(),
                 run_time=anim_time, rate_func=smooth),
        run_time=anim_time, rate_func=smooth)

def make_force_arrows(self, sphere_center, theta):
    slope_dir  = np.array([_math.cos(theta), -_math.sin(theta), 0])
    normal_dir = np.array([-_math.sin(theta),  _math.cos(theta), 0])
    arr_g = Arrow(sphere_center, sphere_center + DOWN*1.2, color=RED, buff=0,
                  stroke_width=5, max_tip_length_to_length_ratio=0.18)
    arr_n = Arrow(sphere_center, sphere_center + normal_dir*1.1, color=GREEN_C, buff=0,
                  stroke_width=5, max_tip_length_to_length_ratio=0.18)
    arr_f = Arrow(sphere_center, sphere_center - slope_dir*0.7, color=ORANGE, buff=0,
                  stroke_width=5, max_tip_length_to_length_ratio=0.2)
    lbl_g = Text("mg", font_size=24, color=RED).next_to(arr_g.get_end(), DOWN, buff=0.1)
    lbl_n = Text("N",  font_size=24, color=GREEN_C).next_to(arr_n.get_end(), normal_dir, buff=0.08)
    lbl_f = Text("f",  font_size=24, color=ORANGE).next_to(arr_f.get_end(), -slope_dir, buff=0.08)
    return VGroup(arr_g, lbl_g), VGroup(arr_n, lbl_n), VGroup(arr_f, lbl_f)

def make_energy_bars(self, ke_trans_h, ke_rot_h, pe_h, x_offset=0):
    bw = 0.7; base_y = -1.2
    bar_kt = Rectangle(width=bw, height=ke_trans_h, color=BLUE_C, fill_color=BLUE_C, fill_opacity=0.9)
    bar_kt.move_to(RIGHT*(x_offset-1.2) + UP*(base_y + ke_trans_h/2))
    bar_kr = Rectangle(width=bw, height=ke_rot_h, color=TEAL, fill_color=TEAL, fill_opacity=0.9)
    bar_kr.move_to(RIGHT*(x_offset-0.4) + UP*(base_y + ke_rot_h/2))
    bar_pe = Rectangle(width=bw, height=pe_h, color=ORANGE, fill_color=ORANGE, fill_opacity=0.9)
    bar_pe.move_to(RIGHT*(x_offset+0.4) + UP*(base_y + pe_h/2))
    lbl_kt = Text("KE\\ntrans", font_size=18, color=BLUE_C).next_to(bar_kt, DOWN, buff=0.1)
    lbl_kr = Text("KE\\nrot",   font_size=18, color=TEAL  ).next_to(bar_kr, DOWN, buff=0.1)
    lbl_pe = Text("PE",         font_size=18, color=ORANGE ).next_to(bar_pe, DOWN, buff=0.1)
    return VGroup(bar_kt, bar_kr, bar_pe, lbl_kt, lbl_kr, lbl_pe)
```

### PHYSICS -- SPORTS BROADCAST HUD (always add for physics problems)
```python
# "INSTANT REPLAY" banner -- slam it down from above the frame
replay_banner = Text("INSTANT REPLAY", font_size=36, color=WHITE, weight="BOLD")
replay_banner.set_color_by_gradient(ORANGE, YELLOW)
replay_bg = SurroundingRectangle(replay_banner, color=ORANGE,
                                  fill_color=ORANGE, fill_opacity=0.9,
                                  buff=0.2, corner_radius=0.1)
replay_group = VGroup(replay_bg, replay_banner).to_edge(UP).shift(UP*3)
self.play(replay_group.animate.to_edge(UP), rate_func=ease_out_bounce, run_time=0.8)
self.wait(0.4)
self.play(FadeOut(replay_group))
```\
"""
