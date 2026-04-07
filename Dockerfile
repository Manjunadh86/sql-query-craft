FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY uv.lock ./
COPY models.py ./
COPY client.py ./
COPY __init__.py ./
COPY openenv.yaml ./
COPY server/ ./server/

RUN pip install --no-cache-dir "openenv-core[core]>=0.2.2" && \
    pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app:$PYTHONPATH"

EXPOSE 7069

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7069/health || exit 1

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7069"]
