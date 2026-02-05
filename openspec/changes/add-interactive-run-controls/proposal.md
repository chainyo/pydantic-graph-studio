# Change: Add Interactive Run Controls

## Why
The built-in examples look too similar in the UI because the runtime only visualizes node/edge traversal. This prevents tool calls and human approvals from materializing, which makes the "tool usage" and "human-in-the-loop" examples feel fake.

## What Changes
- Add runtime events for tool call activity and human input requests/responses.
- Add a server endpoint to accept interactive responses for in-flight runs.
- Add UI surfaces to display tool call activity and require user approval when prompted.
- Update example graphs to emit tool-call events and block on human approval until a response is received.

## Impact
- Affected specs: runtime-event-stream, local-studio-server, studio-ui-layout
- Affected code: `src/pydantic_graph_studio/runtime.py`, `src/pydantic_graph_studio/schemas.py`, `src/pydantic_graph_studio/server.py`, `src/pydantic_graph_studio/ui/assets/app.js`, `examples/tool_usage.py`, `examples/human_in_the_loop.py`, `src/pydantic_graph_studio/examples/*.py`
