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


def _load_ai_concierge() -> Any:
    from . import ai_concierge as ai_concierge_module

    return ai_concierge_module.graph


_EXAMPLES: dict[str, ExampleSpec] = {
    "graph": ExampleSpec(
        name="graph",
        title="Branching Steps",
        description="Async branching graph with looped steps and a final End node.",
        loader=_load_basic_graph,
    ),
    "ai-concierge": ExampleSpec(
        name="ai-concierge",
        title="AI Concierge",
        description="Beta graph with decisions, joins, and parallel fetch steps.",
        loader=_load_ai_concierge,
    ),
}

_ALIASES = {
    "ai_concierge": "ai-concierge",
}


def list_examples() -> list[ExampleSpec]:
    return sorted(_EXAMPLES.values(), key=lambda spec: spec.name)


def get_example(name: str) -> ExampleSpec:
    normalized = name.strip()
    normalized = _ALIASES.get(normalized, normalized)
    try:
        return _EXAMPLES[normalized]
    except KeyError as exc:  # pragma: no cover - mapped to CLI error
        raise KeyError(normalized) from exc


__all__ = [
    "ExampleSpec",
    "get_example",
    "list_examples",
]
