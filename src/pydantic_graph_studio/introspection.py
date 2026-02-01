from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from pydantic_graph import Graph
from pydantic_graph.nodes import NodeDef

from pydantic_graph_studio.schemas import GraphEdge, GraphModel, GraphNode


def build_graph_model(graph: Graph[Any, Any, Any]) -> GraphModel:
    """Build a GraphModel payload from a pydantic_graph.Graph instance."""

    node_defs = _sorted_node_defs(graph.node_defs)
    nodes = _build_nodes(node_defs)
    edges = _build_edges(node_defs)
    entry_nodes = _infer_entry_nodes(node_defs, edges)
    terminal_nodes = _infer_terminal_nodes(node_defs)
    return GraphModel(
        nodes=nodes,
        edges=edges,
        entry_nodes=entry_nodes,
        terminal_nodes=terminal_nodes,
    )


def serialize_graph(graph: Graph[Any, Any, Any]) -> dict[str, Any]:
    """Serialize a graph into a JSON-safe dict payload."""

    return build_graph_model(graph).model_dump(mode="json")


def _sorted_node_defs(node_defs: Mapping[str, NodeDef[Any, Any, Any]]) -> list[NodeDef[Any, Any, Any]]:
    return [node_defs[node_id] for node_id in sorted(node_defs.keys())]


def _build_nodes(node_defs: Iterable[NodeDef[Any, Any, Any]]) -> list[GraphNode]:
    return [
        GraphNode(
            node_id=node_def.node_id,
            label=node_def.node.__name__,
        )
        for node_def in node_defs
    ]


def _build_edges(node_defs: Iterable[NodeDef[Any, Any, Any]]) -> list[GraphEdge]:
    edges: list[GraphEdge] = []
    for node_def in node_defs:
        for target_id in sorted(node_def.next_node_edges.keys()):
            edges.append(
                GraphEdge(
                    source_node_id=node_def.node_id,
                    target_node_id=target_id,
                    dynamic=False,
                )
            )
        if node_def.returns_base_node:
            edges.append(
                GraphEdge(
                    source_node_id=node_def.node_id,
                    target_node_id=None,
                    dynamic=True,
                )
            )
    return edges


def _infer_entry_nodes(
    node_defs: Iterable[NodeDef[Any, Any, Any]],
    edges: Iterable[GraphEdge],
) -> list[str]:
    node_ids = {node_def.node_id for node_def in node_defs}
    inbound: set[str] = set()
    for edge in edges:
        if edge.target_node_id is not None:
            inbound.add(edge.target_node_id)
    entry_nodes = sorted(node_ids - inbound)
    return entry_nodes


def _infer_terminal_nodes(node_defs: Iterable[NodeDef[Any, Any, Any]]) -> list[str]:
    terminal_nodes = sorted(node_def.node_id for node_def in node_defs if node_def.end_edge is not None)
    return terminal_nodes
