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


MAX_RETRIES = _int_env("HITL_MAX_RETRIES", default=1)


@dataclass
class Start(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> Review:
        await asyncio.sleep(0.1)
        return Review(attempt=0)


@dataclass
class Review(BaseNode[None, None, str]):
    attempt: int

    async def run(self, ctx: GraphRunContext) -> RequestInput | Finalize:
        await asyncio.sleep(0.2)
        if _flag("HITL_APPROVED", default=False) or self.attempt >= MAX_RETRIES:
            return Finalize(message="Approved by human")
        return RequestInput(next_attempt=self.attempt + 1)


@dataclass
class RequestInput(BaseNode[None, None, str]):
    next_attempt: int

    async def run(self, ctx: GraphRunContext) -> Review:
        await asyncio.sleep(0.25)
        return Review(attempt=self.next_attempt)


@dataclass
class Finalize(BaseNode[None, None, str]):
    message: str

    async def run(self, ctx: GraphRunContext) -> End[str]:
        await asyncio.sleep(0.2)
        return End(self.message)


NODE_TYPES: list[type[BaseNode[None, None, str]]] = [Start, Review, RequestInput, Finalize]
graph: Graph[None, None, str] = Graph[None, None, str](nodes=NODE_TYPES)
