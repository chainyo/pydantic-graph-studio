from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from importlib import resources
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic_graph import Graph
from pydantic_graph.nodes import BaseNode

from pydantic_graph_studio.introspection import serialize_graph
from pydantic_graph_studio.runtime import iter_run_events
from pydantic_graph_studio.schemas import Event


@dataclass(slots=True)
class RunState:
    run_id: str
    queue: asyncio.Queue[Event]
    done: asyncio.Event
    task: asyncio.Task[None]


class RunRegistry:
    def __init__(self) -> None:
        """Initialize the run registry."""
        self._runs: dict[str, RunState] = {}
        self._lock = asyncio.Lock()

    async def start_run(
        self,
        graph: Graph[Any, Any, Any],
        start_node: BaseNode[Any, Any, Any],
        *,
        state: Any = None,
        deps: Any = None,
        persistence: Any = None,
    ) -> str:
        """Start a graph run and return the run id."""
        run_id = uuid4().hex
        queue: asyncio.Queue[Event] = asyncio.Queue()
        done = asyncio.Event()

        async def producer() -> None:
            try:
                async for event in iter_run_events(
                    graph,
                    start_node,
                    state=state,
                    deps=deps,
                    persistence=persistence,
                    run_id=run_id,
                ):
                    await queue.put(event)
            finally:
                done.set()

        task = asyncio.create_task(producer())
        async with self._lock:
            self._runs[run_id] = RunState(run_id=run_id, queue=queue, done=done, task=task)
        return run_id

    async def get(self, run_id: str) -> RunState | None:
        """Fetch the run state for a run id."""
        async with self._lock:
            return self._runs.get(run_id)

    async def remove(self, run_id: str) -> None:
        """Remove a run state from the registry."""
        async with self._lock:
            self._runs.pop(run_id, None)

    async def shutdown(self) -> None:
        """Cancel any in-flight runs and clear the registry."""
        async with self._lock:
            runs = list(self._runs.values())
            self._runs.clear()
        for run in runs:
            if not run.task.done():
                run.task.cancel()


def create_app(
    graph: Graph[Any, Any, Any],
    start_node: BaseNode[Any, Any, Any],
    *,
    state: Any = None,
    deps: Any = None,
    persistence: Any = None,
) -> FastAPI:
    """Create the FastAPI app bound to a graph and start node."""
    ui_root = resources.files("pydantic_graph_studio.ui")
    index_html = (ui_root / "index.html").read_text(encoding="utf-8")
    assets_dir = ui_root / "assets"

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Initialize and tear down shared server state."""
        registry = RunRegistry()
        app.state.graph = graph
        app.state.start_node = start_node
        app.state.state = state
        app.state.deps = deps
        app.state.persistence = persistence
        app.state.registry = registry
        try:
            yield
        finally:
            await registry.shutdown()

    app = FastAPI(lifespan=lifespan)

    @app.get("/api/graph")
    async def get_graph() -> JSONResponse:
        """Return the serialized graph model."""
        payload = serialize_graph(app.state.graph)
        return JSONResponse(payload)

    @app.post("/api/run")
    async def start_run() -> dict[str, str]:
        """Start a new run and return its identifier."""
        run_id = await app.state.registry.start_run(
            app.state.graph,
            app.state.start_node,
            state=app.state.state,
            deps=app.state.deps,
            persistence=app.state.persistence,
        )
        return {"run_id": run_id}

    @app.get("/api/events")
    async def stream_events(run_id: str) -> StreamingResponse:
        """Stream events for a run as Server-Sent Events."""
        run_state = await app.state.registry.get(run_id)
        if run_state is None:
            raise HTTPException(status_code=404, detail="Unknown run_id")

        async def event_stream() -> AsyncIterator[bytes]:
            """Yield SSE-formatted event payloads."""
            try:
                while True:
                    if run_state.done.is_set() and run_state.queue.empty():
                        break
                    event = await run_state.queue.get()
                    payload = json.dumps(event.model_dump(mode="json"))
                    yield f"data: {payload}\n\n".encode()
            finally:
                await app.state.registry.remove(run_id)

        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
        return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)

    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/")
    async def studio_index() -> HTMLResponse:
        """Serve the bundled studio UI."""
        return HTMLResponse(index_html)

    return app
