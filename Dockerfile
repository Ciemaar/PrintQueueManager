FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY ./src /app/src/

RUN pip install --upgrade pip
RUN pip install .

RUN useradd -m appuser \
    && mkdir -p /watched_folder \
    && chown -R appuser:appuser /app \
    && chown -R appuser:appuser /watched_folder

USER appuser

CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
