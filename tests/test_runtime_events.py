from __future__ import annotations

import asyncio
from dataclasses import dataclass

from pydantic_graph import BaseNode, End, Graph, GraphRunContext

from pydantic_graph_studio.runtime import InteractionHub, iter_run_events, resolve_interaction
from pydantic_graph_studio.schemas import InputRequestEvent


@dataclass
class First(BaseNode[None, None, int]):
    async def run(self, ctx: GraphRunContext) -> Second:
        return Second()


@dataclass
class Second(BaseNode[None, None, int]):
    async def run(self, ctx: GraphRunContext) -> End[int]:
        return End(42)


@dataclass
class Boom(BaseNode[None, None, int]):
    async def run(self, ctx: GraphRunContext) -> End[int]:
        raise RuntimeError("boom")


@dataclass
class AskApproval(BaseNode[None, None, int]):
    async def run(self, ctx: GraphRunContext) -> End[int]:
        interaction = resolve_interaction(ctx.deps)
        assert interaction is not None
        response = await interaction.request_input(
            node_id=self.get_node_id(),
            prompt="Approve?",
            options=["yes", "no"],
            context="draft preview",
        )
        return End(1 if response == "yes" else 0)


def _collect_events(graph: Graph[None, None, int], start_node: BaseNode[None, None, int]) -> list:
    async def _run() -> list:
        events = []
        async for event in iter_run_events(graph, start_node):
            events.append(event)
        return events

    return asyncio.run(_run())


def test_iter_run_events_ordered() -> None:
    nodes: list[type[BaseNode[None, None, int]]] = [First, Second]
    graph = Graph[None, None, int](nodes=nodes)
    events = _collect_events(graph, First())

    event_types = [event.event_type for event in events]
    assert event_types == [
        "node_start",
        "node_end",
        "edge_taken",
        "node_start",
        "node_end",
        "run_end",
    ]

    run_ids = {event.run_id for event in events}
    assert len(run_ids) == 1

    assert events[0].node_id == First.get_node_id()
    assert events[2].source_node_id == First.get_node_id()
    assert events[2].target_node_id == Second.get_node_id()
    assert events[-1].event_type == "run_end"


def test_iter_run_events_error_emits_error_event() -> None:
    nodes: list[type[BaseNode[None, None, int]]] = [Boom]
    graph = Graph[None, None, int](nodes=nodes)
    events = _collect_events(graph, Boom())

    event_types = [event.event_type for event in events]
    assert event_types[0] == "node_start"
    assert "error" in event_types
    assert "run_end" not in event_types


def test_iter_run_events_interactive_input() -> None:
    nodes: list[type[BaseNode[None, None, int]]] = [AskApproval]
    graph = Graph[None, None, int](nodes=nodes)

    async def _run() -> list:
        interaction = InteractionHub()
        events = []
        async for event in iter_run_events(graph, AskApproval(), interaction=interaction):
            events.append(event)
            if isinstance(event, InputRequestEvent):
                await interaction.resolve_input(event.request_id, "yes")
        return events

    events = asyncio.run(_run())
    event_types = [event.event_type for event in events]
    assert event_types == [
        "node_start",
        "input_request",
        "input_response",
        "node_end",
        "run_end",
    ]
    input_request = events[1]
    assert isinstance(input_request, InputRequestEvent)
    assert input_request.context == "draft preview"
