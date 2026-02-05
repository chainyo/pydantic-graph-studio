## MODIFIED Requirements
### Requirement: Ordered Run Event Stream
The system SHALL emit a strictly ordered sequence of events for each graph run, including `node_start`, `node_end`, `edge_taken`, `run_end`, `error`, and optional interactive events (`tool_call`, `tool_result`, `input_request`, `input_response`).

#### Scenario: Tool activity during a run
- **WHEN** a node emits tool call activity
- **THEN** the `tool_call` and `tool_result` events appear in the stream in the order they occurred

## ADDED Requirements
### Requirement: Interactive Event Payloads
The system SHALL include structured payloads for interactive events that allow the UI to correlate calls and responses by identifier.

#### Scenario: Input request payload
- **WHEN** a node requests human approval
- **THEN** the event includes `request_id`, `prompt`, and `options` fields
