# graph-introspection Specification

## Purpose
TBD - created by archiving change add-v1-mvp-spec. Update Purpose after archive.
## Requirements
### Requirement: Graph Model Extraction
The system SHALL produce a graph model from a `pydantic_graph.Graph` instance that includes nodes, edges, entry node(s), and terminal node(s).

#### Scenario: Static graph extraction
- **WHEN** a graph instance is provided with a fixed set of node classes
- **THEN** the model includes every node and edge present in the graph

### Requirement: Deterministic Node Identity
The system SHALL assign a deterministic `node_id` for each node based on its class identity within the graph.

#### Scenario: Stable IDs across runs
- **WHEN** the same graph instance is introspected multiple times
- **THEN** each node receives the same `node_id` value

### Requirement: Edge Inference from Return Types
The system SHALL infer possible edges from `run()` return type annotations when available, and mark edges as dynamic when targets cannot be determined statically.

#### Scenario: Annotated return types
- **WHEN** a node `run()` method returns a union of node types
- **THEN** the model lists edges to each union target

#### Scenario: Unannotated return types
- **WHEN** a node `run()` method lacks a resolvable return type
- **THEN** the model includes a dynamic edge with no fixed target

