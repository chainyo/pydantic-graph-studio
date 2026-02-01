## ADDED Requirements
### Requirement: Ordered Run Event Stream
The system SHALL emit a strictly ordered sequence of events for each graph run, including `node_start`, `node_end`, `edge_taken`, `run_end`, and `error`.

#### Scenario: Normal run completes
- **WHEN** a graph run completes without error
- **THEN** the stream includes node_start/edge_taken/node_end events followed by run_end

#### Scenario: Run error
- **WHEN** a node raises an exception
- **THEN** the stream includes an error event and terminates the run

### Requirement: Run Correlation and Payloads
Each event SHALL include a `run_id`, `event_type`, and the relevant node or edge identifiers.

#### Scenario: Node start event payload
- **WHEN** a node begins execution
- **THEN** the event payload includes the node_id and run_id

### Requirement: Sync and Async Instrumentation
The system SHALL instrument both synchronous and asynchronous node `run()` methods without requiring changes to user code.

#### Scenario: Async node execution
- **WHEN** a graph includes async nodes
- **THEN** events are emitted around their execution in the correct order
