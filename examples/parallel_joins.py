from __future__ import annotations

import asyncio
import os
from typing import Literal

from pydantic_graph.beta.graph_builder import GraphBuilder
from pydantic_graph.beta.join import reduce_dict_update
from pydantic_graph.beta.step import StepContext


def _flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


builder: GraphBuilder[None, None, None, str] = GraphBuilder()


@builder.step(node_id="InputGate", label="Input Gate")
async def input_gate(ctx: StepContext[None, None, None]) -> bool:
    await asyncio.sleep(0.15)
    return _flag("PARALLEL_INPUT_READY", default=True)


@builder.step(node_id="Escalate", label="Escalate")
async def escalate(ctx: StepContext[None, None, bool]) -> str:
    await asyncio.sleep(0.2)
    return "Escalated: manual review required"


@builder.step(node_id="Planner", label="Planner")
async def planner(ctx: StepContext[None, None, bool]) -> None:
    await asyncio.sleep(0.2)
    return None


@builder.step(node_id="FetchProfile", label="Fetch Profile")
async def fetch_profile(ctx: StepContext[None, None, None]) -> dict[str, str]:
    await asyncio.sleep(0.35)
    return {"profile": "ready"}


@builder.step(node_id="FetchMetrics", label="Fetch Metrics")
async def fetch_metrics(ctx: StepContext[None, None, None]) -> dict[str, str]:
    await asyncio.sleep(0.4)
    return {"metrics": "refreshed"}


@builder.step(node_id="FetchHistory", label="Fetch History")
async def fetch_history(ctx: StepContext[None, None, None]) -> dict[str, str]:
    await asyncio.sleep(0.45)
    return {"history": "loaded"}


@builder.step(node_id="Synthesize", label="Synthesize")
async def synthesize(ctx: StepContext[None, None, dict[str, str]]) -> str:
    await asyncio.sleep(0.2)
    summary = ", ".join(sorted(ctx.inputs.keys()))
    return f"synthesized from {summary}"


@builder.step(node_id="Finalize", label="Finalize")
async def finalize(ctx: StepContext[None, None, str]) -> str:
    await asyncio.sleep(0.2)
    return ctx.inputs


input_decision = builder.decision(node_id="InputDecision", note="Input ready?")
input_decision = input_decision.branch(builder.match(Literal[True]).to(planner))
input_decision = input_decision.branch(builder.match(Literal[False]).to(escalate))

fetch_join = builder.join(
    reduce_dict_update,
    initial_factory=dict,
    node_id="FetchJoin",
)

builder.add(builder.edge_from(builder.start_node).to(input_gate))
builder.add(builder.edge_from(input_gate).to(input_decision))
builder.add_edge(escalate, builder.end_node)

builder.add(
    builder.edge_from(planner).broadcast(
        lambda edge: [
            edge.to(fetch_profile),
            edge.to(fetch_metrics),
            edge.to(fetch_history),
        ],
        fork_id="FetchFork",
    )
)

builder.add_edge(fetch_profile, fetch_join)
builder.add_edge(fetch_metrics, fetch_join)
builder.add_edge(fetch_history, fetch_join)
builder.add_edge(fetch_join, synthesize)
builder.add_edge(synthesize, finalize)
builder.add_edge(finalize, builder.end_node)

graph = builder.build()
