# studio-ui-layout Specification

## Purpose
TBD - created by archiving change add-dagre-layout. Update Purpose after archive.
## Requirements
### Requirement: Dagre-based Layout
The studio UI SHALL lay out graph nodes using Dagre for top-to-bottom (TB) flows.

#### Scenario: Parallel branches
- **WHEN** a graph contains fork/join branches
- **THEN** the layout positions branches in parallel without overlapping nodes

### Requirement: Deterministic Layout
The studio UI SHALL produce deterministic node positions for the same graph input.

#### Scenario: Reloaded graph
- **WHEN** the same graph is loaded multiple times
- **THEN** node positions remain stable

