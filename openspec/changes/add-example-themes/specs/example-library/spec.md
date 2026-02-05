## ADDED Requirements
### Requirement: Example Catalog
The system SHALL provide a built-in example catalog that includes the following example names and themes:
- `graph` (branching and loops)
- `parallel-joins` (parallel/fork-join pattern)
- `error-handling` (explicit error path and recovery)
- `tool-usage` (tool invocation and result handling)
- `streaming-events` (state changes that emit runtime events)
- `human-in-the-loop` (simulated user input step)

#### Scenario: Example list includes required themes
- **WHEN** the user runs `pgraph example list`
- **THEN** the listed examples include each required example name

### Requirement: Example Self-Containment
Each built-in example SHALL be self-contained and runnable without external services, API keys, or network access.

#### Scenario: Run without external dependencies
- **WHEN** the user runs any built-in example
- **THEN** the graph runs locally without requiring external credentials or network access

### Requirement: Parallel Example Rename
The existing AI Concierge example SHALL be renamed to `parallel-joins` to describe the parallel join pattern.

#### Scenario: Renamed example appears in catalog
- **WHEN** the user runs `pgraph example list`
- **THEN** the catalog lists `parallel-joins`
