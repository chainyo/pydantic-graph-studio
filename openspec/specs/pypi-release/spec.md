# pypi-release Specification

## Purpose
TBD - created by archiving change add-pypi-release. Update Purpose after archive.
## Requirements
### Requirement: Release Workflow Trigger
The system SHALL publish to PyPI when a GitHub Release is published and the tag matches the format `vX.Y.Z`.

#### Scenario: GitHub Release published with v0.1.0 tag
- **WHEN** a GitHub Release is published with tag `v0.1.0`
- **THEN** the release workflow begins publishing to PyPI

### Requirement: Tag Version Consistency
The system SHALL require the GitHub Release tag version to match the version defined in `pyproject.toml`.

#### Scenario: Tag matches pyproject version
- **WHEN** the GitHub Release tag is `v0.1.0` and `pyproject.toml` version is `0.1.0`
- **THEN** the release workflow proceeds to build and publish artifacts

#### Scenario: Tag does not match pyproject version
- **WHEN** the GitHub Release tag is `v0.1.0` and `pyproject.toml` version is `0.2.0`
- **THEN** the release workflow fails before publishing

### Requirement: PyPI Publishing
The system SHALL build source and wheel distributions and publish them to PyPI.

#### Scenario: Publish artifacts
- **WHEN** the release workflow runs after passing version checks
- **THEN** it builds sdist and wheel artifacts and uploads them to PyPI

