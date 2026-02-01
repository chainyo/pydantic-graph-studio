# Change: Add V1 MVP specification

## Why
The project needs a first, concrete MVP spec to guide implementation of the local-first graph studio and align scope with the goals in `openspec/project.md`.

## What Changes
- Define MVP capabilities for the CLI launcher, local server, graph introspection, and runtime event streaming
- Add requirements and scenarios for each capability
- Provide an implementation checklist for the initial build

## Impact
- Affected specs: `cli-launcher`, `local-studio-server`, `graph-introspection`, `runtime-event-stream`
- Affected code: CLI entrypoint, server routes, runtime instrumentation, UI asset bundling, tests
