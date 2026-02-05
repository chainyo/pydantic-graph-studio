## ADDED Requirements
### Requirement: Tool Activity Surface
The studio UI SHALL display tool call activity emitted during a run.

#### Scenario: Tool call occurs
- **WHEN** a `tool_call` event is received
- **THEN** the UI shows the tool call entry alongside its result when available

### Requirement: Human Approval Prompt
The studio UI SHALL block a run on `input_request` events until the user selects a response.

#### Scenario: Approval requested
- **WHEN** an `input_request` event is received
- **THEN** the UI presents the prompt and only resumes after the user responds
