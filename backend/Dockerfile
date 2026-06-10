# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

WORKDIR /build
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

FROM python:3.11-slim AS runtime

RUN groupadd --gid 1000 app && useradd --uid 1000 --gid app --create-home app

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

ENV APP_ENV=deployed \
    API_HOST=0.0.0.0 \
    API_PORT=8000

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
