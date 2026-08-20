# Reproducible from a clean environment, which is what the case asks for.
#
# Two stages: dependencies are resolved once from the lockfile and cached, then
# the source is copied on top. Editing code does not re-resolve dependencies.

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Dependencies first, as their own layer: they change far less often than code.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

COPY src/ ./src/
COPY configs/ ./configs/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev


FROM python:3.12-slim-bookworm AS runtime

# Not root. The pipeline only ever writes to /app/dados and /app/saida.
RUN useradd --create-home --uid 1000 ranking
WORKDIR /app

COPY --from=builder --chown=ranking:ranking /app/.venv /app/.venv
COPY --from=builder --chown=ranking:ranking /app/src /app/src
COPY --from=builder --chown=ranking:ranking /app/configs /app/configs

RUN mkdir -p /app/dados /app/saida && chown -R ranking:ranking /app/dados /app/saida

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER ranking

# Mount a volume on /app/saida to collect ranking.json and ranking.md:
#   docker run --rm -v "$PWD/saida:/app/saida" ranking --reference-date 2025-12-31
ENTRYPOINT ["ranking"]
CMD ["--help"]
