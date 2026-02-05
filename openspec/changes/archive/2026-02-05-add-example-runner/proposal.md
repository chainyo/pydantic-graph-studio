# Change: Add CLI Example Runner and README Usage

## Why
New users need a fast path to try Pydantic Graph Studio without cloning the repo. A built-in example runner plus clearer README usage lets `uvx` users launch a demo in seconds.

## What Changes
- Add a CLI `example` command to list and run built-in examples.
- Package example graphs inside the Python package so `uvx pydantic-graph-studio` can load them.
- Add auto-port selection (default port, then next) and auto-open the browser.
- Expand README usage and example instructions.

## Impact
- Affected specs: `specs/cli-launcher/spec.md`
- Affected code: `src/pydantic_graph_studio/cli.py`, new example modules under `src/pydantic_graph_studio/examples/`, README updates.
