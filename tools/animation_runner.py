"""
Animation runner tool — saves Manim code and executes it to produce a video.
"""
import asyncio
import concurrent.futures
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from config import audio as audio_cfg
from config import manim as manim_cfg
from config import output as output_cfg

ANIMATIONS_DIR = output_cfg.animations_dir
ANIMATIONS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# LaTeX → Unicode symbol map (applied to string content)
# ---------------------------------------------------------------------------
_LATEX_UNICODE = [
    # Greek lower
    (r"\alpha", "α"), (r"\beta", "β"), (r"\gamma", "γ"), (r"\delta", "δ"),
    (r"\epsilon", "ε"), (r"\zeta", "ζ"), (r"\eta", "η"), (r"\theta", "θ"),
    (r"\iota", "ι"), (r"\kappa", "κ"), (r"\lambda", "λ"), (r"\mu", "μ"),
    (r"\nu", "ν"), (r"\xi", "ξ"), (r"\pi", "π"), (r"\rho", "ρ"),
    (r"\sigma", "σ"), (r"\tau", "τ"), (r"\upsilon", "υ"), (r"\phi", "φ"),
    (r"\chi", "χ"), (r"\psi", "ψ"), (r"\omega", "ω"),
    # Greek upper
    (r"\Gamma", "Γ"), (r"\Delta", "Δ"), (r"\Theta", "Θ"), (r"\Lambda", "Λ"),
    (r"\Xi", "Ξ"), (r"\Pi", "Π"), (r"\Sigma", "Σ"), (r"\Phi", "Φ"),
    (r"\Psi", "Ψ"), (r"\Omega", "Ω"),
    # Operators & symbols
    (r"\infty", "∞"), (r"\partial", "∂"), (r"\nabla", "∇"),
    (r"\int", "∫"), (r"\sum", "∑"), (r"\prod", "∏"),
    (r"\sqrt", "√"), (r"\cdot", "·"), (r"\times", "×"), (r"\div", "÷"),
    (r"\pm", "±"), (r"\mp", "∓"),
    (r"\leq", "≤"), (r"\geq", "≥"), (r"\neq", "≠"),
    (r"\approx", "≈"), (r"\equiv", "≡"), (r"\sim", "~"),
    (r"\in", "∈"), (r"\notin", "∉"), (r"\subset", "⊂"), (r"\supset", "⊃"),
    (r"\cup", "∪"), (r"\cap", "∩"), (r"\emptyset", "∅"),
    (r"\rightarrow", "→"), (r"\leftarrow", "←"),
    (r"\Rightarrow", "⟹"), (r"\Leftarrow", "⟸"),
    (r"\leftrightarrow", "↔"), (r"\Leftrightarrow", "⟺"),
    (r"\forall", "∀"), (r"\exists", "∃"), (r"\neg", "¬"),
    (r"\ldots", "…"), (r"\cdots", "⋯"),
    # superscripts
    ("^{0}", "⁰"), ("^{1}", "¹"), ("^{2}", "²"), ("^{3}", "³"), ("^{4}", "⁴"),
    ("^{5}", "⁵"), ("^{6}", "⁶"), ("^{7}", "⁷"), ("^{8}", "⁸"), ("^{9}", "⁹"),
    ("^0", "⁰"), ("^1", "¹"), ("^2", "²"), ("^3", "³"), ("^4", "⁴"),
    ("^5", "⁵"), ("^6", "⁶"), ("^7", "⁷"), ("^8", "⁸"), ("^9", "⁹"),
    ("^{-1}", "⁻¹"), ("^{-2}", "⁻²"), ("^{n}", "ⁿ"),
    # subscripts -- use plain ASCII so Manim's font always renders them (subscript
    # Unicode chars U+2080-U+209C are NOT in Manim's default Fira-Sans font and
    # appear as colored boxes; use plain characters instead)
    ("_{0}", "0"), ("_{1}", "1"), ("_{2}", "2"), ("_{3}", "3"), ("_{4}", "4"),
    ("_{5}", "5"), ("_{6}", "6"), ("_{7}", "7"), ("_{8}", "8"), ("_{9}", "9"),
    ("_{n}", "n"), ("_{i}", "i"), ("_{x}", "x"), ("_{t}", "t"),
]

# Superscript digit map for single-char exponents inside regex
_SUP_DIGITS = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
               "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"}


def _latex_to_unicode(s: str) -> str:
    """Best-effort conversion of LaTeX notation to Unicode inside a string."""
    # Handle \frac{a}{b} → (a)/(b)
    s = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", s)
    # Handle \sqrt{x} → √(x)
    s = re.sub(r"\\sqrt\{([^{}]+)\}", r"√(\1)", s)
    # Handle \text{...} → ...
    s = re.sub(r"\\(?:text|mathrm|mathbf|mathit|boldsymbol)\{([^{}]*)\}", r"\1", s)
    # Handle x^{expr} multi-char — keep as x^expr
    s = re.sub(r"\^\{([^{}]+)\}", lambda m: "^" + m.group(1), s)
    # Handle _{expr} multi-char
    s = re.sub(r"_\{([^{}]+)\}", lambda m: "_" + m.group(1), s)
    # Apply symbol map
    for latex, uni in _LATEX_UNICODE:
        s = s.replace(latex, uni)
    # Remove \left \right \bigl \bigr etc.
    s = re.sub(r"\\(?:left|right|big[lr]?|[Bb]igg[lr]?)\s*", "", s)
    # Remove remaining lone braces
    s = re.sub(r"(?<!\\)[{}]", "", s)
    # Remove remaining unknown \commands
    s = re.sub(r"\\[a-zA-Z]+\s*", "", s)
    return s.strip()


# All MathTex-only method names that crash when called on a Text object
_MATHTEX_METHODS = (
    "get_part_by_tex",
    "get_parts_by_tex",
    "get_part_by_substring",
    "get_part_by_text",
    "set_color_by_tex",
    "set_color_by_tex_to_color_map",
    "set_submobject_colors_by_tex",
    "get_tex_string",
)

# Methods that look plausible but don't exist on Mobject
_FAKE_MOBJECT_METHODS = (
    "get_part_by_type",
    "get_parts_by_type",
    # below are LLM-invented methods that do not exist in Manim
    "get_part_by_custom_attribute",
    "get_custom_attribute",
    "set_custom_attribute",
    "undo",
)


