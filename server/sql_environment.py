"""
SQL Query Craft Environment Server.

Implements the OpenEnv Environment interface for text-to-SQL tasks.
The agent receives a natural language question and database schema,
then submits SQL queries. Reward is based on query correctness with
rich partial-credit signals.
"""

from __future__ import annotations

import os
import uuid
from typing import Any, Optional

from openenv.core.env_server.interfaces import Environment

from .database import SCHEMA_DESCRIPTION, create_database, execute_query, format_query_result
from .graders import grade_query
from .tasks import TaskDefinition, get_task, list_tasks

try:
    from models import SQLAction, SQLObservation, SQLState
except ImportError:
    from sql_query_craft.models import SQLAction, SQLObservation, SQLState


class SQLQueryCraftEnvironment(Environment):
    """
    Text-to-SQL environment where an AI agent writes SQL queries
    to answer business analytics questions.

    Supports multiple tasks (easy → hard) with deterministic grading.
    """

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self) -> None:
        super().__init__()
        self._db = create_database()
        self._task: Optional[TaskDefinition] = None
        self._state = SQLState(episode_id=str(uuid.uuid4()), step_count=0)
        self._default_task = os.getenv("SQL_QUERY_CRAFT_TASK", "easy_employee_lookup")

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs: Any,
    ) -> SQLObservation:
        task_name = kwargs.get("task_name", self._default_task)
        self._task = get_task(task_name)

        self._db.close()
        self._db = create_database()

        self._state = SQLState(
            episode_id=episode_id or str(uuid.uuid4()),
            step_count=0,
            task_name=task_name,
            best_reward=0.0,
            last_query="",
            queries_attempted=0,
        )

        return SQLObservation(
            done=False,
            reward=0.0,
            question=self._task.question,
            schema_description=SCHEMA_DESCRIPTION,
            query_result="",
            query_error="",
            expected_columns=self._task.expected_columns,
            hints=self._task.hints,
            task_name=self._task.name,
            difficulty=self._task.difficulty,
            step_number=0,
            max_steps=self._task.max_steps,
            reward_breakdown={},
            metadata={
                "available_tasks": list_tasks(),
                "sql_features_needed": self._task.sql_features,
            },
        )

    def step(
        self,
        action: Any,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> SQLObservation:
        if self._task is None:
            return SQLObservation(
                done=True,
                reward=0.0,
                query_error="Environment not initialized. Call reset() first.",
                metadata={},
            )

        if not isinstance(action, SQLAction):
            if isinstance(action, dict):
                action = SQLAction(**action)
            else:
                raise ValueError(f"Expected SQLAction, got {type(action)}")

        self._state.step_count += 1
        self._state.queries_attempted += 1
        self._state.last_query = action.query

        columns, rows, error = execute_query(self._db, action.query)
        result_str = format_query_result(columns, rows, error)

        if error:
            reward = 0.0
            breakdown = {"error": error}
        else:
            reward, breakdown = grade_query(self._db, self._task, action.query)

        self._state.best_reward = max(self._state.best_reward, reward)

        done = (
            reward >= 0.95
            or self._state.step_count >= self._task.max_steps
        )

        return SQLObservation(
            done=done,
            reward=reward,
            question=self._task.question,
            schema_description=SCHEMA_DESCRIPTION,
            query_result=result_str,
            query_error=error or "",
            expected_columns=self._task.expected_columns,
            hints=self._task.hints if self._state.step_count <= 2 else "",
            task_name=self._task.name,
            difficulty=self._task.difficulty,
            step_number=self._state.step_count,
            max_steps=self._task.max_steps,
            reward_breakdown=breakdown,
            metadata={
                "best_reward_so_far": self._state.best_reward,
                "queries_attempted": self._state.queries_attempted,
            },
        )

    @property
    def state(self) -> SQLState:
        return self._state

    def close(self) -> None:
        try:
            self._db.close()
        except Exception:
            pass
