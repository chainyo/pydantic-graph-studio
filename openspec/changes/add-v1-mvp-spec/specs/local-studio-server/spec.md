## ADDED Requirements
### Requirement: Local HTTP Server
The system SHALL run a local HTTP server bound to localhost and serve the studio UI and API.

#### Scenario: Server starts
- **WHEN** the CLI launches the studio
- **THEN** the server listens on the configured host and port

### Requirement: Graph Endpoint
The server SHALL expose `GET /api/graph` returning the current graph model as JSON.

#### Scenario: Graph request
- **WHEN** a client requests `/api/graph`
- **THEN** the response includes nodes and edges for the loaded graph

### Requirement: Run Endpoint
The server SHALL expose `POST /api/run` to start a graph execution and return a `run_id`.

#### Scenario: Run started
- **WHEN** a client posts to `/api/run`
- **THEN** a new run_id is returned and execution begins

### Requirement: Event Stream Endpoint
The server SHALL expose `GET /api/events?run_id=...` as a Server-Sent Events stream for the specified run.

#### Scenario: Event stream connected
- **WHEN** a client connects with a valid run_id
- **THEN** the server streams ordered events until the run ends

### Requirement: Bundled Static UI
The server SHALL serve bundled static UI assets at `/` without requiring Node.js at runtime.

#### Scenario: UI load
- **WHEN** a browser loads the root path
- **THEN** the studio UI is returned as static files