def _fix_raw_newlines_in_strings(code: str) -> str:
    """
    Scan code character-by-character and replace any literal newline that
    appears *inside* a single- or double-quoted string literal with the
    two-character escape sequence \\n.

    Triple-quoted strings are passed through unchanged (they legitimately
    span multiple lines).  Comment lines and escaped characters are also
    handled correctly.

    This guards against LLMs that emit:
        Text("Line 1
        Line 2")
    instead of the valid:
        Text("Line 1\\nLine 2")
    """
    result: list[str] = []
    i = 0
    n = len(code)
    in_string = False
    quote_char: str | None = None

    while i < n:
        ch = code[i]

        if not in_string:
            if ch == "#":
                # Comment — copy to end-of-line, cannot contain string markers
                eol = code.find("\n", i)
                if eol == -1:
                    result.append(code[i:])
                    break
                result.append(code[i : eol + 1])
                i = eol + 1
                continue
            elif ch in ('"', "'"):
                # Check for triple quote
                tq = code[i : i + 3]
                if tq in ('"""', "'''"):
                    # Find the closing triple quote and pass through verbatim
                    close = code.find(tq, i + 3)
                    if close == -1:
                        result.append(code[i:])
                        break
                    result.append(code[i : close + 3])
                    i = close + 3
                    continue
                else:
                    in_string = True
                    quote_char = ch
                    result.append(ch)
                    i += 1
                    continue
            result.append(ch)
            i += 1
        else:
            # Inside a single- or double-quoted string
            if ch == "\\":
                # Escaped character — copy both chars as-is
                result.append(ch)
                if i + 1 < n:
                    result.append(code[i + 1])
                    i += 2
                else:
                    i += 1
            elif ch == "\n":
                # Raw newline inside a string literal → replace with \n escape
                result.append("\\n")
                i += 1
            elif ch == quote_char:
                # Closing quote
                in_string = False
                quote_char = None
                result.append(ch)
                i += 1
            else:
                result.append(ch)
                i += 1

    return "".join(result)


