# cli-launcher Specification

## Purpose
TBD - created by archiving change add-v1-mvp-spec. Update Purpose after archive.
## Requirements
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
The CLI SHALL allow configuring host and port for the local server and auto-select the next port when the default port is unavailable.

#### Scenario: Custom port
- **WHEN** the user supplies a port option
- **THEN** the server binds to that port

#### Scenario: Default port unavailable
- **WHEN** the default port is already in use and no explicit port is provided
- **THEN** the CLI retries on the next port and starts the server

### Requirement: Example Subcommand
The CLI SHALL provide an `example` subcommand to list and run built-in example graphs.

#### Scenario: List examples
- **WHEN** the user runs `pgraph example list`
- **THEN** the CLI prints available example names with a short description

#### Scenario: Run example by name
- **WHEN** the user runs `pgraph example <name>`
- **THEN** the CLI loads the matching built-in example graph and starts the studio

### Requirement: Auto Open Browser
The CLI SHALL open the default browser to the studio URL after startup unless disabled.

#### Scenario: Auto-open browser
- **WHEN** the studio starts without a `--no-open` flag
- **THEN** the default browser is opened to the studio URL

#### Scenario: Disable auto-open
- **WHEN** the user provides `--no-open`
- **THEN** the CLI does not open the browser

