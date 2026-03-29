FROM python:3.13-slim

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
COPY alembic.ini ./
COPY ./alembic /app/alembic/

RUN pip install --upgrade pip
RUN pip install .

CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
