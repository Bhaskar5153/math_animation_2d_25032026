"""
Orchestrator Agent — the root agent that coordinates the full MathViz pipeline.

Pipeline (runs as sequential tool calls via AgentTool):
  User Question
       │
       ▼
  math_solver_agent      ← identifies domain + solves (AgentTool call)
       │
       ▼
  solution_writer_agent  ← saves solution as markdown (AgentTool call)
       │
       ▼
  story_agent            ← creates animation story (AgentTool call)
       │
       ▼
  animation_agent        ← generates + renders Manim 2D animation (AgentTool call)
       │
       ▼
  Final Response         ← summary, solution path, video path

Key: sub_agents causes a one-way TRANSFER (handoff). 
AgentTool wraps each agent as a TOOL so the orchestrator can call all four 
in sequence and collect every result before responding.
"""
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from agents.math_solver_agent import math_solver_agent
from agents.solution_writer_agent import solution_writer_agent
from agents.story_agent import story_agent
from agents.animation_agent import animation_agent
from prompts.orchestrator_prompts import ORCHESTRATOR_INSTRUCTION

# Wrap each pipeline agent as an AgentTool so the orchestrator LLM can call
# them one-by-one and receive each result before deciding the next step.
math_solver_tool = AgentTool(agent=math_solver_agent)
solution_writer_tool = AgentTool(agent=solution_writer_agent)
story_tool = AgentTool(agent=story_agent)
animation_tool = AgentTool(agent=animation_agent)

root_agent = LlmAgent(
    name="mathviz_orchestrator",
    model="gemini-2.5-pro",
    description=(
        "MathViz — the master orchestrator that transforms any math question into "
        "a step-by-step solution AND a beautiful 2D animation. Coordinates math solving, "
        "solution writing, story creation, and animation rendering in strict sequence."
    ),
    instruction=ORCHESTRATOR_INSTRUCTION,
    tools=[
        math_solver_tool,
        solution_writer_tool,
        story_tool,
        animation_tool,
    ],
)
