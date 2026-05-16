"""
Animation Agent instruction — assembled from per-domain prompt modules.
Each domain's code helpers live in prompts/domains/*.py for easy maintenance.
"""
from prompts.domains.shared_rules import SHARED_RULES
from prompts.domains.shared_style import VISUAL_STYLE
from prompts.domains.math_calculus import CALCULUS_HELPERS
from prompts.domains.math_algebra import ALGEBRA_HELPERS
from prompts.domains.math_trigonometry import TRIGONOMETRY_HELPERS
from prompts.domains.math_series import SERIES_HELPERS
from prompts.domains.math_statistics import STATISTICS_HELPERS
from prompts.domains.math_quadratics import QUADRATICS_HELPERS
from prompts.domains.math_geometry import GEOMETRY_HELPERS
from prompts.domains.physics_kinematics import PHYSICS_KINEMATICS_HELPERS
from prompts.domains.physics_forces import PHYSICS_FORCES_HELPERS
from prompts.domains.shared_ui import SHARED_UI_HELPERS
from prompts.domains.shared_characters import CHARACTER_LIBRARY
from prompts.domains.shared_character_selection import CHARACTER_SELECTION
from prompts.domains.shared_layout import LAYOUT_RULES

_STEP2_HEADER = """\
==============================================================================
STEP 2 -- CODE HELPERS (domain-specific patterns)
==============================================================================
"""

ANIMATION_AGENT_INSTRUCTION = (
    SHARED_RULES + "\n\n"
    + VISUAL_STYLE + "\n\n"
    + _STEP2_HEADER
    + CALCULUS_HELPERS + "\n\n"
    + ALGEBRA_HELPERS + "\n\n"
    + TRIGONOMETRY_HELPERS + "\n\n"
    + SERIES_HELPERS + "\n\n"
    + STATISTICS_HELPERS + "\n\n"
    + QUADRATICS_HELPERS + "\n\n"
    + PHYSICS_KINEMATICS_HELPERS + "\n\n"
    + PHYSICS_FORCES_HELPERS + "\n\n"
    + GEOMETRY_HELPERS + "\n\n"
    + SHARED_UI_HELPERS + "\n\n"
    + CHARACTER_LIBRARY + "\n\n"
    + CHARACTER_SELECTION + "\n\n"
    + LAYOUT_RULES
)