def _sanitize_no_latex(code: str) -> str:
    """
    Safety net: replace MathTex/Tex class names with Text and remove
    kwargs / methods that only exist on MathTex.  Does NOT touch string
    contents (to avoid accidentally corrupting code or comments).

    The primary defence is the animation prompt instructing the LLM to
    use Text + Unicode symbols from the start.  This function is a
    last-resort guard for stray MathTex uses.
    """
    # 0. Fix literal newlines inside single/double-quoted string literals
    code = _fix_raw_newlines_in_strings(code)

    # 1. Replace MathTex( → Text( (full word match)
    code = re.sub(r"\bMathTex\s*\(", "Text(", code)

    # 2. Replace standalone Tex( → Text(  (avoid touching Vertex, Complex…)
    code = re.sub(r"(?<![A-Za-z])Tex\s*\(", "Text(", code)

    # 3. Remove MathTex-only keyword arguments (won't exist on Text)
    for kwarg in ("substrings_to_isolate", "tex_environment", "tex_template",
                  "arg_separator"):
        code = re.sub(r",?\s*" + kwarg + r"\s*=\s*(?:[^,)\n]+)", "", code)

    # 4a. Remove entire assignment lines whose RHS uses a forbidden method.
    method_alt = "|".join(re.escape(m) for m in (*_MATHTEX_METHODS, *_FAKE_MOBJECT_METHODS))
    code = re.sub(
        r"^[ \t]*\w+\s*=\s*[^\n]+\.(?:" + method_alt + r")\([^)]*\)(?:\[\d+\])?[^\n]*\n",
        "",
        code,
        flags=re.MULTILINE,
    )

    # 4b. Remove remaining chained MathTex-only method calls (not assignments)
    for m in _MATHTEX_METHODS:
        code = re.sub(r"\." + re.escape(m) + r"\([^)]*\)(?:\[\d+\])?", "", code)

    # 4c. Replace fake Mobject methods with .get_center() so chained calls survive
    #     e.g.  obj.get_part_by_type(Circle).get_center()  → obj.get_center().get_center()
    for m in _FAKE_MOBJECT_METHODS:
        code = re.sub(r"\." + re.escape(m) + r"\([^)]*\)(?:\[\d+\])?", ".get_center()", code)

    # 5. Replace VGroup(*self.mobjects) → Group(*self.mobjects)
    #    VGroup only accepts VMobject; self.mobjects may contain plain Mobjects
    code = re.sub(r"\bVGroup\(\s*\*\s*self\.mobjects\s*\)", "Group(*self.mobjects)", code)

    # 5b. Replace Rectangle(... corner_radius=...) → RoundedRectangle(... corner_radius=...)
    #     Rectangle.__init__ does NOT accept corner_radius in Manim 0.18+;
    #     RoundedRectangle does. Only apply when corner_radius kwarg is present.
    #     \bRectangle\b won't match RoundedRectangle or SurroundingRectangle (no word boundary before R).
    code = re.sub(
        r"\bRectangle(\s*\([^)]*corner_radius\s*=)",
        "RoundedRectangle\\1",
        code,
    )

    # 6. Replace bare `bounce` rate_func (not a Manim built-in) → ease_out_bounce
    code = re.sub(r"\brate_func\s*=\s*bounce\b", "rate_func=ease_out_bounce", code)

    # 7. Ensure ease_out_bounce import exists if used
    if "ease_out_bounce" in code and "from manim.utils.rate_functions import" not in code:
        code = "from manim.utils.rate_functions import ease_out_bounce\n" + code

    # 8. Remove include_numbers=True from NumberLine/Axes — uses MathTex internally
    code = re.sub(r",?\s*include_numbers\s*=\s*True", "", code)

    # 9. Remove .add_coordinates(...) calls — Axes.add_coordinates() uses MathTex
    code = re.sub(r"\.\s*add_coordinates\s*\([^)]*\)", "", code)

    # 10. Remove x_axis_config / y_axis_config include_numbers dict entries
    code = re.sub(r",?\s*\"include_numbers\"\s*:\s*True", "", code)
    code = re.sub(r",?\s*'include_numbers'\s*:\s*True", "", code)

    # 11. Replace direction_constant[.copy()].rotate(angle) → np.array([cos,sin,0])
    #     Manim direction constants (RIGHT/UP/UR etc.) are numpy arrays — no .rotate().
    #     Covers: RIGHT LEFT UP DOWN UR UL DR DL, with or without .copy().
    def _dir_rotate_repl(m):
        angle_expr = m.group(1)
        return f"np.array([np.cos({angle_expr}), np.sin({angle_expr}), 0])"
    code = re.sub(
        r"(?:RIGHT|LEFT|UP|DOWN|UR|UL|DR|DL)(?:\.copy\(\))?\.rotate\(([^)]+)\)",
        _dir_rotate_repl,
        code,
    )

    # 12. Replace non-existent rate functions with valid Manim equivalents
    #     LLMs commonly invent names like shake, wobble, elastic, spring.
    _fake_rate_funcs = {
        "shake":       "there_and_back",
        "wobble":      "there_and_back",
        "elastic":     "ease_out_bounce",
        "spring":      "ease_out_bounce",
        "overshoot":   "ease_out_bounce",
        "rubber_band": "there_and_back",
    }
    for fake, real in _fake_rate_funcs.items():
        code = re.sub(r"\brate_func\s*=\s*" + fake + r"\b", f"rate_func={real}", code)

    # 13. Remove lines that call invented custom-attribute helpers the LLM makes up.
    #     e.g. pancho.get_part_by_custom_attribute("head")
    #          obj.get_custom_attribute("arms")
    #     Replace with .submobjects[0] so chained calls don't crash on NoneType.
    code = re.sub(
        r"\.get_part_by_custom_attribute\s*\([^)]*\)",
        ".submobjects[0]",
        code,
    )
    code = re.sub(
        r"\.get_custom_attribute\s*\([^)]*\)",
        ".submobjects[0]",
        code,
    )

    # 14b. Replace non-existent animation classes → safe equivalents.
    #      SpinIn / SpinOut are LLM-invented — not in Manim 0.20.
    #      Regex captures the first positional arg (the mobject variable name).
    code = re.sub(r"\bSpinIn\s*\((\w+(?:\.\w+)*)[^)]*\)", r"FadeIn(\1)", code)
    code = re.sub(r"\bSpinOut\s*\((\w+(?:\.\w+)*)[^)]*\)", r"FadeOut(\1)", code)
    # SpiralIn / FlyIn / ZoomIn are also common LLM inventions
    code = re.sub(r"\bSpiralIn\s*\((\w+(?:\.\w+)*)[^)]*\)", r"GrowFromCenter(\1)", code)
    code = re.sub(r"\bFlyIn\s*\((\w+(?:\.\w+)*)[^)]*\)", r"FadeIn(\1)", code)
    code = re.sub(r"\bZoomIn\s*\((\w+(?:\.\w+)*)[^)]*\)", r"GrowFromCenter(\1)", code)
    code = re.sub(r"\bZoomOut\s*\((\w+(?:\.\w+)*)[^)]*\)", r"ShrinkToCenter(\1)", code)

    # 14c. Checkmark / Crossmark: non-existent Manim classes.
    #      Keep all kwargs (color=, font_size=) intact after replacement.
    code = re.sub(r"\bCheckmark\s*\(", 'Text("✓", ', code)
    code = re.sub(r"\bCrossmark\s*\(", 'Text("✗", ', code)

    # 14d-pre. Replace calls to undefined helper self.make_star(...) → Star() mobject.
    #           make_star is listed in the prompt but never provided as a class method,
    #           so the LLM sometimes calls it without defining it.
    code = re.sub(
        r"\bself\.make_star\s*\([^)]*\)",
        "Star(n=6, outer_radius=0.4, inner_radius=0.16, color=YELLOW, fill_color=YELLOW, fill_opacity=1)",
        code,
    )

    # 14d. Fake direction constants → valid Manim equivalents.
    code = re.sub(r"\bLEFT_SIDE\b", "LEFT * 7", code)
    code = re.sub(r"\bRIGHT_SIDE\b", "RIGHT * 7", code)
    # CENTER is not a Manim constant (use ORIGIN); TOP is not defined (use UP * 3.8).
    # Only replace when used as an identifier (not inside a string literal — handled
    # by the fact that these are all-caps identifiers rarely used in text content).
    code = re.sub(r"\bCENTER\b(?!\s*=)", "ORIGIN", code)
    code = re.sub(r"\bTOP\b(?!\s*=)", "UP * 3.8", code)

    # 14. Remove Mobject.set(...) calls that try to assign custom Python attributes.
    #     e.g.  person.set(head=head, arms=arms)  — Mobject.set() only accepts
    #     valid Manim style kwargs, not arbitrary Python attributes.
    #     Safe to remove the whole statement; it was only used to store refs.
    code = re.sub(
        r"^[ \t]*\w+\.set\s*\([^)]*\)\s*\n",
        "",
        code,
        flags=re.MULTILINE,
    )

    # 15. Remove .animate.undo() — no such animation exists in Manim.
    code = re.sub(r"\.animate\.undo\s*\(\s*\)", "", code)

    # 16. Replace SVGMobject("anything") with a safe fallback Circle.
    #     LLMs sometimes request SVG assets that don't exist on disk.
    code = re.sub(
        r'\bSVGMobject\s*\(\s*["\'][^"\']*["\']\s*\)',
        "Circle(radius=0.3, color=WHITE, fill_color=WHITE, fill_opacity=1)",
        code,
    )

    # 17. If self.camera.frame is used, Scene must be MovingCameraScene.
    #     Silently upgrade the base class so the code runs.
    if "self.camera.frame" in code:
        code = re.sub(
            r"\bclass\s+MathAnimationScene\s*\(\s*Scene\s*\)",
            "class MathAnimationScene(MovingCameraScene)",
            code,
        )

    # 18. Fix invalid / non-existent Manim color names LLMs commonly invent.
    _bad_colors = {
        r"\bDARK_BLUE\b":   "BLUE_E",
        r"\bDARK_GREEN\b":  "GREEN_E",
        r"\bDARK_RED\b":    "MAROON_A",
        r"\bLIGHT_GRAY\b":  "GRAY_A",
        r"\bLIGHT_GREY\b":  "GRAY_A",
        r"\bDARK_GRAY\b":   "GRAY_D",
        r"\bDARK_GREY\b":   "GRAY_D",
        r"\bMAROON_E\b":    "MAROON",
        r"\bBROWN\b":       "GOLD_D",
        r"\bINDIGO\b":      "PURPLE",
        r"\bCYAN\b":        "TEAL_A",
    }
    for bad_pat, good in _bad_colors.items():
        code = re.sub(bad_pat, good, code)

    # 19. Remove .set_anim_args(...) — not valid on an AnimationBuilder (.animate).
    #     The rate_func / run_time should be passed directly to self.play().
    code = re.sub(r"\.set_anim_args\s*\([^)]*\)", "", code)

    # 20. Fix numpy-array direction constants used as boolean (causes ValueError).
    #     e.g.  if side == UL:  →  if True:  (since LLMs pass UL/DR as string args now,
    #     this most commonly happens in user-defined make_bubble helper code).
    #     Replace function default  side=UL  with  side="left"  and
    #                              side=DR / side=UR  with  side="right"
    #     so the function signature is safe even if the LLM keeps using it.
    code = re.sub(r"\bdef\s+make_bubble\s*\(([^)]*)\bside\s*=\s*UL\b([^)]*)\)",
                  lambda m: f"def make_bubble({m.group(1)}side='left'{m.group(2)})", code)
    code = re.sub(r"\bdef\s+make_bubble\s*\(([^)]*)\bside\s*=\s*(?:DR|UR|DL)\b([^)]*)\)",
                  lambda m: f"def make_bubble({m.group(1)}side='right'{m.group(2)})", code)
    # Fix callers: side=UL/DL → side="left", side=DR/UR → side="right"
    code = re.sub(r"\bside\s*=\s*(?:UL|DL)\b", 'side="left"', code)
    code = re.sub(r"\bside\s*=\s*(?:DR|UR)\b", 'side="right"', code)
    # Fix the conditional inside make_bubble bodies that compare a numpy array
    code = re.sub(r'\bif\s+side\s*(?:is|==)\s*UL\b', 'if side == "left"', code)
    code = re.sub(r'\belse\s+side\s*(?:is|==)\s*DR\b', 'else', code)

    # 21. Fix removed/renamed Manim CE fade animations.
    #     Manim 0.18+ dropped directional FadeIn/FadeOut variants.
    _fade_renames = {
        r"\bFadeOutToDown\b":   "FadeOut",
        r"\bFadeOutToUp\b":     "FadeOut",
        r"\bFadeInFromDown\b":  "FadeIn",
        r"\bFadeInFromUp\b":    "FadeIn",
        r"\bFadeInFromLeft\b":  "FadeIn",
        r"\bFadeInFromRight\b": "FadeIn",
        r"\bShowCreation\b":    "Create",   # old Manim 2.x name
        r"\bUncreate\b":        "Uncreate", # keep — still valid
        r"\bGrowArrow\b":       "Create",   # removed in newer versions
        r"\bShowPassingFlash\b": "ShowPassingFlash",  # still valid
        r"\bCircleIndicate\b":  "Indicate", # not in CE
        r"\bFocusOn\b":         "Indicate", # not in CE
    }
    for bad_pat, good in _fade_renames.items():
        code = re.sub(bad_pat, good, code)

    # 22. Fix VGroup([a, b, c]) — LLMs often pass a list instead of unpacked args.
    #     VGroup expects *args, not a list.
    code = re.sub(
        r"\bVGroup\(\s*\[([^\]]+)\]\s*\)",
        lambda m: f"VGroup({m.group(1)})",
        code,
    )

    # 23. Fix Group([a, b, c]) — same issue as VGroup.
    code = re.sub(
        r"\bGroup\(\s*\[([^\]]+)\]\s*\)",
        lambda m: f"Group({m.group(1)})",
        code,
    )

    # 24. Fix Arrow(start=..., end=...) using keyword-only syntax.
    #     Manim Arrow accepts positional: Arrow(start, end) but keywords work too.
    #     However LLMs sometimes pass direction=(X) for tip direction — remove it.
    code = re.sub(r",?\s*direction\s*=\s*(?:UP|DOWN|LEFT|RIGHT|UL|UR|DL|DR)\b", "", code)

    # 25. Fix .get_center() called without parentheses (LLMs sometimes drop them).
    #     e.g.  obj.get_center  →  obj.get_center()
    #     Only fix when the bare attribute is immediately used as a value
    #     (followed by , ) ] or whitespace/newline).
    code = re.sub(r"\.get_center(?!\s*\()", ".get_center()", code)
    code = re.sub(r"\.get_top(?!\s*\()", ".get_top()", code)
    code = re.sub(r"\.get_bottom(?!\s*\()", ".get_bottom()", code)
    code = re.sub(r"\.get_left(?!\s*\()", ".get_left()", code)
    code = re.sub(r"\.get_right(?!\s*\()", ".get_right()", code)

    # 26. Fix Polygon with fewer than 3 vertices (crashes on creation).
    #     Replace degenerate Polygon(A, B) with Line(A, B).
    def _fix_polygon(m: re.Match) -> str:
        args_str = m.group(1).strip()
        # Count top-level comma-separated args (simplified — no nested parens)
        depth = 0
        count = 1
        for ch in args_str:
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            elif ch == "," and depth == 0:
                count += 1
        if count < 3:
            return f"Line({args_str})"
        return m.group(0)  # leave intact

    code = re.sub(r"\bPolygon\s*\(([^)]+)\)", _fix_polygon, code)

    # 27. Fix self.play() called with None or empty args — crashes Manim.
    #     Remove any play() call where all arguments are just None or empty.
    code = re.sub(r"\bself\.play\(\s*None\s*\)", "self.wait(0.1)", code)
    code = re.sub(r"\bself\.play\(\s*\)", "self.wait(0.1)", code)

    # 28. Fix ImageMobject("path") — image files won't exist in production.
    #     Replace with a colored Rectangle of similar proportions.
    code = re.sub(
        r'\bImageMobject\s*\(\s*["\'][^"\']*["\']\s*\)',
        "Rectangle(width=2, height=1.5, color=BLUE_C, fill_color=BLUE_E, fill_opacity=0.8)",
        code,
    )

    # 29. Strip Unicode subscript characters (U+2080–U+209C) — Manim's default Fira Sans
    #     font does not include these glyphs; missing chars render as colored boxes.
    #     Replace with their plain ASCII digit/letter equivalents.
    _uni_sub_map = {
        "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
        "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
        "ₙ": "n", "ᵢ": "i", "ₓ": "x", "ₐ": "a", "ₑ": "e",
        "ₒ": "o", "ᵤ": "u", "ₜ": "t", "ₖ": "k", "ₘ": "m",
    }
    for uni_ch, plain_ch in _uni_sub_map.items():
        code = code.replace(uni_ch, plain_ch)

    # 30. Strip Unicode superscripts that are NOT in Fira Sans: ⁰ ³ ⁴ ⁵ ⁶ ⁷ ⁸ ⁹ ⁿ ⁻
    #     Keep only ¹ ² ³ which ARE in standard Latin-1 supplement.
    #     Manim's font supports ² (U+00B2) and ³ (U+00B3) reliably; others may render
    #     as boxes. Replace rare superscripts with ^N notation inside Text strings.
    _uni_sup_map = {
        "⁰": "^0", "⁴": "^4", "⁵": "^5", "⁶": "^6",
        "⁷": "^7", "⁸": "^8", "⁹": "^9", "ⁿ": "^n",
        "⁻¹": "^-1", "⁻²": "^-2",
    }
    for uni_ch, plain_ch in _uni_sup_map.items():
        code = code.replace(uni_ch, plain_ch)

    return code


