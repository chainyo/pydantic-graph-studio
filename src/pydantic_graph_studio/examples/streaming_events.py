from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

from pydantic_graph import BaseNode, End, Graph, GraphRunContext


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return max(1, int(raw))
    except ValueError:
        return default


MAX_TICKS = _int_env("STREAMING_TICKS", default=5)


@dataclass
class Start(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> Tick:
        await asyncio.sleep(0.1)
        return Tick(count=1)


@dataclass
class Tick(BaseNode[None, None, str]):
    count: int

    async def run(self, ctx: GraphRunContext) -> Tick | Done:
        await asyncio.sleep(0.15)
        if self.count >= MAX_TICKS:
            return Done(total=self.count)
        return Tick(count=self.count + 1)


@dataclass
class Done(BaseNode[None, None, str]):
    total: int

    async def run(self, ctx: GraphRunContext) -> End[str]:
        await asyncio.sleep(0.1)
        return End(f"streamed {self.total} ticks")


NODE_TYPES: list[type[BaseNode[None, None, str]]] = [Start, Tick, Done]
graph: Graph[None, None, str] = Graph[None, None, str](nodes=NODE_TYPES)
