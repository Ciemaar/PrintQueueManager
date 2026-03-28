FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the dependency files first to leverage Docker layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies before installing the project
RUN uv sync --frozen --no-install-project --no-dev

# Now copy the source code and install the project itself
COPY ./src /app/src/
RUN uv sync --frozen --no-dev

# Use uv to run the application natively in the container
CMD ["uv", "run", "uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
