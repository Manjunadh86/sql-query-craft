"""
Typed Pydantic models for the SQL Query Craft environment.

Defines the Action, Observation, and State types used across
the server, client, and inference script.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field

from openenv.core.env_server.types import Action, Observation, State


class SQLAction(Action):
    """Agent submits a SQL query to execute against the database."""

    query: str = Field(..., description="The SQL query to execute")


class SQLObservation(Observation):
    """Observation returned after each step or reset."""

    question: str = Field(default="", description="Natural language question to answer with SQL")
    schema_description: str = Field(default="", description="Database schema in human-readable format")
    query_result: str = Field(default="", description="Formatted result of the last executed query")
    query_error: str = Field(default="", description="Error message if the last query failed")
    expected_columns: List[str] = Field(default_factory=list, description="Expected column names in the answer")
    hints: str = Field(default="", description="Hints for solving the current task")
    task_name: str = Field(default="", description="Current task identifier")
    difficulty: str = Field(default="", description="Task difficulty: easy, medium, or hard")
    step_number: int = Field(default=0, description="Current step number")
    max_steps: int = Field(default=10, description="Maximum steps allowed for this task")
    reward_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Detailed breakdown of how the reward was computed",
    )


class SQLState(State):
    """Internal environment state."""

    task_name: str = ""
    best_reward: float = 0.0
    last_query: str = ""
    queries_attempted: int = 0
