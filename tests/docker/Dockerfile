# Use a build argument for Python version
ARG PYTHON_VERSION=3.12
ARG OS_IMAGE=python:${PYTHON_VERSION}-slim

# Stage 1: Build the package
FROM ${OS_IMAGE} AS builder
RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Create a source distribution and wheel

RUN --mount=type=cache,target=/root/.cache/uv \
    uv build --link-mode=copy

# Stage 2: Test the package
FROM ${OS_IMAGE} AS tester

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y && apt-get install -y \
    default-libmysqlclient-dev \
    default-mysql-client \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/dist/*.whl /app/dist/
COPY tests/ ./tests/
COPY tests/runtests_d.py .

RUN --mount=type=cache,target=/root/.cache/uv \
    pip install --no-cache-dir uv \
    && uv pip install --link-mode=copy --system /app/dist/*.whl "django-mariadb-vector[test,orjson]" \
    && uv pip install --link-mode=copy --system mysqlclient

CMD ["python", "runtests_d.py"]
