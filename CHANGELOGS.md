# CHANGELOGS

## [0.2.0] - 2026-03-30

### Added
- Docker-based test coverage across multiple Python versions and platforms using a real MariaDB container with migrations.
  - Script: `tests/docker/run_docker_tests.sh`
- Optional performance improvement for vector handling using `orjson` and the `binary_response` option.
- Test coverage for the new options.
- Docker test coverage with real stored data via `FillDataTest`.
- `VectorModelBinary` model for Docker test scenarios.

### Notes
- See [performance comparison](assets/images/perf_v0.2.0_sm.png) for the vector serialization benchmark.