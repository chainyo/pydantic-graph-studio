# Change: Add Dagre-based layout for the studio UI

## Why
Current manual layouting produces crossings and overlapping long edges for parallel branches, which makes the default view hard to read without manual tweaks.

## What Changes
- Add Dagre as the layout engine for the React Flow graph.
- Replace the in-app heuristic layout with Dagre top-to-bottom positioning.
- Keep deterministic layout for identical graph inputs.

## Impact
- Affected specs: `studio-ui-layout` (new)
- Affected code: `src/pydantic_graph_studio/ui/assets/app.js`, frontend build pipeline, bundled static assets.
