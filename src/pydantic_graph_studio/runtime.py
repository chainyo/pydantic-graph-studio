"""Runtime instrumentation utilities for pydantic_graph execution."""

from __future__ import annotations

import asyncio
import inspect
import types
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from pydantic_graph import Graph
from pydantic_graph.graph import GraphRun, GraphRunResult
from pydantic_graph.nodes import BaseNode, End

from pydantic_graph_studio.schemas import (
    EdgeTakenEvent,
    ErrorEvent,
    Event,
    NodeEndEvent,
    NodeStartEvent,
    RunEndEvent,
)

BetaGraph: type[Any] | None = None
BetaEndMarker: type[Any] = object
BetaJoinItem: type[Any] = object
try:  # pragma: no cover - optional beta support
    from pydantic_graph.beta.graph import EndMarker as _BetaEndMarker
    from pydantic_graph.beta.graph import Graph as _BetaGraph
    from pydantic_graph.beta.graph import JoinItem as _BetaJoinItem
except ModuleNotFoundError:  # pragma: no cover
    pass
else:
    BetaGraph = _BetaGraph
    BetaEndMarker = _BetaEndMarker
    BetaJoinItem = _BetaJoinItem

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
        setattr(graph_run, "_pgraph_run_hooks", hooks)  # noqa: B010
        return graph_run

    original_next = graph_run.next
    setattr(graph_run, "_pgraph_instrumented", True)  # noqa: B010
    setattr(graph_run, "_pgraph_run_hooks", hooks)  # noqa: B010
    setattr(graph_run, "_pgraph_original_next", original_next)  # noqa: B010

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

    setattr(graph_run, "next", types.MethodType(_instrumented_next, graph_run))  # noqa: B010
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


async def iter_run_events(
    graph: Graph[Any, Any, Any],
    start_node: BaseNode[Any, Any, Any] | None = None,
    *,
    state: Any = None,
    deps: Any = None,
    persistence: Any = None,
    inputs: Any = None,
    run_id: str | None = None,
) -> AsyncIterator[Event]:
    """Yield an ordered stream of runtime events for a graph run."""

    if _is_beta_graph(graph):
        async for event in _iter_run_events_beta(
            graph,
            state=state,
            deps=deps,
            inputs=inputs,
            run_id=run_id,
        ):
            yield event
        return

    if start_node is None:
        raise ValueError("start_node is required for v1 graphs")

    if run_id is None:
        run_id = uuid4().hex
    queue: asyncio.Queue[Event] = asyncio.Queue()
    done = asyncio.Event()

    async def emit(event: Event) -> None:
        await queue.put(event)

    async def on_node_start(
        _run: GraphRun[Any, Any, Any],
        node: BaseNode[Any, Any, Any],
    ) -> None:
        await emit(
            NodeStartEvent(
                run_id=run_id,
                event_type="node_start",
                node_id=node.get_node_id(),
            )
        )

    async def on_node_end(
        _run: GraphRun[Any, Any, Any],
        node: BaseNode[Any, Any, Any],
        _result: BaseNode[Any, Any, Any] | End[Any],
    ) -> None:
        await emit(
            NodeEndEvent(
                run_id=run_id,
                event_type="node_end",
                node_id=node.get_node_id(),
            )
        )

    async def on_edge_taken(
        _run: GraphRun[Any, Any, Any],
        source: BaseNode[Any, Any, Any],
        target: BaseNode[Any, Any, Any],
    ) -> None:
        await emit(
            EdgeTakenEvent(
                run_id=run_id,
                event_type="edge_taken",
                source_node_id=source.get_node_id(),
                target_node_id=target.get_node_id(),
            )
        )

    async def on_run_end(
        _run: GraphRun[Any, Any, Any],
        _end: End[Any],
    ) -> None:
        await emit(
            RunEndEvent(
                run_id=run_id,
                event_type="run_end",
            )
        )
        done.set()

    async def on_error(
        _run: GraphRun[Any, Any, Any],
        node: BaseNode[Any, Any, Any],
        exc: BaseException,
    ) -> None:
        await emit(
            ErrorEvent(
                run_id=run_id,
                event_type="error",
                message=str(exc),
                node_id=node.get_node_id(),
            )
        )
        done.set()

    hooks = RunHooks(
        on_node_start=on_node_start,
        on_node_end=on_node_end,
        on_edge_taken=on_edge_taken,
        on_run_end=on_run_end,
        on_error=on_error,
    )

    async def _run() -> None:
        try:
            await run_instrumented(
                graph,
                start_node,
                state=state,
                deps=deps,
                persistence=persistence,
                hooks=hooks,
            )
        except BaseException as exc:
            if not done.is_set():
                await emit(
                    ErrorEvent(
                        run_id=run_id,
                        event_type="error",
                        message=str(exc),
                        node_id=None,
                    )
                )
        finally:
            done.set()

    task = asyncio.create_task(_run())
    try:
        while True:
            if done.is_set() and queue.empty():
                break
            event = await queue.get()
            yield event
    finally:
        if not task.done():
            task.cancel()
        with suppress(asyncio.CancelledError):
            await task


