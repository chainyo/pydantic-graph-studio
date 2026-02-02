# Change: Add parallel graph support (beta fork/join)

## Why
Users need to visualize and execute graphs with true parallel branches (e.g., concurrent fetch nodes) without collapsing them into a single aggregated node.

## What Changes
- Add support for `pydantic_graph.beta.Graph` in graph introspection and runtime execution.
- Emit runtime events for parallel branches in a single ordered event stream.
- Allow the local studio server to serve graph models and runs for both stable and beta graph types.

## Impact
- Affected specs: graph-introspection, runtime-event-stream, local-studio-server
- Affected code: `src/pydantic_graph_studio/introspection.py`, `src/pydantic_graph_studio/runtime.py`, `src/pydantic_graph_studio/server.py`, `src/pydantic_graph_studio/cli.py`
