"""Pydantic Graph Studio entrypoint."""

from pydantic_graph_studio.introspection import build_graph_model, serialize_graph
from pydantic_graph_studio.schemas import (
    EdgeTakenEvent,
    ErrorEvent,
    Event,
    EventBase,
    GraphEdge,
    GraphModel,
    GraphNode,
    NodeEndEvent,
    NodeStartEvent,
    RunEndEvent,
    event_schema,
    export_schemas,
    graph_schema,
)

__all__ = [
    "EdgeTakenEvent",
    "ErrorEvent",
    "Event",
    "EventBase",
    "GraphEdge",
    "GraphModel",
    "GraphNode",
    "NodeEndEvent",
    "NodeStartEvent",
    "RunEndEvent",
    "build_graph_model",
    "event_schema",
    "export_schemas",
    "graph_schema",
    "main",
    "serialize_graph",
]


def main() -> None:
    """CLI entrypoint placeholder."""

    print("pydantic-graph-studio is not implemented yet.")
