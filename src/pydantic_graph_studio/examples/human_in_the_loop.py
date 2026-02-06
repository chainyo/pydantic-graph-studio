from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any

from pydantic_graph import BaseNode, End, Graph, GraphRunContext

from pydantic_graph_studio.runtime import resolve_interaction


def _flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return max(0, int(raw))
    except ValueError:
        return default


AUTO_APPROVE_AFTER = _int_env("HITL_AUTO_APPROVE_AFTER", default=2)


def _interaction(ctx: GraphRunContext) -> Any:
    return resolve_interaction(getattr(ctx, "deps", None))


def _approved_from_response(response: str) -> bool:
    return response.strip().lower() in {"1", "true", "yes", "y", "approve", "approved"}


def _draft_context() -> str:
    return (
        "Draft summary:\n"
        "- Title: Quarterly Support Trends\n"
        "- Key claim: Ticket resolution time improved by 14%\n"
        "- Open concern: Week 3 had a spike in escalations\n"
        "- Recommendation: Approve publishing with a brief risk note"
    )


@dataclass
class Start(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> Draft:
        await asyncio.sleep(0.1)
        return Draft()


@dataclass
class Draft(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> AwaitApproval:
        await asyncio.sleep(0.2)
        return AwaitApproval(attempt=0, review_context=_draft_context())


@dataclass
class AwaitApproval(BaseNode[None, None, str]):
    attempt: int
    review_context: str

    async def run(self, ctx: GraphRunContext) -> AwaitApproval | Finalize:
        await asyncio.sleep(0.3)
        interaction = _interaction(ctx)
        if interaction is not None:
            response = await interaction.request_input(
                node_id=self.get_node_id(),
                prompt="Approve this run?",
                options=["yes", "no"],
                context=self.review_context,
            )
            if _approved_from_response(response):
                return Finalize(message="Approved by human")
            raise RuntimeError("Rejected by human")
        approved = _flag("HITL_APPROVED", default=False)
        auto_approve = AUTO_APPROVE_AFTER > 0 and self.attempt >= AUTO_APPROVE_AFTER
        if approved or auto_approve:
            return Finalize(message="Approved by human")
        return AwaitApproval(attempt=self.attempt + 1, review_context=self.review_context)


@dataclass
class Finalize(BaseNode[None, None, str]):
    message: str

    async def run(self, ctx: GraphRunContext) -> End[str]:
        await asyncio.sleep(0.2)
        return End(self.message)


NODE_TYPES: list[type[BaseNode[None, None, str]]] = [Start, Draft, AwaitApproval, Finalize]
graph: Graph[None, None, str] = Graph[None, None, str](nodes=NODE_TYPES)
