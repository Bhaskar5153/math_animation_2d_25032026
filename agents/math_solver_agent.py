"""
Math Solver Agent -- a single, powerful LlmAgent that:
  1. Detects the math domain from the question
  2. Solves the problem step-by-step with full working
  3. Returns a structured solution with DOMAIN label

No sub-agent routing -- single agent handles all domains for reliability.
"""
from google.adk.agents import LlmAgent

from config import models
from prompts.math_prompts import MATH_SOLVER_INSTRUCTION

math_solver_agent = LlmAgent(
    name="math_solver_agent",
    model=models.primary,
    description=(
        "Expert math solver. Identifies the domain (algebra, geometry, calculus, "
        "statistics, trigonometry, arithmetic, number theory) and produces a full "
        "step-by-step solution with domain label, all steps shown, and final answer."
    ),
    instruction=MATH_SOLVER_INSTRUCTION,
    # Store the full solution in session state so downstream agents read it
    # via the {math_solution} placeholder -- no orchestrator LLM needed.
    output_key="math_solution",
)
