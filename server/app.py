"""
FastAPI application for the SQL Query Craft environment.

Exposes the SQLQueryCraftEnvironment over HTTP and WebSocket endpoints
compatible with EnvClient.
"""

try:
    from openenv.core.env_server.http_server import create_app
except ImportError:
    from openenv.core.env_server import create_app

try:
    from models import SQLAction, SQLObservation
except ImportError:
    from sql_query_craft.models import SQLAction, SQLObservation

from .sql_environment import SQLQueryCraftEnvironment

app = create_app(
    SQLQueryCraftEnvironment,
    SQLAction,
    SQLObservation,
    env_name="sql_query_craft",
)


def main() -> None:
    import uvicorn

    port = int(__import__("os").getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
