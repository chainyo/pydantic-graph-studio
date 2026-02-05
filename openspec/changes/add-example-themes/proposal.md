# Change: Add Example Themes and Rename Parallel Example

## Why
Users need a broader set of self-contained example graphs to explore common patterns like error handling, tools, streaming events, and human-in-the-loop flows. A richer catalog also improves the `pgraph example` quickstart experience.

## What Changes
- Add a new example library specification that enumerates required example themes.
- Add new built-in examples for error handling, tool usage, streaming events, and human-in-the-loop flows.
- Rename the existing AI Concierge example to a more generic parallel/joins name.

## Impact
- Affected specs: `specs/example-library/spec.md`
- Affected code: `src/pydantic_graph_studio/examples/*`, `src/pydantic_graph_studio/cli.py`, README updates.