# ---------------------------------------------------------------------------
# Guaranteed fallback animation generator
# ---------------------------------------------------------------------------

def _generate_fallback_code(problem_slug: str, question: str, solution_text: str) -> str:
    """
    Generate a minimal, guaranteed-to-render text-based Manim animation.
    Used automatically when the LLM's creative script fails to render.
    Displays the question and every solution step as animated on-screen text,
    finishing with the final answer boxed in gold.
    Uses ONLY the most basic Manim primitives — nothing that can crash.
    """
    def _safe(s: str, maxlen: int = 72) -> str:
        """Escape text for safe embedding inside a Python double-quoted string."""
        s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").strip()
        s = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", s)   # strip control chars
        return s[:maxlen]

    q_safe = _safe(question, 80) or "Math Problem"

    # Split solution into non-empty lines, cap at 24 to avoid overflow
    raw_lines = [ln.strip() for ln in solution_text.splitlines() if ln.strip()][:24]
    step_lines = [_safe(ln, 72) for ln in raw_lines] or ["Solution not available."]
    answer_line = step_lines[-1]   # last line is treated as the final answer

    # Group steps into pages of 5 lines so they fit vertically on screen
    PAGE = 5
    pages = [step_lines[i : i + PAGE] for i in range(0, len(step_lines), PAGE)]
    # Alternating bullet colors on black (mathematisa-inspired: white body, cyan accent)
    BULLET_COLORS = ["CYAN", "TEAL", "CYAN", "GREEN_C", "TEAL"]

    page_blocks: list[str] = []
    for pg_num, pg_lines in enumerate(pages):
        blk: list[str] = []
        if pg_num > 0:
            blk.append(f"\n        self.wait(0.8)")
            blk.append(f"        self.play(FadeOut(step_grp_{pg_num - 1}), run_time=0.4)")
        y = 1.4
        for i, ln in enumerate(pg_lines):
            bullet_col = BULLET_COLORS[i % len(BULLET_COLORS)]
            vname = f"s{pg_num}_{i}"
            bname = f"b{pg_num}_{i}"
            # Small colored dot bullet + white text side by side
            blk.append(f'\n        {bname} = Dot(radius=0.07, color={bullet_col}, fill_opacity=1).move_to(np.array([-5.8, {y:.2f}, 0]))')
            blk.append(f'\n        {vname} = Text("{ln}", font_size=23, color=WHITE)')
            blk.append(f"        {vname}.move_to(np.array([0.2, {y:.2f}, 0]))")
            blk.append(f"        self.play(FadeIn({bname}), FadeIn({vname}, shift=RIGHT * 0.15), run_time=0.38)")
            y -= 0.65
        grp_vars = ", ".join(
            f"b{pg_num}_{i}, s{pg_num}_{i}" for i in range(len(pg_lines))
        )
        blk.append(f"        step_grp_{pg_num} = VGroup({grp_vars})")
        grp_vars = ", ".join(f"s{pg_num}_{i}" for i in range(len(pg_lines)))
        blk.append(f"        step_grp_{pg_num} = VGroup({grp_vars})")
        page_blocks.append("\n".join(blk))

    last_pg = len(pages) - 1
    fade_last = f"\n        self.wait(0.5)\n        self.play(FadeOut(step_grp_{last_pg}), run_time=0.4)"
    steps_code = "\n".join(page_blocks) + fade_last

    return f"""\
from manim import *
import numpy as np

class MathAnimationScene(Scene):
    def construct(self):
        # Pure black background -- mathematisa dark-elegance style
        bg = Rectangle(width=16, height=9, fill_color=BLACK, fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Gradient title
        title = Text("Step-by-Step Solution", font_size=44)
        title.set_color_by_gradient(CYAN, BLUE_B)
        title.to_edge(UP, buff=0.30)
        self.play(Write(title), run_time=0.9)

        # Question label
        q_label = Text("{q_safe}", font_size=26, color=WHITE)
        q_label.next_to(title, DOWN, buff=0.25)
        self.play(FadeIn(q_label, shift=UP * 0.15), run_time=0.6)

        # Thin cyan separator line
        sep = Line(LEFT * 6.0, RIGHT * 6.0, color=CYAN, stroke_width=1.2)
        sep.next_to(q_label, DOWN, buff=0.20)
        self.play(Create(sep), run_time=0.35)
        self.wait(0.2)
{steps_code}

        # Final answer -- gold box, large gradient text
        ans_text = Text("{answer_line}", font_size=32)
        ans_text.set_color_by_gradient(TEAL, GREEN_C)
        ans_text.to_edge(DOWN, buff=0.65)
        ans_box = RoundedRectangle(
            corner_radius=0.14,
            width=ans_text.width + 0.9,
            height=ans_text.height + 0.45,
            color=GOLD,
            stroke_width=2.2,
        )
        ans_box.move_to(ans_text)
        self.play(Create(ans_box), FadeIn(ans_text), run_time=0.9)
        self.play(Flash(ans_text.get_center(), color=GOLD, flash_radius=0.9, line_length=0.3), run_time=0.6)
        self.wait(5.0)
"""


