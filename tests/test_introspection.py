from __future__ import annotations

from dataclasses import dataclass

from pydantic_graph import BaseNode, End, Graph, GraphRunContext

from pydantic_graph_studio.introspection import build_graph_model


@dataclass
class Start(BaseNode[None, None, int]):
    async def run(self, ctx: GraphRunContext) -> Dynamic | Middle:
        return Dynamic()


@dataclass
class Dynamic(BaseNode[None, None, int]):
    async def run(self, ctx: GraphRunContext) -> BaseNode[None, None, int]:
        return Middle()


@dataclass
class Middle(BaseNode[None, None, int]):
    async def run(self, ctx: GraphRunContext) -> End[int]:
        return End(1)


def test_build_graph_model_includes_edges_and_nodes() -> None:
    nodes: list[type[BaseNode[None, None, int]]] = [Start, Dynamic, Middle]
    graph = Graph[None, None, int](nodes=nodes)
    model = build_graph_model(graph)

    node_ids = {node.label: node.node_id for node in model.nodes}
    assert node_ids["Start"] == Start.get_node_id()
    assert node_ids["Dynamic"] == Dynamic.get_node_id()
    assert node_ids["Middle"] == Middle.get_node_id()

    assert model.entry_nodes == [Start.get_node_id()]
    assert model.terminal_nodes == [Middle.get_node_id()]

    edges = {(edge.source_node_id, edge.target_node_id, edge.dynamic) for edge in model.edges}
    assert (Start.get_node_id(), Dynamic.get_node_id(), False) in edges
    assert (Start.get_node_id(), Middle.get_node_id(), False) in edges
    assert (Dynamic.get_node_id(), None, True) in edges


def test_node_ids_deterministic_across_runs() -> None:
    nodes: list[type[BaseNode[None, None, int]]] = [Start, Dynamic, Middle]
    graph = Graph[None, None, int](nodes=nodes)
    model_one = build_graph_model(graph)
    model_two = build_graph_model(graph)

    assert [node.node_id for node in model_one.nodes] == [node.node_id for node in model_two.nodes]
