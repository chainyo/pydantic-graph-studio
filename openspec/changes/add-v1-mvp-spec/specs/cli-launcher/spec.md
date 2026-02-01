## ADDED Requirements
### Requirement: CLI Entry Point
The system SHALL provide a `pgraph` CLI that launches the local studio for a graph locator.

#### Scenario: Module locator
- **WHEN** the user runs `pgraph <module:var>`
- **THEN** the graph is loaded and the server starts

#### Scenario: File locator
- **WHEN** the user runs `pgraph <path.py:var>`
- **THEN** the graph is loaded and the server starts

### Requirement: Locator Validation
The CLI SHALL validate the locator and exit with a non-zero status on errors.

#### Scenario: Missing graph variable
- **WHEN** the locator does not resolve to a Graph instance
- **THEN** the CLI prints an error and exits non-zero

### Requirement: Host and Port Options
The CLI SHALL allow configuring host and port for the local server.

#### Scenario: Custom port
- **WHEN** the user supplies a port option
- **THEN** the server binds to that port
