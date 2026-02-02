## ADDED Requirements
### Requirement: Beta Graph Model Extraction
The system SHALL produce a graph model from a `pydantic_graph.beta.Graph` instance that includes nodes, edges, entry node(s), and terminal node(s), including fork/join structure when present.

#### Scenario: Parallel branches in beta graph
- **WHEN** a beta graph includes a fork that fans out to multiple nodes and joins downstream
- **THEN** the model includes edges for each parallel branch and the join relationship
