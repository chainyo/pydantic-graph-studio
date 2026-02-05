"""Built-in examples for Pydantic Graph Studio."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

ExampleLoader = Callable[[], Any]


@dataclass(frozen=True, slots=True)
class ExampleSpec:
    name: str
    title: str
    description: str
    loader: ExampleLoader


def _load_basic_graph() -> Any:
    from . import graph as graph_module

    return graph_module.graph


def _load_parallel_joins() -> Any:
    from . import parallel_joins as parallel_joins_module

    return parallel_joins_module.graph


def _load_error_handling() -> Any:
    from . import error_handling as error_handling_module

    return error_handling_module.graph


def _load_tool_usage() -> Any:
    from . import tool_usage as tool_usage_module

    return tool_usage_module.graph


def _load_streaming_events() -> Any:
    from . import streaming_events as streaming_events_module

    return streaming_events_module.graph


def _load_human_in_the_loop() -> Any:
    from . import human_in_the_loop as human_in_the_loop_module

    return human_in_the_loop_module.graph


_EXAMPLES: dict[str, ExampleSpec] = {
    "graph": ExampleSpec(
        name="graph",
        title="Branching Steps",
        description="Async branching graph with looped steps and a final End node.",
        loader=_load_basic_graph,
    ),
    "parallel-joins": ExampleSpec(
        name="parallel-joins",
        title="Parallel Joins",
        description="Beta graph with a fork-join pattern and parallel fetch steps.",
        loader=_load_parallel_joins,
    ),
    "error-handling": ExampleSpec(
        name="error-handling",
        title="Error Handling",
        description="Shows an explicit error branch and recovery path.",
        loader=_load_error_handling,
    ),
    "tool-usage": ExampleSpec(
        name="tool-usage",
        title="Tool Usage",
        description="Simulates a tool call and result handling.",
        loader=_load_tool_usage,
    ),
    "streaming-events": ExampleSpec(
        name="streaming-events",
        title="Streaming Events",
        description="Loops to generate repeated runtime events.",
        loader=_load_streaming_events,
    ),
    "human-in-the-loop": ExampleSpec(
        name="human-in-the-loop",
        title="Human In The Loop",
        description="Simulates a human approval step before finishing.",
        loader=_load_human_in_the_loop,
    ),
}


def list_examples() -> list[ExampleSpec]:
    return sorted(_EXAMPLES.values(), key=lambda spec: spec.name)


def get_example(name: str) -> ExampleSpec:
    normalized = name.strip().lower().replace("_", "-")
    try:
        return _EXAMPLES[normalized]
    except KeyError as exc:  # pragma: no cover - mapped to CLI error
        raise KeyError(normalized) from exc


__all__ = [
    "ExampleSpec",
    "get_example",
    "list_examples",
]
