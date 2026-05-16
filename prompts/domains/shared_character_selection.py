CHARACTER_SELECTION = """\
==============================================================================
DOMAIN -> CHARACTER SMART SELECTION (always from the DETECTED domain)
==============================================================================

CHARACTER RULE -- MANDATORY:
  DEFAULT CHARACTER: make_human(shirt_color=...) with distinct skin/hair/shirt/pants.
  make_emoji() may ONLY be used as small accent decorations (scale 0.5-0.7, at screen edges)
  or as a quick reaction pop-up that FadeOuts immediately. NEVER as the main character.
  make_emoji() as a large standing character looks like a generic yellow blob -- students
  disengage. make_human() has skin tone, hair, coloured shirt and dark pants -- it looks
  like a real cartoon boy or girl.

  FORBIDDEN: make_emoji() at scale > 0.8 as a standing character.
  FORBIDDEN: Two large emoji faces at LEFT and RIGHT edges as the "characters".
  CORRECT:   make_human(shirt_color=BLUE_C,  scale=1.0, emotion="shocked") at LEFT edge.
             make_human(shirt_color=GREEN_C, scale=1.0, emotion="happy")   at RIGHT edge.
  PHYSICS:   make_athlete(shirt_color=BLUE_C, scale=0.6) at FAR LEFT for projectile/sports.

BODY LANGUAGE POSES -- use pose= to match the story moment:
  pose="neutral"   : arms hanging down (default -- standing at rest, listening)
  pose="thinking"  : right arm bent up, forearm toward chin (pondering, confused, reading)
  pose="excited"   : right arm raised straight up (eureka!, got the answer, celebrating)
  pose="explaining": right arm extended forward/sideways (pointing at equation, presenting)

  CONTEXTUAL POSE GUIDE (change pose between acts to tell a story with body language):
    Character first sees the problem         -> pose="thinking",  emotion="thinking"
    Character gets the key insight           -> pose="excited",   emotion="happy"
    Character explains a step to viewer     -> pose="explaining", emotion="neutral"
    Character celebrating the final answer   -> pose="excited",   emotion="happy"
    Character surprised by the result        -> pose="neutral",   emotion="shocked"
  REBUILD the character with a new pose between acts using GrowFromCenter() or FadeIn()
  so the body language visibly changes. Example:
    char = self.make_human(shirt_color=TEAL, emotion="thinking", pose="thinking")
    char.to_edge(RIGHT).shift(LEFT*0.5+DOWN*0.5)
    self.play(GrowFromCenter(char))
    # ... equations play ...
    self.play(FadeOut(char))
    char2 = self.make_human(shirt_color=TEAL, emotion="happy", pose="excited")
    char2.to_edge(RIGHT).shift(LEFT*0.5+DOWN*0.5)
    self.play(GrowFromCenter(char2))

DETECTED DOMAIN       | CHARACTERS + STYLE
----------------------|-------------------------------------------------------
Algebra / Equations   | make_human(shirt_color=TEAL, emotion="thinking") detective at RIGHT
                      | make_robot() analyzes balance scale (LEFT edge)
                      | Puzzle lock opens each step; stars burst on answer
----------------------|-------------------------------------------------------
Calculus derivatives  | make_human(shirt_color=ORANGE) RIDES a car/ball along the curve (LEFT)
                      | make_robot() at RIGHT reads out the slope value
                      | Roller coaster genre: "SPEED:" HUD updating
----------------------|-------------------------------------------------------
Calculus integrals    | Water/color fills area under curve (wave animation)
                      | make_human(emotion="shocked") at edge as area fills
                      | Bridge or tank as real-world anchor
----------------------|-------------------------------------------------------
Geometry              | make_human() architect DRAWS shapes with a compass (LEFT)
                      | Blueprint grid background (crosshatch gray lines)
                      | Shapes construct themselves with Create() + glow
----------------------|-------------------------------------------------------
Trigonometry          | make_human() SPINS on unit circle like a dance move
                      | Sound wave rises from circle at right
                      | make_robot() at edge reads "frequency: X Hz"
----------------------|-------------------------------------------------------
Statistics            | make_human(emotion="neutral") DETECTIVE with magnifying glass
                      | Data dots appear one by one on a map/grid
                      | Bar chart bars GROW from zero dramatically
----------------------|-------------------------------------------------------
Linear Algebra        | make_robot() OPERATES on vectors (pushes them)
                      | Grid lines transform under matrix multiplication
                      | Stars trail behind transformed vectors
----------------------|-------------------------------------------------------
Physics / Kinematics  | Domain OBJECTS (sphere, car, ball) ARE the hero
                      | make_human(shirt_color=ORANGE, scale=0.55) sports commentator at FAR RIGHT
                      | Projectile: make_athlete(shirt_color=BLUE_C, scale=0.6) at FAR LEFT
                      |   ball is center-stage; stadium sky+grass background mandatory
                      | Free fall: ball on LEFT half; height axis; equations on RIGHT half
                      | Newton's Laws / Forces: free body diagram + make_athlete() for dynamics
                      | Force arrows grow; energy bars animate
----------------------|-------------------------------------------------------
Quadratics            | Arcade game style: ball bounces, score updates
                      | make_human(emotion="happy") player at LEFT edge, cheering
                      | Parabola arc drawn as the "shot path"
----------------------|-------------------------------------------------------
Number Theory         | make_robot() CRACKS the lock (prime combination)
                      | Cryptography vault visual: digits clicking into place
                      | make_human(emotion="happy") cheers when it unlocks
----------------------|-------------------------------------------------------
Word Problems-People  | make_human() (scale 1.0) ARE the scene actors
                      | Each person gets a badge; they walk in from edges
                      | Average bar appears between them
----------------------|-------------------------------------------------------
Word Problems-Objects | Domain objects (coins, pizza, vehicles) ARE actors
                      | make_human() as side commentator at edge; objects animate
                      | Flowers + stars as accent decorations

DECORATION RULES (apply to EVERY animation):
  make_flower -- scatter 2-3 at screen corners or bottom
                 LaggedStart(*[GrowFromCenter(f)...], lag_ratio=0.15)
  make_heart  -- pop 1-3 on each correct step completion
                 GrowFromCenter(h) then Flash(h, color=RED)
  Stars       -- burst on the FINAL answer
                 Use Star() directly: Star(n=6, outer_radius=0.4, inner_radius=0.16,
                                          color=YELLOW, fill_color=YELLOW, fill_opacity=1)
  NEVER call self.make_star() -- it does NOT exist as a Star class in Manim;
  use the explicit Star() constructor shown above.\
"""
