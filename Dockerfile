FROM --platform=linux/amd64 python:3

WORKDIR /app

COPY pyproject.toml uv.lock models.py client.py __init__.py openenv.yaml ./
COPY server/ ./server/

RUN pip install --no-cache-dir "openenv-core[core]>=0.2.2" && \
    pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app:$PYTHONPATH"

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
