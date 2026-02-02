from __future__ import annotations

from pydantic_graph.beta.graph_builder import GraphBuilder
from pydantic_graph.beta.join import reduce_dict_update
from pydantic_graph.beta.step import StepContext

from pydantic_graph_studio.introspection import build_graph_model


def test_beta_graph_model_includes_parallel_edges() -> None:
    builder: GraphBuilder[None, None, None, dict[str, str]] = GraphBuilder()

    @builder.step(node_id="Planner")
    async def planner(ctx: StepContext[None, None, None]) -> None:
        return None

    @builder.step(node_id="FetchA")
    async def fetch_a(ctx: StepContext[None, None, None]) -> dict[str, str]:
        return {"a": "ok"}

    @builder.step(node_id="FetchB")
    async def fetch_b(ctx: StepContext[None, None, None]) -> dict[str, str]:
        return {"b": "ok"}

    join = builder.join(reduce_dict_update, initial_factory=dict, node_id="JoinFetch")

    builder.add(builder.edge_from(builder.start_node).to(planner))
    builder.add(
        builder.edge_from(planner).broadcast(
            lambda edge: [edge.to(fetch_a), edge.to(fetch_b)],
            fork_id="FetchFork",
        )
    )
    builder.add_edge(fetch_a, join)
    builder.add_edge(fetch_b, join)
    builder.add_edge(join, builder.end_node)

    graph = builder.build()
    model = build_graph_model(graph)

    edges = {(edge.source_node_id, edge.target_node_id) for edge in model.edges}
    assert ("__start__", "Planner") in edges
    assert ("Planner", "FetchFork") in edges
    assert ("FetchFork", "FetchA") in edges
    assert ("FetchFork", "FetchB") in edges
    assert ("FetchA", "JoinFetch") in edges
    assert ("FetchB", "JoinFetch") in edges
    assert ("JoinFetch", "__end__") in edges

    assert model.entry_nodes == ["__start__"]
    assert model.terminal_nodes == ["__end__"]
