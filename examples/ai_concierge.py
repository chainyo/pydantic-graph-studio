from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field

from pydantic_graph import BaseNode, End, Graph, GraphRunContext


def _flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass
class FetchBundle:
    results: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


async def _fetch_questionnaire() -> str:
    await asyncio.sleep(0.35)
    return "questionnaire: completed"


async def _fetch_biomarkers() -> str:
    await asyncio.sleep(0.4)
    return "biomarkers: refreshed"


async def _fetch_transcript() -> str:
    await asyncio.sleep(0.45)
    return "transcript: indexed"


async def _fetch_all() -> FetchBundle:
    questionnaire, biomarkers, transcript = await asyncio.gather(
        _fetch_questionnaire(),
        _fetch_biomarkers(),
        _fetch_transcript(),
    )
    bundle = FetchBundle(
        results={
            "questionnaire": questionnaire,
            "biomarkers": biomarkers,
            "transcript": transcript,
        },
        notes=[questionnaire, biomarkers, transcript],
    )
    return bundle


@dataclass
class Start(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> "ResultsGate":
        await asyncio.sleep(0.15)
        return ResultsGate()


@dataclass
class ResultsGate(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> "ThreadGate | Escalate":
        await asyncio.sleep(0.2)
        results_available = _flag("CONCIERGE_RESULTS_AVAILABLE", default=True)
        if results_available:
            return ThreadGate()
        return Escalate()


@dataclass
class ThreadGate(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> "Escalate | PlannerLLM":
        await asyncio.sleep(0.2)
        thread_locked = _flag("CONCIERGE_THREAD_LOCKED", default=False)
        if thread_locked:
            return Escalate()
        return PlannerLLM()


@dataclass
class Escalate(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> "Done":
        await asyncio.sleep(0.2)
        return Done(reason="Escalated: lock thread and alert clinician")


@dataclass
class PlannerLLM(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> "FetchAll":
        await asyncio.sleep(0.25)
        return FetchAll()


@dataclass
class FetchAll(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> "AnswerLLM":
        bundle = await _fetch_all()
        return AnswerLLM(bundle=bundle)


@dataclass
class AnswerLLM(BaseNode[None, None, str]):
    bundle: FetchBundle

    async def run(self, ctx: GraphRunContext) -> "AttributionValidation":
        await asyncio.sleep(0.2)
        if self.bundle.results:
            summary = ", ".join(self.bundle.results.values())
            self.bundle.notes.append(f"answer: drafted with {summary}")
        return AttributionValidation()


@dataclass
class AttributionValidation(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> "Done":
        await asyncio.sleep(0.2)
        return Done(reason="Response ready with attributions")


@dataclass
class Done(BaseNode[None, None, str]):
    reason: str = "Completed"

    async def run(self, ctx: GraphRunContext) -> End[str]:
        await asyncio.sleep(0.1)
        return End(self.reason)


graph = Graph(nodes=[
    Start,
    ResultsGate,
    ThreadGate,
    Escalate,
    PlannerLLM,
    FetchAll,
    AnswerLLM,
    AttributionValidation,
    Done,
])
