"""Runtime instrumentation utilities for pydantic_graph execution."""

from __future__ import annotations

import asyncio
import inspect
import types
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from pydantic_graph import Graph
from pydantic_graph.graph import GraphRun, GraphRunResult
from pydantic_graph.nodes import BaseNode, End

HookReturn = Awaitable[None] | None
NodeStartHook = Callable[[GraphRun[Any, Any, Any], BaseNode[Any, Any, Any]], HookReturn]
NodeEndHook = Callable[
    [GraphRun[Any, Any, Any], BaseNode[Any, Any, Any], BaseNode[Any, Any, Any] | End[Any]],
    HookReturn,
]
EdgeTakenHook = Callable[[GraphRun[Any, Any, Any], BaseNode[Any, Any, Any], BaseNode[Any, Any, Any]], HookReturn]
RunEndHook = Callable[[GraphRun[Any, Any, Any], End[Any]], HookReturn]
ErrorHook = Callable[[GraphRun[Any, Any, Any], BaseNode[Any, Any, Any], BaseException], HookReturn]


@dataclass(slots=True)
class RunHooks:
    """Callbacks for runtime instrumentation.

    Callbacks may be synchronous functions or async callables. Async callables are awaited.
    """

    on_node_start: NodeStartHook | None = None
    on_node_end: NodeEndHook | None = None
    on_edge_taken: EdgeTakenHook | None = None
    on_run_end: RunEndHook | None = None
    on_error: ErrorHook | None = None


async def _maybe_await(func: Callable[..., HookReturn] | None, *args: Any) -> None:
    if func is None:
        return
    result = func(*args)
    if inspect.isawaitable(result):
        await result


def instrument_graph_run(graph_run: GraphRun[Any, Any, Any], hooks: RunHooks) -> GraphRun[Any, Any, Any]:
    """Attach runtime hooks to a GraphRun instance."""

    if getattr(graph_run, "_pgraph_instrumented", False):
        setattr(graph_run, "_pgraph_run_hooks", hooks)
        return graph_run

    original_next = graph_run.next
    setattr(graph_run, "_pgraph_instrumented", True)
    setattr(graph_run, "_pgraph_run_hooks", hooks)
    setattr(graph_run, "_pgraph_original_next", original_next)

    async def _instrumented_next(
        self: GraphRun[Any, Any, Any],
        node: BaseNode[Any, Any, Any] | None = None,
    ) -> BaseNode[Any, Any, Any] | End[Any]:
        run_hooks: RunHooks | None = getattr(self, "_pgraph_run_hooks", None)
        if run_hooks is None:
            return await original_next(node)

        active_node = node if node is not None else self.next_node
        if isinstance(active_node, BaseNode):
            await _maybe_await(run_hooks.on_node_start, self, active_node)

        try:
            result = await original_next(node)
        except BaseException as exc:
            if isinstance(active_node, BaseNode):
                await _maybe_await(run_hooks.on_error, self, active_node, exc)
            raise

        if isinstance(active_node, BaseNode):
            await _maybe_await(run_hooks.on_node_end, self, active_node, result)
            if isinstance(result, BaseNode):
                await _maybe_await(run_hooks.on_edge_taken, self, active_node, result)
            elif isinstance(result, End):
                await _maybe_await(run_hooks.on_run_end, self, result)

        return result

    graph_run.next = types.MethodType(_instrumented_next, graph_run)
    return graph_run


@asynccontextmanager
async def iter_instrumented(
    graph: Graph[Any, Any, Any],
    start_node: BaseNode[Any, Any, Any],
    *,
    state: Any = None,
    deps: Any = None,
    persistence: Any = None,
    hooks: RunHooks,
) -> AsyncIterator[GraphRun[Any, Any, Any]]:
    """Iterate over a graph run while emitting instrumentation callbacks."""

    async with graph.iter(start_node, state=state, deps=deps, persistence=persistence, infer_name=True) as graph_run:
        instrument_graph_run(graph_run, hooks)
        yield graph_run


async def run_instrumented(
    graph: Graph[Any, Any, Any],
    start_node: BaseNode[Any, Any, Any],
    *,
    state: Any = None,
    deps: Any = None,
    persistence: Any = None,
    hooks: RunHooks,
) -> GraphRunResult[Any, Any]:
    """Run a graph to completion with instrumentation."""

    async with iter_instrumented(
        graph,
        start_node,
        state=state,
        deps=deps,
        persistence=persistence,
        hooks=hooks,
    ) as graph_run:
        async for _node in graph_run:
            pass
        result = graph_run.result
        assert result is not None, "GraphRun should have a result"
        return result


def run_instrumented_sync(
    graph: Graph[Any, Any, Any],
    start_node: BaseNode[Any, Any, Any],
    *,
    state: Any = None,
    deps: Any = None,
    persistence: Any = None,
    hooks: RunHooks,
) -> GraphRunResult[Any, Any]:
    """Synchronously run a graph with instrumentation."""

    return _get_event_loop().run_until_complete(
        run_instrumented(
            graph,
            start_node,
            state=state,
            deps=deps,
            persistence=persistence,
            hooks=hooks,
        )
    )


def _get_event_loop() -> asyncio.AbstractEventLoop:
    try:
        event_loop = asyncio.get_event_loop()
    except RuntimeError:
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
    return event_loop