def _is_beta_graph(graph: Any) -> bool:
    return BetaGraph is not None and isinstance(graph, BetaGraph)


async def _iter_run_events_beta(
    graph: Any,
    *,
    state: Any = None,
    deps: Any = None,
    inputs: Any = None,
    run_id: str | None = None,
) -> AsyncIterator[Event]:
    if run_id is None:
        run_id = uuid4().hex
    queue: asyncio.Queue[Event] = asyncio.Queue()
    done = asyncio.Event()

    async def emit(event: Event) -> None:
        await queue.put(event)

    async def _run() -> None:
        try:
            async with graph.iter(state=state, deps=deps, inputs=inputs, infer_name=True) as graph_run:
                iterator = graph_run._iterator_instance
                original_run_task = iterator._run_task

                async def instrumented_run_task(task: Any) -> Any:
                    node_id = str(task.node_id)
                    await emit(NodeStartEvent(run_id=run_id, event_type="node_start", node_id=node_id))
                    try:
                        result = await original_run_task(task)
                    except BaseException as exc:
                        await emit(
                            ErrorEvent(
                                run_id=run_id,
                                event_type="error",
                                message=str(exc),
                                node_id=node_id,
                            )
                        )
                        raise
                    await emit(NodeEndEvent(run_id=run_id, event_type="node_end", node_id=node_id))

                    if isinstance(result, BetaEndMarker):
                        await emit(RunEndEvent(run_id=run_id, event_type="run_end"))
                        done.set()
                    elif isinstance(result, BetaJoinItem):
                        await emit(
                            EdgeTakenEvent(
                                run_id=run_id,
                                event_type="edge_taken",
                                source_node_id=node_id,
                                target_node_id=str(result.join_id),
                            )
                        )
                    elif isinstance(result, Sequence):
                        for new_task in result:
                            await emit(
                                EdgeTakenEvent(
                                    run_id=run_id,
                                    event_type="edge_taken",
                                    source_node_id=node_id,
                                    target_node_id=str(new_task.node_id),
                                )
                            )
                    return result

                iterator._run_task = instrumented_run_task

                async for _item in graph_run:
                    pass
        except BaseException as exc:
            if not done.is_set():
                await emit(
                    ErrorEvent(
                        run_id=run_id,
                        event_type="error",
                        message=str(exc),
                        node_id=None,
                    )
                )
        finally:
            done.set()

    task = asyncio.create_task(_run())
    try:
        while True:
            if done.is_set() and queue.empty():
                break
            event = await queue.get()
            yield event
    finally:
        if not task.done():
            task.cancel()
        with suppress(asyncio.CancelledError):
            await task


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
