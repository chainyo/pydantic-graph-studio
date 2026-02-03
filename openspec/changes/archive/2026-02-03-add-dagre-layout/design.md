## Context
The studio UI currently uses a custom heuristic to place nodes vertically. Parallel branches and long edges often overlap or cross, hurting readability. React Flow recommends external layout engines for proper graph layout.

## Goals / Non-Goals
- Goals:
  - Produce a clean top-to-bottom DAG layout for flow graphs.
  - Reduce edge crossings for fork/join branches.
  - Keep layout deterministic across reloads.
- Non-Goals:
  - Interactive node dragging or manual layout persistence.
  - Advanced edge routing beyond Dagre’s built-in layout.

## Decisions
- **Use Dagre for layout**: Dagre provides deterministic DAG layout suitable for top-to-bottom flows.
- **Fixed node dimensions**: Use static node width/height for layout calculation to avoid measuring DOM at runtime.
- **Single layout pass per graph load**: Compute layout once when loading `/api/graph`.

## Risks / Trade-offs
- Adds a new JS dependency to the bundled frontend.
- Fixed node sizing may under/overestimate spacing for long labels.
- Very large graphs may incur noticeable layout time.

## Migration Plan
- Add Dagre dependency to the frontend build.
- Replace heuristic layout with Dagre-based positions in `buildFlowGraph`.
- Rebuild bundled assets for distribution.

## Open Questions
- Should we allow switching layout direction (TB/LR) via a UI toggle?
