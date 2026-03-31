#!/bin/bash
# Helper script to run docker builds for different python versions and OS

PYTHON_VERSIONS=("3.11" "3.12" "3.13" "3.14")
OS_TYPES=("-slim" "-slim-bookworm" "-slim-trixie")

#PYTHON_VERSIONS=("3.14")
#OS_TYPES=("-slim")

# Exit on any failure
set -e

# Change directory to project root
cd "$(dirname "$0")/../.."

COMPOSE_FILE=tests/docker/docker-compose.yml

echo "Testing build for different versions..."

docker compose -f ${COMPOSE_FILE}  up -d db

for PY_VER in "${PYTHON_VERSIONS[@]}"; do
  for OS_TYPE in "${OS_TYPES[@]}"; do
    IMAGE="python:${PY_VER}${OS_TYPE}"
    TAG="django-mariadb-vector:test-py${PY_VER}${OS_TYPE}"
    export TAG
    echo "--- Building and testing with $IMAGE ---"
    docker compose -f ${COMPOSE_FILE}  build \
        --build-arg PYTHON_VERSION=$PY_VER \
        --build-arg OS_IMAGE=$IMAGE \
        test
    
    echo "--- Running tests for $TAG ---"
    docker compose -f ${COMPOSE_FILE} run --rm test
  done
done

docker compose -f ${COMPOSE_FILE}  down -v


echo "All tests finished!"
