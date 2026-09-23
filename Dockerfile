FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder
WORKDIR /app
COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project
COPY src ./src
COPY configs ./configs
COPY README.md ./
RUN uv sync --no-dev

FROM python:3.11-slim-bookworm AS runtime
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/configs /app/configs
EXPOSE 8000
CMD ["uvicorn", "ekyc.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
