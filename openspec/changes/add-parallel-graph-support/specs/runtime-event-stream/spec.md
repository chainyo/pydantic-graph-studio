## MODIFIED Requirements
### Requirement: Ordered Run Event Stream
The system SHALL emit a strictly ordered sequence of events for each graph run, including `node_start`, `node_end`, `edge_taken`, `run_end`, and `error`, and this sequence SHALL reflect the real-time interleaving of parallel branches when present.

#### Scenario: Normal run completes
- **WHEN** a graph run completes without error
- **THEN** the stream includes node_start/edge_taken/node_end events followed by run_end

#### Scenario: Parallel branches interleave
- **WHEN** a graph run executes parallel branches
- **THEN** the stream preserves a single total order reflecting the interleaved execution of those branches

#### Scenario: Run error
- **WHEN** a node raises an exception
- **THEN** the stream includes an error event and terminates the run