def _extract_error_context(stderr: str, script_path: str, code: str) -> str:
    """
    Pull the most useful details out of a Manim traceback so the LLM can
    fix the code on retry without re-reading the whole stderr dump.
    Returns a compact, actionable error summary.
    """
    lines = stderr.splitlines()
    # Find the last '> NNN  code line' pattern Manim uses in its rich traceback
    error_line_no = None
    error_src = None
    for ln in reversed(lines):
        m = re.search(r"[>|]\s*(\d+)\s+(.*)", ln)
        if m:
            error_line_no = int(m.group(1))
            error_src = m.group(2).strip()
            break

    # Find the exception type + message — last line that looks like an exception
    exc_line = ""
    for ln in reversed(lines):
        ln_stripped = ln.strip()
        if re.match(r"[A-Z][a-zA-Z]+Error|NameError|TypeError|AttributeError|ValueError", ln_stripped):
            exc_line = ln_stripped
            break

    # Grab ±3 lines of context from the actual saved script
    context_snippet = ""
    if error_line_no:
        try:
            script_lines = Path(script_path).read_text(encoding="utf-8").splitlines()
            lo = max(0, error_line_no - 4)
            hi = min(len(script_lines), error_line_no + 3)
            numbered = [
                (">>> " if i + 1 == error_line_no else "    ") + f"{i+1}: {script_lines[i]}"
                for i in range(lo, hi)
            ]
            context_snippet = "\nCode around the crash:\n" + "\n".join(numbered)
        except Exception:
            pass

    summary = f"ERROR: {exc_line}\n"
    if error_line_no:
        summary += f"Crashed at line {error_line_no}: {error_src}"
    summary += context_snippet
    return summary


def _extract_code_block(text: str) -> str:
    """Extract Python code from a markdown code block if present."""
    pattern = r"```(?:python)?\s*\n([\s\S]+?)\n```"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


def _ensure_scene_class(code: str) -> str:
    """Ensure the Manim script uses MathAnimationScene as the class name."""
    if "class MathAnimationScene" not in code:
        code = re.sub(
            r"class\s+(\w+)\s*\(Scene\)",
            "class MathAnimationScene(Scene)",
            code,
            count=1,
        )
    return code


def _extract_narration(story_text: str) -> str:
    """
    Extract only the NARRATION SCRIPT sentences from a full animation story plan.
    Handles the case where animation_agent passes the entire scene plan — we parse
    out just the sentences that a teacher would speak aloud.
    Returns the input unchanged if no NARRATION SCRIPT section is found.
    """
    match = re.search(
        r'\*{0,2}NARRATION SCRIPT\*{0,2}[^\n]*\n(.*?)(?=\n\*{2}[A-Z]|\Z)',
        story_text, re.IGNORECASE | re.DOTALL
    )
    if not match:
        return story_text

    block = match.group(1).strip()
    sentences = []
    for line in block.split('\n'):
        line = line.strip()
        if not line:
            continue
        # Skip template placeholders like [sentence 1: ...]
        if re.match(r'^\[.*\]$', line):
            continue
        # Remove leading bullet/dash markers
        line = re.sub(r'^[-*•]\s*', '', line).strip()
        if line:
            sentences.append(line)

    result = ' '.join(sentences)
    return result if result and not result.startswith('[') else ''


