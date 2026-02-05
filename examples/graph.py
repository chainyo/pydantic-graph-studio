from __future__ import annotations

import asyncio
from dataclasses import dataclass

from pydantic_graph import BaseNode, End, Graph, GraphRunContext

MAX_STEPS = 4


@dataclass
class Start(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> Decide:
        await asyncio.sleep(0.2)
        return Decide(step=1)


@dataclass
class Decide(BaseNode[None, None, str]):
    step: int

    async def run(self, ctx: GraphRunContext) -> Loop | Done:
        await asyncio.sleep(0.3)
        if self.step >= MAX_STEPS:
            return Done(message=f"done after {self.step} steps")
        return Loop(next_step=self.step + 1)


@dataclass
class Loop(BaseNode[None, None, str]):
    next_step: int

    async def run(self, ctx: GraphRunContext) -> Decide:
        await asyncio.sleep(0.2)
        return Decide(step=self.next_step)


@dataclass
class Done(BaseNode[None, None, str]):
    message: str

    async def run(self, ctx: GraphRunContext) -> End[str]:
        await asyncio.sleep(0.1)
        return End(self.message)


NODE_TYPES: list[type[BaseNode[None, None, str]]] = [Start, Decide, Loop, Done]
graph: Graph[None, None, str] = Graph[None, None, str](nodes=NODE_TYPES)
