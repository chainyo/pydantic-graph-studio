from __future__ import annotations

import asyncio

from pydantic_graph.beta.graph_builder import GraphBuilder
from pydantic_graph.beta.join import reduce_dict_update
from pydantic_graph.beta.step import StepContext

from pydantic_graph_studio.runtime import iter_run_events


def _collect_events(graph) -> list:
    async def _run() -> list:
        events = []
        async for event in iter_run_events(graph, None):
            events.append(event)
            if event.event_type in {"run_end", "error"}:
                break
        return events

    return asyncio.run(_run())


def test_beta_iter_run_events_parallel_edges() -> None:
    builder: GraphBuilder[None, None, None, dict[str, str]] = GraphBuilder()

    @builder.step(node_id="Planner")
    async def planner(ctx: StepContext[None, None, None]) -> None:
        return None

    @builder.step(node_id="FetchFast")
    async def fetch_fast(ctx: StepContext[None, None, None]) -> dict[str, str]:
        await asyncio.sleep(0.01)
        return {"fast": "ok"}

    @builder.step(node_id="FetchSlow")
    async def fetch_slow(ctx: StepContext[None, None, None]) -> dict[str, str]:
        await asyncio.sleep(0.05)
        return {"slow": "ok"}

    join = builder.join(reduce_dict_update, initial_factory=dict, node_id="JoinFetch")

    builder.add(builder.edge_from(builder.start_node).to(planner))
    builder.add(
        builder.edge_from(planner).broadcast(
            lambda edge: [edge.to(fetch_fast), edge.to(fetch_slow)],
            fork_id="FetchFork",
        )
    )
    builder.add_edge(fetch_fast, join)
    builder.add_edge(fetch_slow, join)
    builder.add_edge(join, builder.end_node)

    graph = builder.build()
    events = _collect_events(graph)

    event_types = {event.event_type for event in events}
    assert "node_start" in event_types
    assert "node_end" in event_types
    assert "edge_taken" in event_types
    assert "run_end" in event_types

    edge_pairs = {
        (event.source_node_id, event.target_node_id)
        for event in events
        if event.event_type == "edge_taken"
    }
    assert ("Planner", "FetchFork") in edge_pairs
    assert ("FetchFork", "FetchFast") in edge_pairs
    assert ("FetchFork", "FetchSlow") in edge_pairs
