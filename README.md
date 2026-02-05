# Pydantic Graph Studio

A lightweight studio/CLI scaffold for `pydantic-graph` projects.

## Release

Releases are published automatically to PyPI via GitHub Actions using Trusted Publishing (OIDC).

Release rules:
- Tag format MUST be `vX.Y.Z` (e.g., `v0.1.0`)
- Tag version MUST match `version` in `pyproject.toml`
- Publish happens when a GitHub Release is published

Process:
1. Update `version` in `pyproject.toml`
2. Create a git tag `vX.Y.Z`
3. Publish a GitHub Release from that tag

Notes:
- The PyPI project must be configured for Trusted Publishing with this GitHub repository.