async def _narrate_async(text: str, mp3_path: Path) -> bool:
    """Generate TTS narration using edge-tts and save to mp3_path."""
    import edge_tts
    communicate = edge_tts.Communicate(text[:audio_cfg.max_chars], audio_cfg.voice)
    await communicate.save(str(mp3_path))
    return mp3_path.exists() and mp3_path.stat().st_size > 0


def _run_tts_in_thread(text: str, mp3_path: Path) -> bool:
    """Run TTS in a fresh event loop. Safe to submit to any ThreadPoolExecutor."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_narrate_async(text, mp3_path))
    except Exception:
        return False
    finally:
        loop.close()


def _probe_video_duration(video: Path, ffmpeg_exe: str) -> float | None:
    """Return video duration in seconds by running ffmpeg -i, or None on failure."""
    try:
        probe = subprocess.run(
            [ffmpeg_exe, "-i", str(video)],
            capture_output=True, text=True, timeout=10,
        )
        m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", probe.stderr + probe.stdout)
        if m:
            h, mn, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
            return h * 3600 + mn * 60 + s
    except Exception:
        pass
    return None


def _merge_audio_video(video: Path, audio: Path, out: Path, ffmpeg_exe: str) -> bool:
    """Merge narration MP3 into video MP4 using ffmpeg. Returns True on success.

    Strategy:
    - Probe both video and audio durations.
    - If audio > video + 0.5s: freeze-extend the last frame using the tpad filter
      so the narration is never cut off mid-sentence. This is the main fix for
      the "animation cuts off before narration finishes" bug.
    - Otherwise: -t video_dur clips output at video length (no freeze needed).
    - -movflags +faststart writes the moov atom at file start for HTML5 players.
    """
    video_dur = _probe_video_duration(video, ffmpeg_exe)
    audio_dur = _probe_video_duration(audio, ffmpeg_exe)  # reuse — ffmpeg reads any media

    if video_dur and audio_dur and audio_dur > video_dur + 0.5:
        # Narration outlasts animation: freeze the last frame for the overflow duration
        extra = audio_dur - video_dur
        cmd = [
            ffmpeg_exe, "-y",
            "-i", str(video),
            "-i", str(audio),
            "-filter_complex",
            f"[0:v]tpad=stop_mode=clone:stop_duration={extra:.3f}[v]",
            "-map", "[v]",
            "-map", "1:a:0",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            str(out),
        ]
    else:
        cmd = [
            ffmpeg_exe, "-y",
            "-i", str(video),
            "-i", str(audio),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            "-map", "0:v:0",
            "-map", "1:a:0",
        ]
        if video_dur is not None:
            cmd += ["-t", str(video_dur)]
        else:
            cmd += ["-shortest"]
        cmd += ["-movflags", "+faststart", str(out)]

    result = subprocess.run(cmd, capture_output=True, timeout=audio_cfg.merge_timeout)
    return result.returncode == 0 and out.exists() and out.stat().st_size > 10_000



def run_manim_animation(
    manim_code: str,
    problem_slug: str = "animation",
    question: str = "",
    solution_text: str = "",
    narration_script: str = "",
) -> dict:
    """
    Save the provided Manim code to a Python file and execute it.
    If rendering fails AND solution_text is provided, an auto-fallback
    text-based animation is rendered instead so the student always
    receives a video.

    Args:
        manim_code:       The complete Python/Manim code as a string.
        problem_slug:     A short slug used to name the output file (no spaces).
        question:         The original math/physics question (used in fallback video).
        solution_text:    The full step-by-step solution text (used in fallback video).
                          ALWAYS provide this so a fallback video can be generated
                          automatically if the creative script fails to render.
        narration_script: Character-voiced story text to narrate over the video.
                          When provided, this is used for TTS instead of solution_text,
                          so the audio sounds like the story characters talking rather
                          than reading dry equations. Pass the animation_story here.

    Returns:
        A dict with keys:
          - status: 'success' or 'error'
          - video_path: path to the produced .mp4 (on success)
          - script_path: path to the saved .py file
          - message: human-readable status message (contains [FALLBACK VIDEO] tag
                     if the guaranteed fallback was used instead of the creative script)
          - stdout / stderr: command output
    """
    # Extract only the narration sentences from the story plan (strips scene/color descriptions)
    _narration_raw = _extract_narration(narration_script.strip()) if narration_script.strip() else ""
    _narration_text = _narration_raw or solution_text
    # 1. Strip markdown fences if present
    clean_code = _extract_code_block(manim_code)

    # 2. Ensure correct class name
    clean_code = _ensure_scene_class(clean_code)

    # 3. Safety: replace MathTex/Tex (requires LaTeX) with Text + Unicode symbols
    clean_code = _sanitize_no_latex(clean_code)

    # 4. Ensure manim import exists
    if "from manim import" not in clean_code and "import manim" not in clean_code:
        clean_code = "from manim import *\n\n" + clean_code

    # 5. Pre-validate Python syntax — catch errors immediately so the LLM can fix
    #    them without waiting for a full 10-minute render attempt to fail.
    import ast as _ast
    try:
        _ast.parse(clean_code)
    except SyntaxError as _se:
        # Save the bad script anyway so the LLM can inspect it
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r"[^\w]", "_", problem_slug)[:40]
        _bad_path = ANIMATIONS_DIR / f"{slug}_{timestamp}_syntax_err.py"
        _bad_path.write_text(clean_code, encoding="utf-8")
        bad_line_text = (clean_code.splitlines()[_se.lineno - 1] if _se.lineno else "")
        return {
            "status": "error",
            "video_path": None,
            "script_path": str(_bad_path),
            "message": (
                f"Python syntax error in generated code — fix before rendering.\n"
                f"Line {_se.lineno}: {_se.msg}\n"
                f"  >>> {bad_line_text.strip()}\n\n"
                "Fix the syntax and call run_manim_animation again with the corrected script."
            ),
            "stdout": "",
            "stderr": f"SyntaxError at line {_se.lineno}: {_se.msg}",
        }

    # ── Save the script ───────────────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r"[^\w]", "_", problem_slug)[:40]
    script_name = f"{slug}_{timestamp}.py"
    script_path = ANIMATIONS_DIR / script_name
    script_path.write_text(clean_code, encoding="utf-8")

    # ── Output directories ────────────────────────────────────────────────────
    # ALL rendered videos are stored under outputs/animations/media/videos/
    # (Manim auto-creates the /videos/<scene>/<quality>/ subfolder hierarchy)
    media_dir = ANIMATIONS_DIR / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    # ── Write manim.cfg into ANIMATIONS_DIR ───────────────────────────────────
    # Use the absolute POSIX path so Manim never falls back to a different location
    # even on Windows paths that contain spaces.
    quality = manim_cfg.quality  # set in config.yaml: l=480p15  m=720p30  h=1080p60  k=4K
    (ANIMATIONS_DIR / "manim.cfg").write_text(
        "[CLI]\n"
        f"media_dir = {media_dir.as_posix()}\n"
        "verbosity = WARNING\n",
        encoding="utf-8",
    )

    # ── Build manim command ───────────────────────────────────────────────────
    cmd = [
        sys.executable, "-m", "manim",
        "render",
        f"-q{quality}",               # high quality: 1080p60 by default
        "--media_dir", str(media_dir),  # explicit CLI override
        str(script_path),
        "MathAnimationScene",
    ]

    # Ensure PYTHONPATH includes the project root so any local imports work
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ANIMATIONS_DIR.parent.parent)

    # ── Ensure ffmpeg is discoverable by Manim ────────────────────────────────
    # Manim calls ffmpeg to combine partial_movie_files into the final mp4.
    # We guarantee at least one of these is on PATH:
    #   1. The venv Scripts dir (we copy ffmpeg.exe there on first run)
    #   2. The imageio_ffmpeg bundled binary directory (fallback)
    venv_scripts = Path(sys.executable).parent        # e.g. .venv/Scripts
    path_parts = env.get("PATH", "").split(os.pathsep)
    if str(venv_scripts) not in path_parts:
        path_parts.insert(0, str(venv_scripts))

    # Also add imageio_ffmpeg binary dir if available and ffmpeg.exe not yet on PATH
    import shutil as _shutil
    if not _shutil.which("ffmpeg", path=os.pathsep.join(path_parts)):
        try:
            import imageio_ffmpeg as _ioff
            _ff_src = Path(_ioff.get_ffmpeg_exe())
            _ff_dst = venv_scripts / "ffmpeg.exe"
            if not _ff_dst.exists() and _ff_src.exists():
                import shutil as _sh
                _sh.copy2(_ff_src, _ff_dst)
            path_parts.insert(0, str(_ff_src.parent))
        except Exception:
            pass

    env["PATH"] = os.pathsep.join(path_parts)
    ffmpeg_exe = _shutil.which("ffmpeg", path=env["PATH"]) or "ffmpeg"

    # ── Start TTS concurrently with the Manim render ──────────────────────────
    # TTS takes ~30-45 s; the Manim render takes ~90 s.  By submitting TTS to a
    # background thread NOW, the audio file is ready before the render finishes,
    # so the merge step is immediate.  Saves ~35-45 s on every animation.
    _tts_pool: concurrent.futures.ThreadPoolExecutor | None = None
    _tts_future: "concurrent.futures.Future[bool] | None" = None
    _mp3_path: Path | None = None

    if audio_cfg.enabled and _narration_text:
        _mp3_path = script_path.with_suffix(".mp3")
        _tts_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="mathviz-tts"
        )
        _tts_future = _tts_pool.submit(_run_tts_in_thread, _narration_text, _mp3_path)

    def _finish_with_audio(raw_video: str) -> str:
        """Wait for the in-flight TTS result and merge into video if available."""
        if not _tts_future or not _mp3_path:
            return raw_video
        try:
            tts_ok = _tts_future.result(timeout=audio_cfg.generation_timeout)
        except Exception:
            tts_ok = False
        if not tts_ok or not _mp3_path.exists():
            return raw_video
        vp = Path(raw_video)
        out = vp.with_name(vp.stem + "_narrated.mp4")
        try:
            if _merge_audio_video(vp, _mp3_path, out, ffmpeg_exe):
                _mp3_path.unlink(missing_ok=True)
                return str(out)
        except Exception:
            pass
        return raw_video

    # Hoisted outside try so it's available in the TimeoutExpired handler too
    def _latest_mp4(search_root: Path, min_mtime: float = 0.0) -> Path | None:
        # Manim creates: <media_dir>/videos/<script_stem>/<quality_folder>/MathAnimationScene.mp4
        # Only accept files created/modified AFTER render_start_time to avoid stale results.
        if not search_root.exists():
            return None
        hits = [
            p for p in search_root.rglob("MathAnimationScene.mp4")
            if p.is_file() and p.stat().st_size > 0
            and p.stat().st_mtime >= min_mtime
        ]
        if not hits:
            return None
        return sorted(hits, key=lambda p: p.stat().st_mtime)[-1]

    try:
        render_start_time = time.time() - 2  # 2-second grace window for filesystem lag
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=manim_cfg.render_timeout,
            cwd=str(ANIMATIONS_DIR),   # manim.cfg is here; default media/ lands here too
            env=env,
        )

        stdout = result.stdout
        stderr = result.stderr

        _quality_labels = {"l": "480p15", "m": "720p30", "h": "1080p60", "p": "1440p60", "k": "2160p60"}
        quality_label = _quality_labels.get(quality, quality)

        # Search only inside the canonical outputs/animations/media directory.
        # Never fall back to the root-level media/ folder — that avoids stale
        # videos from previous runs being reported as the current render.
        video_path_obj = _latest_mp4(media_dir, min_mtime=render_start_time)
        video_path = str(video_path_obj) if video_path_obj else None

        if video_path and Path(video_path).is_file() and Path(video_path).stat().st_size > 0:
            video_path = _finish_with_audio(video_path)
            return {
                "status": "success",
                "video_path": video_path,
                "script_path": str(script_path),
                "message": (
                    f"Animation rendered successfully at {quality_label}!\n"
                    f"VIDEO SAVED AT: {video_path}\n"
                    f"Script saved at: {script_path}"
                ),
                "stdout": stdout[-2000:] if len(stdout) > 2000 else stdout,
                "stderr": stderr[-500:] if len(stderr) > 500 else stderr,
            }

        if result.returncode != 0:
            error_summary = _extract_error_context(stderr, str(script_path), clean_code)

            # ── GUARANTEED FALLBACK VIDEO ─────────────────────────────────────────
            # If solution_text was supplied, auto-render a safe text-only animation
            # so the student ALWAYS gets a video, no matter what the LLM code does.
            if solution_text.strip():
                _fb_code = _generate_fallback_code(problem_slug, question, solution_text)
                _fb_code = _sanitize_no_latex(_fb_code)
                _fb_path = ANIMATIONS_DIR / f"{slug}_{timestamp}_textonly.py"
                _fb_path.write_text(_fb_code, encoding="utf-8")
                try:
                    _fb_proc = subprocess.run(
                        [
                            sys.executable, "-m", "manim", "render", "-ql",
                            # Fallback is text-only: low quality renders in ~15s
                            # vs 5-8 min at 1080p — no need to re-punish the user
                            "--media_dir", str(media_dir),
                            str(_fb_path), "MathAnimationScene",
                        ],
                        capture_output=True, text=True,
                        timeout=manim_cfg.fallback_render_timeout,
                        cwd=str(ANIMATIONS_DIR),
                        env=env,
                    )
                    _fb_video = _latest_mp4(media_dir, min_mtime=render_start_time)
                    if _fb_video and _fb_video.is_file() and _fb_video.stat().st_size > 0:
                        _fb_video_path = _finish_with_audio(str(_fb_video))
                        return {
                            "status": "success",
                            "video_path": _fb_video_path,
                            "script_path": str(_fb_path),
                            "message": (
                                f"[FALLBACK VIDEO] The creative animation script had an error, "
                                f"but a clean text-based solution video was auto-generated.\n"
                                f"VIDEO SAVED AT: {_fb_video}\n"
                                f"Script saved at: {_fb_path}\n\n"
                                f"The student can watch their full solution right now.\n"
                                f"Optional: fix the original error and retry for the creative version:\n"
                                f"{error_summary[:400]}"
                            ),
                            "stdout": (_fb_proc.stdout or "")[-1000:],
                            "stderr": "",
                        }
                except Exception:
                    pass   # fallback itself failed — return the original error below
            # ─────────────────────────────────────────────────────────────────────

            return {
                "status": "error",
                "video_path": None,
                "script_path": str(script_path),
                "message": (
                    f"Manim render failed.\n\n"
                    f"{error_summary}\n\n"
                    "INSTRUCTIONS FOR RETRY:\n"
                    "1. Read the ERROR line and the code snippet above carefully.\n"
                    "2. Fix ONLY the broken lines — do not rewrite unrelated parts.\n"
                    "3. Common causes:\n"
                    "   - Calling a method that doesn't exist on Text/Mobject (use simple transforms instead)\n"
                    "   - Using RIGHT/UP/LEFT/DOWN.copy().rotate() — use np.array([np.cos(a),np.sin(a),0]) instead\n"
                    "   - Undefined rate_func name — only use: linear, smooth, there_and_back, ease_out_bounce, rush_into, rush_from\n"
                    "   - VGroup(*self.mobjects) — use Group(*self.mobjects)\n"
                    "   - MathTex/Tex — use Text() with Unicode\n"
                    "4. Call run_manim_animation again with corrected code AND solution_text."
                ),
                "stdout": stdout[-2000:] if len(stdout) > 2000 else stdout,
                "stderr": stderr[-3000:] if len(stderr) > 3000 else stderr,
            }

        # Render completed with returncode=0 but no video found — try fallback too
        if solution_text.strip():
            _fb_code2 = _generate_fallback_code(problem_slug, question, solution_text)
            _fb_code2 = _sanitize_no_latex(_fb_code2)
            _fb_path2 = ANIMATIONS_DIR / f"{slug}_{timestamp}_textonly.py"
            _fb_path2.write_text(_fb_code2, encoding="utf-8")
            try:
                subprocess.run(
                    [
                        sys.executable, "-m", "manim", "render", "-ql",
                        "--media_dir", str(media_dir),
                        str(_fb_path2), "MathAnimationScene",
                    ],
                    capture_output=True, text=True,
                    timeout=90,
                    cwd=str(ANIMATIONS_DIR),
                    env=env,
                )
                _fb_video2 = _latest_mp4(media_dir, min_mtime=render_start_time)
                if _fb_video2 and _fb_video2.is_file() and _fb_video2.stat().st_size > 0:
                    _fb_video2_path = _finish_with_audio(str(_fb_video2))
                    return {
                        "status": "success",
                        "video_path": _fb_video2_path,
                        "script_path": str(_fb_path2),
                        "message": (
                            f"[FALLBACK VIDEO] Creative script produced no output — "
                            f"a text-based solution video was auto-generated.\n"
                            f"VIDEO SAVED AT: {_fb_video2}\n"
                        ),
                        "stdout": "",
                        "stderr": "",
                    }
            except Exception:
                pass

        return {
            "status": "error",
            "video_path": None,
            "script_path": str(script_path),
            "message": (
                f"Render completed (returncode={result.returncode}) but no valid video file was found.\n"
                f"Searched in: {media_dir / 'videos'} (recursively).\n"
                "This usually means Manim ran but wrote no output — check stderr for warnings.\n"
                "INSTRUCTIONS FOR RETRY:\n"
                "1. Inspect stderr for any Manim warnings about the scene not rendering.\n"
                "2. Ensure the class is named MathAnimationScene and the construct() method is not empty.\n"
                "3. Always pass solution_text= so the auto-fallback can trigger.\n"
                "4. Fix the script and call run_manim_animation again."
            ),
            "stdout": stdout[-2000:] if len(stdout) > 2000 else stdout,
            "stderr": stderr[-1000:] if len(stderr) > 1000 else stderr,
        }

    except subprocess.TimeoutExpired:
        # Render timed out — immediately try guaranteed text-only fallback so the
        # animation_agent does NOT retry (which would waste another ~150s + 60s LLM).
        if solution_text.strip():
            _fb_code_t = _generate_fallback_code(problem_slug, question, solution_text)
            _fb_code_t = _sanitize_no_latex(_fb_code_t)
            _fb_path_t = ANIMATIONS_DIR / f"{slug}_{timestamp}_textonly.py"
            _fb_path_t.write_text(_fb_code_t, encoding="utf-8")
            try:
                subprocess.run(
                    [
                        sys.executable, "-m", "manim", "render", "-ql",
                        "--media_dir", str(media_dir),
                        str(_fb_path_t), "MathAnimationScene",
                    ],
                    capture_output=True, text=True,
                    timeout=manim_cfg.fallback_render_timeout,
                    cwd=str(ANIMATIONS_DIR),
                    env=env,
                )
                _fb_video_t = _latest_mp4(media_dir, min_mtime=render_start_time)
                if _fb_video_t and _fb_video_t.is_file() and _fb_video_t.stat().st_size > 0:
                    _fb_video_t_path = _finish_with_audio(str(_fb_video_t))
                    return {
                        "status": "success",
                        "video_path": _fb_video_t_path,
                        "script_path": str(_fb_path_t),
                        "message": (
                            f"[FALLBACK VIDEO] Creative render timed out after "
                            f"{manim_cfg.render_timeout}s ({quality} quality). "
                            f"A clean text-based solution video was auto-generated.\n"
                            f"VIDEO SAVED AT: {_fb_video_t}\n"
                            f"The student can watch the full step-by-step solution now.\n"
                            f"Do NOT retry — the student already has a complete video."
                        ),
                        "stdout": "",
                        "stderr": "",
                    }
            except Exception:
                pass
        return {
            "status": "error",
            "video_path": None,
            "script_path": str(script_path),
            "message": (
                f"Animation rendering timed out after {manim_cfg.render_timeout}s "
                f"(quality={quality}). Set MANIM_QUALITY=l for faster renders."
            ),
            "stdout": "",
            "stderr": "TimeoutExpired",
        }
    except Exception as exc:
        return {
            "status": "error",
            "video_path": None,
            "script_path": str(script_path),
            "message": f"Unexpected error: {exc}",
            "stdout": "",
            "stderr": str(exc),
        }
    finally:
        if _tts_pool is not None:
            _tts_pool.shutdown(wait=False)



def list_animations() -> list[dict]:
    """
    List all previously generated animation scripts and videos.

    Returns:
        A list of dicts with filename, script_path, created_at.
    """
    files = sorted(ANIMATIONS_DIR.glob("*.py"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [
        {
            "filename": f.name,
            "script_path": str(f),
            "created_at": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        }
        for f in files
    ]
