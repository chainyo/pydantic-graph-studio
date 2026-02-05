# Pydantic Graph Studio

A lightweight studio/CLI scaffold for `pydantic-graph` projects.

## Quickstart with uvx

Run built-in examples without cloning the repo:

```bash
uvx pydantic-graph-studio example list
uvx pydantic-graph-studio example graph
uvx pydantic-graph-studio example parallel-joins
```

Built-in example themes:
- `graph` (branching and loops)
- `parallel-joins` (parallel/fork-join)
- `error-handling` (explicit error path and recovery)
- `tool-usage` (tool invocation and result handling)
- `streaming-events` (event-rich run)
- `human-in-the-loop` (simulated user input step)

The studio opens in your browser automatically. It binds to port 8000 by default and retries 8001 if 8000 is already in use and you did not set `--port`.

Common flags:
- `--no-open` to disable browser auto-open
- `--host` to change the bind host
- `--port` to choose a specific port

## Run your own graph

Use the CLI with a module or file reference:

```bash
pgraph module:graph
pgraph path/to/file.py:graph
```

You can also run with uvx directly:

```bash
uvx pydantic-graph-studio module:graph
uvx pydantic-graph-studio path/to/file.py:graph
```

If the graph has multiple entry nodes, pass `--start` with the node id.

## Examples in this repo

The repository examples are in `examples/`:

```bash
pgraph examples/graph.py:graph
pgraph examples/parallel_joins.py:graph
pgraph examples/error_handling.py:graph
pgraph examples/tool_usage.py:graph
pgraph examples/streaming_events.py:graph
pgraph examples/human_in_the_loop.py:graph
```

## Release

Releases are published automatically to PyPI via GitHub Actions using Trusted Publishing (OIDC).

Release rules:
- Tag format MUST be `vX.Y.Z` (e.g., `v0.1.0`)
- Tag version MUST match `version` in `pyproject.toml`
- Publish happens when a GitHub Release is published

Process:
1. Update `version` in `pyproject.toml`
2. Create a git tag `vX.Y.Z`
3. Publish a GitHub Release from that tag

Notes:
- The PyPI project must be configured for Trusted Publishing with this GitHub repository.
