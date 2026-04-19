FROM python:3.12-slim

WORKDIR /app

# System deps kept minimal — chromadb's sqlite-vss wheel bundles what it needs.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e . \
  && pip install --no-cache-dir uvicorn[standard]

COPY app ./app

# Default command is overridden per-service in docker-compose.yml
CMD ["python", "-m", "app.bot"]
