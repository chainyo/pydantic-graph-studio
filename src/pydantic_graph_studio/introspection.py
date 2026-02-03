from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from pydantic_graph import Graph
from pydantic_graph.nodes import NodeDef

from pydantic_graph_studio.schemas import GraphEdge, GraphModel, GraphNode

BetaGraph: type[Any] | None = None
try:  # pragma: no cover - optional beta support
    from pydantic_graph.beta.decision import Decision as BetaDecision
    from pydantic_graph.beta.graph import Graph as _BetaGraph
    from pydantic_graph.beta.join import Join as BetaJoin
    from pydantic_graph.beta.node import EndNode as BetaEndNode
    from pydantic_graph.beta.node import Fork as BetaFork
    from pydantic_graph.beta.node import StartNode as BetaStartNode
    from pydantic_graph.beta.paths import DestinationMarker as BetaDestinationMarker
    from pydantic_graph.beta.paths import Path as BetaPath
    from pydantic_graph.beta.step import NodeStep as BetaNodeStep
    from pydantic_graph.beta.step import Step as BetaStep
except ModuleNotFoundError:  # pragma: no cover
    pass
else:
    BetaGraph = _BetaGraph


def build_graph_model(graph: Any) -> GraphModel:
    """Build a GraphModel payload from a pydantic_graph.Graph instance."""

    if _is_beta_graph(graph):
        return _build_beta_graph_model(graph)

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


def _is_beta_graph(graph: Any) -> bool:
    return BetaGraph is not None and isinstance(graph, BetaGraph)


def _build_beta_graph_model(graph: Any) -> GraphModel:
    nodes = _build_beta_nodes(graph)
    edges = _build_beta_edges(graph.edges_by_source, graph.nodes)
    entry_nodes = _infer_beta_entry_nodes(graph)
    terminal_nodes = _infer_beta_terminal_nodes(graph)
    return GraphModel(
        nodes=nodes,
        edges=edges,
        entry_nodes=entry_nodes,
        terminal_nodes=terminal_nodes,
    )


def _build_beta_nodes(graph: Any) -> list[GraphNode]:
    items = sorted(graph.nodes.items(), key=lambda item: str(item[0]))
    return [
        GraphNode(
            node_id=str(node_id),
            label=_beta_node_label(node),
        )
        for node_id, node in items
    ]


def _beta_node_label(node: Any) -> str | None:
    if BetaGraph is None:
        return None
    if isinstance(node, BetaStartNode):
        return "Start"
    if isinstance(node, BetaEndNode):
        return "Done"
    if isinstance(node, BetaFork):
        return "Map Fork" if node.is_map else "Fork"
    if isinstance(node, BetaJoin):
        return "Join"
    if isinstance(node, BetaDecision):
        return "Decision"
    if isinstance(node, BetaNodeStep):
        return node.node_type.__name__
    if isinstance(node, BetaStep):
        return node.label or str(node.id)
    raw = getattr(node, "label", None) or getattr(node, "id", None)
    return str(raw) if raw is not None else None


def _build_beta_edges(
    edges_by_source: Mapping[Any, list[Any]], nodes: Mapping[Any, Any] | None = None
) -> list[GraphEdge]:
    edge_pairs: set[tuple[str, str]] = set()

    for source_id, paths in edges_by_source.items():
        for path in paths:
            for target_id in _beta_path_destinations(path):
                edge_pairs.add((str(source_id), str(target_id)))

    if nodes:
        for node_id, node in nodes.items():
            if BetaGraph is None or not isinstance(node, BetaDecision):
                continue
            for branch in node.branches:
                for target_id in _beta_path_destinations(branch.path):
                    edge_pairs.add((str(node_id), str(target_id)))

    edges = [
        GraphEdge(
            source_node_id=source_id,
            target_node_id=target_id,
            dynamic=False,
        )
        for source_id, target_id in sorted(edge_pairs)
    ]
    return edges


def _beta_path_destinations(path: Any) -> list[Any]:
    if BetaGraph is None:
        return []
    if not isinstance(path, BetaPath):
        return []
    destinations: list[Any] = []
    for item in path.items:
        if isinstance(item, BetaDestinationMarker):
            destinations.append(item.destination_id)
    return destinations


def _infer_beta_entry_nodes(graph: Any) -> list[str]:
    if BetaGraph is None:
        return []
    start_id = str(BetaStartNode.id)
    return [start_id] if start_id in {str(node_id) for node_id in graph.nodes.keys()} else []


def _infer_beta_terminal_nodes(graph: Any) -> list[str]:
    if BetaGraph is None:
        return []
    end_id = str(BetaEndNode.id)
    return [end_id] if end_id in {str(node_id) for node_id in graph.nodes.keys()} else []
