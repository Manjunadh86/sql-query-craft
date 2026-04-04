"""
SQL Query Craft EnvClient.

WebSocket-based client for persistent sessions with the SQL environment.
"""

from __future__ import annotations

from openenv.core.client_types import StepResult
from openenv.core.env_client import EnvClient

try:
    from .models import SQLAction, SQLObservation, SQLState
except ImportError:
    from models import SQLAction, SQLObservation, SQLState


class SQLQueryCraftEnv(EnvClient[SQLAction, SQLObservation, SQLState]):

    def _step_payload(self, action: SQLAction) -> dict:
        return {"query": action.query}

    def _parse_result(self, payload: dict) -> StepResult[SQLObservation]:
        obs_data = payload.get("observation", {})
        obs = SQLObservation(**obs_data)
        return StepResult(
            observation=obs,
            reward=payload.get("reward"),
            done=bool(payload.get("done", False)),
        )

    def _parse_state(self, payload: dict) -> SQLState:
        return SQLState(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
            task_name=payload.get("task_name", ""),
            best_reward=payload.get("best_reward", 0.0),
            last_query=payload.get("last_query", ""),
            queries_attempted=payload.get("queries_attempted", 0),
        )
