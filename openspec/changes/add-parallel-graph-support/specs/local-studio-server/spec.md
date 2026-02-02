## MODIFIED Requirements
### Requirement: Graph Endpoint
The server SHALL expose `GET /api/graph` returning the current graph model as JSON for both stable `pydantic_graph.Graph` and beta `pydantic_graph.beta.Graph` instances.

#### Scenario: Graph request
- **WHEN** a client requests `/api/graph`
- **THEN** the response includes nodes and edges for the loaded graph

#### Scenario: Beta graph request
- **WHEN** the loaded graph is a beta graph with parallel branches
- **THEN** the response includes nodes and edges for each parallel branch

### Requirement: Run Endpoint
The server SHALL expose `POST /api/run` to start a graph execution and return a `run_id`, supporting both stable and beta graph types.

#### Scenario: Run started
- **WHEN** a client posts to `/api/run`
- **THEN** a new run_id is returned and execution begins

#### Scenario: Beta graph run
- **WHEN** the loaded graph is a beta graph with parallel branches
- **THEN** the run starts and emits events for concurrent node execution
