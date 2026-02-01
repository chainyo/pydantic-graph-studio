"""Pydantic Graph Studio entrypoint."""

from pydantic_graph_studio.introspection import build_graph_model, serialize_graph
from pydantic_graph_studio.runtime import (
    RunHooks,
    instrument_graph_run,
    iter_instrumented,
    iter_run_events,
    run_instrumented,
    run_instrumented_sync,
)
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
from pydantic_graph_studio.server import RunRegistry, create_app

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
    "RunHooks",
    "RunRegistry",
    "build_graph_model",
    "create_app",
    "event_schema",
    "export_schemas",
    "graph_schema",
    "instrument_graph_run",
    "iter_instrumented",
    "iter_run_events",
    "main",
    "run_instrumented",
    "run_instrumented_sync",
    "serialize_graph",
]


def main() -> None:
    """CLI entrypoint placeholder."""

    print("pydantic-graph-studio is not implemented yet.")
