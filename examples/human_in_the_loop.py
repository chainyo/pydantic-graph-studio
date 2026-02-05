from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

from pydantic_graph import BaseNode, End, Graph, GraphRunContext


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


@dataclass
class Start(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> Draft:
        await asyncio.sleep(0.1)
        return Draft()


@dataclass
class Draft(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> AwaitApproval:
        await asyncio.sleep(0.2)
        return AwaitApproval(attempt=0)


@dataclass
class AwaitApproval(BaseNode[None, None, str]):
    attempt: int

    async def run(self, ctx: GraphRunContext) -> WaitForApproval | Finalize:
        await asyncio.sleep(0.2)
        approved = _flag("HITL_APPROVED", default=False)
        auto_approve = AUTO_APPROVE_AFTER > 0 and self.attempt >= AUTO_APPROVE_AFTER
        if approved or auto_approve:
            return Finalize(message="Approved by human")
        return WaitForApproval(attempt=self.attempt + 1)


@dataclass
class WaitForApproval(BaseNode[None, None, str]):
    attempt: int

    async def run(self, ctx: GraphRunContext) -> AwaitApproval:
        await asyncio.sleep(0.3)
        return AwaitApproval(attempt=self.attempt)


@dataclass
class Finalize(BaseNode[None, None, str]):
    message: str

    async def run(self, ctx: GraphRunContext) -> End[str]:
        await asyncio.sleep(0.2)
        return End(self.message)


NODE_TYPES: list[type[BaseNode[None, None, str]]] = [Start, Draft, AwaitApproval, WaitForApproval, Finalize]
graph: Graph[None, None, str] = Graph[None, None, str](nodes=NODE_TYPES)
