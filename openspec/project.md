# Project Context

## Purpose

This project is a **local-first visualization and execution studio for `pydantic_graph` workflows**.

Its goals are to:
- Visually inspect **PydanticAI / pydantic_graph** graphs without relying on Mermaid diagrams.
- Run graphs locally and **observe execution live** (node traversal, edges taken, state changes).
- Provide a **clean, modern UI** suitable for debugging, teaching, and screen recording (videos, demos, social content).
- Remain **fully offline, stateless, and developer-only**.

This is a **Python developer tool**, not:
- a SaaS product
- a workflow editor
- a low-code platform
- an automation or scheduling system

Non-goals include visual editing, persistence, authentication, and cloud hosting.

---

## Tech Stack

### Backend
- Python **≥ 3.12**
- `pydantic_graph`
- FastAPI or Starlette (local HTTP server)
- Server-Sent Events (SSE) for runtime execution streaming
- `uv` / `uvx` for local execution and tooling
- Standard library only for runtime state (no database)

### Frontend (bundled, prebuilt)
- React
- Vite (build-time only)
- Tailwind CSS
- shadcn/ui
- React Flow (graph rendering and layout)

> The frontend is built once and shipped as static assets inside the Python wheel.  
> End users do **not** need Node.js installed.

---

## Project Conventions

### Code Style

#### Python
- Explicit over clever
- Minimal metaprogramming
- Composition over inheritance
- Full type annotations on public APIs
- Async-safe code paths (even when executed synchronously)

Formatting and linting:
- `ruff` for linting
- `black`-compatible formatting
- `snake_case` for functions and variables
- `PascalCase` for classes
- `SCREAMING_SNAKE_CASE` for constants

#### Frontend
- Functional React components only
- No global state frameworks
- Tailwind utility-first styling
- Minimal animations (used only for execution highlighting)

---

### Architecture Patterns

#### High-level architecture

```
Python Package
├─ CLI (pgraph)
├─ Graph Introspection
├─ Runtime Instrumentation
├─ Local HTTP Server (FastAPI)
│   ├─ /api/graph
│   ├─ /api/run
│   ├─ /api/events   (SSE)
│   └─ /             (static UI)
└─ Bundled Frontend Assets
```

#### Key architectural decisions

- **Static graph introspection**
  - Graph structure is inferred from:
    - Node classes passed to `Graph(nodes=[...])`
    - `run()` return type annotations
    - Runtime return values for dynamic edge resolution

- **Event-driven runtime visualization**
  - Execution emits a linear stream of events:
    - `node_start`
    - `node_end`
    - `edge_taken`
    - `run_end`
    - `error`
    - optional `state_patch`

- **Automatic instrumentation**
  - Node `run()` methods are wrapped at runtime
  - No changes required to user code
  - No dependency on private `pydantic_graph` internals

- **No persistence layer**
  - All runs are in-memory
  - Optional JSONL recording to disk
  - Replay is file-based only

- **Read-only frontend**
  - Visualizes structure and execution
  - Never mutates graphs or source code

---

### Testing Strategy

- **Unit tests**
  - Graph introspection (nodes, edges)
  - CLI parsing (`module:var`, `file.py:var`)
  - Runtime instrumentation and event ordering

- **Integration tests**
  - Execute minimal graphs and assert emitted event streams
  - Validate server startup and static UI serving

- **Frontend testing**
  - Manual QA initially
  - Backend event correctness is the primary source of truth

Testing principle:
> If the event stream is correct, the UI will be correct.

---

### Git Workflow

- `main` branch is always releasable
- Short-lived feature branches
- Squash merges preferred

Commit message format:

```
feat: add runtime event streaming
fix: correct edge inference for End nodes
docs: clarify uv run usage
```

---

## Domain Context

Key concepts required to work on this project:

- **pydantic_graph**
  - Graphs are composed of node classes
  - Control flow is driven by returning node instances
  - `End[T]` terminates execution
  - Graphs may be synchronous or asynchronous

- **Agentic workflows**
  - Explicit control flow and state transitions
  - Visualization focuses on decision paths, not just topology

- **Developer tooling**
  - Similar mental model to TensorBoard, Dagster Dev, or MLflow UI
  - Optimized for engineers, not non-technical users

---

## Important Constraints

- Must run entirely locally
- Must not require Node.js at runtime
- Must not modify user graph source files
- Must avoid reliance on private or unstable `pydantic_graph` internals
- Must remain useful across future `pydantic_graph` versions

Scope discipline:
> Any feature requiring authentication, databases, or cloud services is out of scope.

---

## External Dependencies

- `pydantic_graph` (core dependency)
- React Flow (frontend graph rendering)
- `uv` / `uvx` (recommended execution tooling)

No external APIs.  
No telemetry.  
No network dependencies beyond localhost.
