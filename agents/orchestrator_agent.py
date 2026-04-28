"""
Orchestrator Agent -- LlmAgent router + optimised parallel pipeline.

Structure:
  root_agent  (LlmAgent)
      Greets users and routes math/physics questions to mathviz_pipeline.

      └── mathviz_pipeline  (SequentialAgent)
              ├── math_solver_agent          Stage 1: solve -> session.state["math_solution"]
              └── outer_parallel  (ParallelAgent)
                      ├── story_then_animation  (SequentialAgent)  ← critical path
                      │       ├── story_agent    -> session.state["animation_story"]
                      │       └── animation_agent  starts the MOMENT story_agent finishes
                      └── solution_writer_agent   runs off the critical path, fully overlapped
                                                  with animation_agent's LLM call + render

Why this is faster than the previous layout:
  Old: math_solver → [story ‖ solution_writer] → animation
       animation_agent was blocked until BOTH story and solution_writer finished.

  New: math_solver → [story → animation] ‖ solution_writer
       animation_agent starts the moment story_agent finishes.
       solution_writer's ~15 s is hidden inside animation_agent's ~40 s LLM call.
"""
from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent

from config import models

from agents.math_solver_agent import math_solver_agent
from agents.solution_writer_agent import solution_writer_agent
from agents.story_agent import story_agent
from agents.animation_agent import animation_agent

# Critical path: story produces animation_story, then animation_agent runs immediately
story_then_animation = SequentialAgent(
    name="story_then_animation",
    description="Creates the animation story then immediately renders the animation.",
    sub_agents=[story_agent, animation_agent],
)

# solution_writer runs freely in parallel — completely off the critical path
outer_parallel = ParallelAgent(
    name="outer_parallel",
    description=(
        "Runs the story→animation pipeline and the markdown solution writer concurrently. "
        "animation_agent starts as soon as story_agent finishes, without waiting for "
        "solution_writer_agent."
    ),
    sub_agents=[story_then_animation, solution_writer_agent],
)

# Full pipeline
mathviz_pipeline = SequentialAgent(
    name="mathviz_pipeline",
    description=(
        "Full MathViz pipeline: solves a math or physics question step-by-step, "
        "saves a markdown solution, creates an animation story, and renders a 2D "
        "Manim animation video. Use this for ANY math or physics question."
    ),
    sub_agents=[math_solver_agent, outer_parallel],
)

# Root agent: routes greetings vs math questions
root_agent = LlmAgent(
    name="mathviz_orchestrator",
    model=models.primary,
    description="MathViz assistant. Greets users and routes math/physics questions to the animation pipeline.",
    instruction="""\
You are MathViz, a friendly math and physics animation assistant.

For greetings, small talk, or questions about what you can do:
  Respond warmly and directly. Tell the user you can solve and animate any
  math or physics problem — algebra, calculus, geometry, trigonometry,
  statistics, kinematics, forces, energy, and more.

For any math or physics question (equations, proofs, word problems, calculations):
  Transfer immediately to mathviz_pipeline. Do not solve it yourself.
""",
    sub_agents=[mathviz_pipeline],
)
