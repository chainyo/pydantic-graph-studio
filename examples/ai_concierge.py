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


@builder.step(node_id="ResultsGate", label="Results Gate")
async def results_gate(ctx: StepContext[None, None, None]) -> bool:
    await asyncio.sleep(0.15)
    return _flag("CONCIERGE_RESULTS_AVAILABLE", default=True)


@builder.step(node_id="ThreadGate", label="Thread Gate")
async def thread_gate(ctx: StepContext[None, None, None]) -> bool:
    await asyncio.sleep(0.15)
    return _flag("CONCIERGE_THREAD_LOCKED", default=False)


@builder.step(node_id="Escalate", label="Escalate")
async def escalate(ctx: StepContext[None, None, bool]) -> str:
    await asyncio.sleep(0.2)
    return "Escalated: lock thread and alert clinician"


@builder.step(node_id="PlannerLLM", label="Planner LLM")
async def planner(ctx: StepContext[None, None, bool]) -> None:
    await asyncio.sleep(0.2)
    return None


@builder.step(node_id="FetchQuestionnaire", label="Fetch Questionnaire")
async def fetch_questionnaire(ctx: StepContext[None, None, None]) -> dict[str, str]:
    await asyncio.sleep(0.35)
    return {"questionnaire": "completed"}


@builder.step(node_id="FetchBiomarkers", label="Fetch Biomarkers")
async def fetch_biomarkers(ctx: StepContext[None, None, None]) -> dict[str, str]:
    await asyncio.sleep(0.4)
    return {"biomarkers": "refreshed"}


@builder.step(node_id="FetchTranscript", label="Fetch Transcript")
async def fetch_transcript(ctx: StepContext[None, None, None]) -> dict[str, str]:
    await asyncio.sleep(0.45)
    return {"transcript": "indexed"}


@builder.step(node_id="AnswerLLM", label="Answer LLM")
async def answer_llm(ctx: StepContext[None, None, dict[str, str]]) -> str:
    await asyncio.sleep(0.2)
    summary = ", ".join(sorted(ctx.inputs.keys()))
    return f"answer drafted from {summary}"


@builder.step(node_id="AttributionValidation", label="Attribution Validation")
async def attribution_validation(ctx: StepContext[None, None, str]) -> str:
    await asyncio.sleep(0.2)
    return ctx.inputs


results_decision = builder.decision(node_id="ResultsDecision", note="Results available?")
results_decision = results_decision.branch(builder.match(Literal[True]).to(thread_gate))
results_decision = results_decision.branch(builder.match(Literal[False]).to(escalate))

thread_decision = builder.decision(node_id="ThreadDecision", note="Thread locked?")
thread_decision = thread_decision.branch(builder.match(Literal[True]).to(escalate))
thread_decision = thread_decision.branch(builder.match(Literal[False]).to(planner))

fetch_join = builder.join(
    reduce_dict_update,
    initial_factory=dict,
    node_id="FetchJoin",
)

builder.add(builder.edge_from(builder.start_node).to(results_gate))
builder.add(builder.edge_from(results_gate).to(results_decision))
builder.add(builder.edge_from(thread_gate).to(thread_decision))
builder.add_edge(escalate, builder.end_node)

builder.add(
    builder.edge_from(planner).broadcast(
        lambda edge: [
            edge.to(fetch_questionnaire),
            edge.to(fetch_biomarkers),
            edge.to(fetch_transcript),
        ],
        fork_id="FetchFork",
    )
)

builder.add_edge(fetch_questionnaire, fetch_join)
builder.add_edge(fetch_biomarkers, fetch_join)
builder.add_edge(fetch_transcript, fetch_join)
builder.add_edge(fetch_join, answer_llm)
builder.add_edge(answer_llm, attribution_validation)
builder.add_edge(attribution_validation, builder.end_node)

graph = builder.build()
