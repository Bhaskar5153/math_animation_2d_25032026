"""
ADK entry point for `adk web` and `adk run` commands.
This file is discovered automatically by the ADK CLI.
"""
from agents.orchestrator_agent import root_agent

__all__ = ["root_agent"]
