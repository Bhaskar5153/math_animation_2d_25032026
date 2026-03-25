"""
Animation runner tool — saves Manim code and executes it to produce a video.
"""
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent
ANIMATIONS_DIR = _BASE_DIR / "outputs" / "animations"
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
    # subscripts
    ("_{0}", "₀"), ("_{1}", "₁"), ("_{2}", "₂"), ("_{3}", "₃"), ("_{4}", "₄"),
    ("_{n}", "ₙ"), ("_{i}", "ᵢ"), ("_{x}", "ₓ"),
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


def _sanitize_no_latex(code: str) -> str:
    """
    Safety net: replace MathTex/Tex class names with Text and remove
    kwargs that only exist on MathTex.  Does NOT touch string contents
    (to avoid accidentally corrupting code or comments).

    The primary defence is the animation prompt instructing the LLM to
    use Text + Unicode symbols from the start.  This function is a
    last-resort guard for stray MathTex uses.
    """
    # 1. Replace MathTex( → Text( (full word match)
    code = re.sub(r"\bMathTex\s*\(", "Text(", code)

    # 2. Replace standalone Tex( → Text(  (avoid touching Vertex, Complex…)
    code = re.sub(r"(?<![A-Za-z])Tex\s*\(", "Text(", code)

    # 3. Remove MathTex-only keyword arguments (won't exist on Text)
    for kwarg in ("substrings_to_isolate", "tex_environment", "tex_template",
                  "arg_separator"):
        code = re.sub(r",?\s*" + kwarg + r"\s*=\s*(?:[^,)\n]+)", "", code)

    # 4. Remove MathTex-only methods chained onto any expression
    code = re.sub(r"\.get_part_by_(?:tex|substring)\([^)]*\)", "", code)

    # 5. Replace VGroup(*self.mobjects) → Group(*self.mobjects)
    #    VGroup only accepts VMobject; self.mobjects may contain plain Mobjects
    code = re.sub(r"\bVGroup\(\s*\*\s*self\.mobjects\s*\)", "Group(*self.mobjects)", code)

    return code




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


def run_manim_animation(manim_code: str, problem_slug: str = "animation") -> dict:
    """
    Save the provided Manim code to a Python file and execute it.

    Args:
        manim_code:   The complete Python/Manim code as a string.
        problem_slug: A short slug used to name the output file (no spaces).

    Returns:
        A dict with keys:
          - status: 'success' or 'error'
          - video_path: path to the produced .mp4 (on success)
          - script_path: path to the saved .py file
          - message: human-readable status message
          - stdout / stderr: command output
    """
    # 1. Strip markdown fences if present
    clean_code = _extract_code_block(manim_code)

    # 2. Ensure correct class name
    clean_code = _ensure_scene_class(clean_code)

    # 3. Safety: replace MathTex/Tex (requires LaTeX) with Text + Unicode symbols
    clean_code = _sanitize_no_latex(clean_code)

    # 4. Ensure manim import exists
    if "from manim import" not in clean_code and "import manim" not in clean_code:
        clean_code = "from manim import *\n\n" + clean_code

    # Save the script
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r"[^\w]", "_", problem_slug)[:40]
    script_name = f"{slug}_{timestamp}.py"
    script_path = ANIMATIONS_DIR / script_name
    script_path.write_text(clean_code, encoding="utf-8")

    # Output media sub-dir that Manim will create
    media_dir = ANIMATIONS_DIR / "media"

    # Run manim from the PROJECT ROOT so Python imports resolve
    project_root = str(_BASE_DIR)

    # -ql = low quality (faster render); use absolute paths
    cmd = [
        sys.executable, "-m", "manim",
        "render",
        "-ql",
        "--media_dir", str(media_dir),
        str(script_path),
        "MathAnimationScene",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=project_root,   # run from project root, not animations dir
        )

        stdout = result.stdout
        stderr = result.stderr

        if result.returncode == 0:
            video_search = list(media_dir.rglob("MathAnimationScene.mp4"))
            if video_search:
                video_path = str(sorted(video_search, key=lambda p: p.stat().st_mtime)[-1])
            else:
                video_path = "Video rendered — check outputs/animations/media/"

            return {
                "status": "success",
                "video_path": video_path,
                "script_path": str(script_path),
                "message": "Animation rendered successfully!",
                "stdout": stdout[-3000:] if len(stdout) > 3000 else stdout,
                "stderr": stderr[-1000:] if len(stderr) > 1000 else stderr,
            }
        else:
            return {
                "status": "error",
                "video_path": None,
                "script_path": str(script_path),
                "message": f"Manim render failed with exit code {result.returncode}",
                "stdout": stdout[-3000:] if len(stdout) > 3000 else stdout,
                "stderr": stderr[-3000:] if len(stderr) > 3000 else stderr,
            }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "video_path": None,
            "script_path": str(script_path),
            "message": "Animation rendering timed out after 5 minutes.",
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
