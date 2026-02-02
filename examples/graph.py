from __future__ import annotations

import asyncio
from dataclasses import dataclass

from pydantic_graph import BaseNode, End, Graph, GraphRunContext

MAX_STEPS = 4


@dataclass
class Start(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> "Work":
        await asyncio.sleep(0.2)
        return Work(step=1)


@dataclass
class Work(BaseNode[None, None, str]):
    step: int

    async def run(self, ctx: GraphRunContext) -> "OddStep | EvenStep | Done":
        await asyncio.sleep(0.3)
        if self.step >= MAX_STEPS:
            return Done(message=f"done after {self.step} steps")
        if self.step % 2 == 0:
            return EvenStep(next_step=self.step + 1)
        return OddStep(next_step=self.step + 1)


@dataclass
class OddStep(BaseNode[None, None, str]):
    next_step: int

    async def run(self, ctx: GraphRunContext) -> Work:
        await asyncio.sleep(0.2)
        return Work(step=self.next_step)


@dataclass
class EvenStep(BaseNode[None, None, str]):
    next_step: int

    async def run(self, ctx: GraphRunContext) -> Work:
        await asyncio.sleep(0.2)
        return Work(step=self.next_step)


@dataclass
class Done(BaseNode[None, None, str]):
    message: str

    async def run(self, ctx: GraphRunContext) -> End[str]:
        await asyncio.sleep(0.1)
        return End(self.message)


graph = Graph(nodes=[Start, Work, OddStep, EvenStep, Done])
