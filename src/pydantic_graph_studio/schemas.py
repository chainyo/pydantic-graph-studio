from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, TypeAdapter


class GraphNode(BaseModel):
    """Represents a node in the introspected graph."""

    node_id: str
    label: str | None = None


class GraphEdge(BaseModel):
    """Represents a directed edge between nodes."""

    source_node_id: str
    target_node_id: str | None = None
    dynamic: bool = False


class GraphModel(BaseModel):
    """Container for the full graph payload."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    entry_nodes: list[str]
    terminal_nodes: list[str]


class EventBase(BaseModel):
    """Base event fields shared across all runtime events."""

    run_id: str
    event_type: str


class NodeStartEvent(EventBase):
    """Emitted when a node begins execution."""

    event_type: Literal["node_start"]
    node_id: str


class NodeEndEvent(EventBase):
    """Emitted when a node finishes execution."""

    event_type: Literal["node_end"]
    node_id: str


class EdgeTakenEvent(EventBase):
    """Emitted when an edge is traversed during execution."""

    event_type: Literal["edge_taken"]
    source_node_id: str
    target_node_id: str | None = None


class RunEndEvent(EventBase):
    """Emitted when a run completes successfully."""

    event_type: Literal["run_end"]


class ToolCallEvent(EventBase):
    """Emitted when a tool call starts."""

    event_type: Literal["tool_call"]
    node_id: str
    tool_name: str
    call_id: str
    arguments: Any


class ToolResultEvent(EventBase):
    """Emitted when a tool call completes."""

    event_type: Literal["tool_result"]
    node_id: str
    tool_name: str
    call_id: str
    output: Any
    success: bool = True


class InputRequestEvent(EventBase):
    """Emitted when a node requests human input."""

    event_type: Literal["input_request"]
    node_id: str
    request_id: str
    prompt: str
    options: list[str]
    context: Any | None = None


class InputResponseEvent(EventBase):
    """Emitted when a response is provided to an input request."""

    event_type: Literal["input_response"]
    node_id: str
    request_id: str
    response: str


class ErrorEvent(EventBase):
    """Emitted when a run terminates due to an error."""

    event_type: Literal["error"]
    message: str
    node_id: str | None = None


Event = Annotated[
    NodeStartEvent
    | NodeEndEvent
    | EdgeTakenEvent
    | RunEndEvent
    | ToolCallEvent
    | ToolResultEvent
    | InputRequestEvent
    | InputResponseEvent
    | ErrorEvent,
    Field(discriminator="event_type"),
]


def graph_schema() -> dict[str, Any]:
    """Return the JSON Schema for the graph payload."""

    return GraphModel.model_json_schema()


def event_schema() -> dict[str, Any]:
    """Return the JSON Schema for the event payload."""

    return TypeAdapter(Event).json_schema()


def export_schemas() -> dict[str, dict[str, Any]]:
    """Export all JSON Schemas keyed by payload name."""

    return {
        "graph": graph_schema(),
        "event": event_schema(),
    }
