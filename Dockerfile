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
COPY seeds/ ./seeds/
# the text shared by pages and emails (AD-12): the booking terms and the reception sentence of the confirmation email
COPY content/ ./content/
RUN uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH" \
    BP_ROOT=/app \
    BP_HOST=0.0.0.0 \
    BP_PORT=8000

EXPOSE 8000
CMD ["booking-platform", "serve"]
