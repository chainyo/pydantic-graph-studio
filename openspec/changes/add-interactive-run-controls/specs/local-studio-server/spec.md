## ADDED Requirements
### Requirement: Input Response Endpoint
The server SHALL expose a `POST /api/input` endpoint to deliver interactive responses to in-flight runs.

#### Scenario: Human approval submitted
- **WHEN** the UI submits a response with a valid `run_id` and `request_id`
- **THEN** the server accepts the response and the run resumes execution
