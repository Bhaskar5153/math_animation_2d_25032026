import re, pathlib

path = pathlib.Path(r'outputs/animations/CoinTossProbability_20260326_124034.py')
code = path.read_text(encoding='utf-8')

fixes_applied = 0

# ── Fix 1 ──────────────────────────────────────────────────────────────────
# bubble_text string has a literal newline inside double-quotes, and the 4
# lines that follow (problem_bubble, self.play, self.wait) lost their indentation.
old1 = (
    '        bubble_text = "If 4 of us toss a coin...\n'
    "what's the probability of getting\n"
    'exactly 1 Head and 3 Tails?"\n'
    'problem_bubble = self.make_bubble(bubble_text, fsize=24).scale(0.8)\n'
    'problem_bubble.next_to(pippa, UL, buff=0.1).shift(UP*0.5)\n'
    'self.play(Write(problem_bubble))\n'
    'self.wait(2.0)\n'
)
new1 = (
    '        bubble_text = "If 4 of us toss a coin...\\nwhat\'s the probability of getting\\nexactly 1 Head and 3 Tails?"\n'
    '        problem_bubble = self.make_bubble(bubble_text, fsize=24).scale(0.8)\n'
    '        problem_bubble.next_to(pippa, UL, buff=0.1).shift(UP*0.5)\n'
    '        self.play(Write(problem_bubble))\n'
    '        self.wait(2.0)\n'
)

# ── Fix 2 ──────────────────────────────────────────────────────────────────
# generator_label Text() has a literal newline inside its string argument
old2 = (
    '        generator_label = Text("Possibility\n'
    'Generator 3000", font_size=24, color=WHITE).move_to(generator_body.get_center())\n'
)
new2 = (
    '        generator_label = Text("Possibility\\nGenerator 3000", font_size=24, color=WHITE).move_to(generator_body.get_center())\n'
)

# ── Fix 3 ──────────────────────────────────────────────────────────────────
# lesson_bubble make_bubble() call has a literal newline inside its string argument
old3 = (
    '        lesson_bubble = self.make_bubble("Probability is just counting what you WANT...\n'
    'over EVERYTHING that could happen!", fsize=22, width=5.0, height=1.8)\n'
)
new3 = (
    '        lesson_bubble = self.make_bubble("Probability is just counting what you WANT...\\nover EVERYTHING that could happen!", fsize=22, width=5.0, height=1.8)\n'
)

for i, (old, new) in enumerate([(old1, new1), (old2, new2), (old3, new3)], 1):
    if old in code:
        code = code.replace(old, new, 1)
        print(f'Fix {i}: applied')
        fixes_applied += 1
    else:
        print(f'Fix {i}: NOT FOUND — showing nearby content')
        # Show first 80 chars of old to help debug
        key = old.split('\n')[0][:60]
        idx = code.find(key)
        if idx >= 0:
            print('  Nearby:', repr(code[idx:idx+200]))

# ── Fix 4 ──────────────────────────────────────────────────────────────────
# VGroup(*self.mobjects) → Group(*self.mobjects) (sanitiser rule)
before = code.count('VGroup(*self.mobjects)')
code = code.replace('VGroup(*self.mobjects)', 'Group(*self.mobjects)')
after_count = before - code.count('Group(*self.mobjects)')
if before:
    print(f'Fix 4: replaced {before} VGroup(*self.mobjects) → Group(*self.mobjects)')
    fixes_applied += 1

path.write_text(code, encoding='utf-8')
print(f'\nDone — {fixes_applied} fixes applied. Saved to {path}')
