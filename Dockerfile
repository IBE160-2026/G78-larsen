# The backend image (AD-22). It copies named paths only, never the whole build context (AD-17), and runs the
# backend from the image's virtual environment: no `uv run` at runtime, one uvicorn process, no --workers.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.24 /uv /usr/local/bin/uv

ENV UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies first, so a code change does not reinstall them.
COPY pyproject.toml uv.lock README.md .python-version ./
RUN uv sync --locked --no-dev --no-install-project

COPY src/ ./src/
COPY migrations/ ./migrations/
COPY config/ ./config/
# seeds/ and content/ are copied when present (Story 1.3 adds them). The bracket glob matches nothing until then,
# so the COPY of the always-present pyproject.toml keeps the instruction valid.
COPY pyproject.toml se[e]ds/ ./seeds/
COPY pyproject.toml conten[t]/ ./content/
RUN rm -f ./seeds/pyproject.toml ./content/pyproject.toml && uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH" \
    BP_ROOT=/app \
    BP_HOST=0.0.0.0 \
    BP_PORT=8000

EXPOSE 8000
CMD ["booking-platform", "serve"]
