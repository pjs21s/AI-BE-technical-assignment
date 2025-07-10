# backend/Dockerfile
FROM python:3.13-slim

RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Poetry 사용
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

COPY backend ./backend

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
