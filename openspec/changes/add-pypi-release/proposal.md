# Change: Add PyPI Release Automation

## Why
Manual releases are error-prone and slow. A GitHub Actions workflow will provide a consistent, auditable, and repeatable path to publish releases to PyPI.

## What Changes
- Add a GitHub Actions release workflow triggered by GitHub Release publication.
- Enforce tag format `vX.Y.Z` and require it to match the version in `pyproject.toml`.
- Build source and wheel distributions and publish to PyPI (no TestPyPI).
- Document the release process in the README.

## Impact
- Affected specs: pypi-release (new)
- Affected code: `.github/workflows/`, `README.md`, packaging metadata
