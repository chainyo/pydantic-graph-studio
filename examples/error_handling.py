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


@dataclass
class Start(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> Validate:
        await asyncio.sleep(0.15)
        return Validate()


@dataclass
class Validate(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> HandleError | Process:
        await asyncio.sleep(0.25)
        if _flag("ERROR_HANDLING_FAIL", default=True):
            return HandleError(reason="Validation failed")
        return Process()


@dataclass
class HandleError(BaseNode[None, None, str]):
    reason: str

    async def run(self, ctx: GraphRunContext) -> Recover:
        await asyncio.sleep(0.2)
        return Recover(message=f"Recovered after error: {self.reason}")


@dataclass
class Recover(BaseNode[None, None, str]):
    message: str

    async def run(self, ctx: GraphRunContext) -> End[str]:
        await asyncio.sleep(0.2)
        return End(self.message)


@dataclass
class Process(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> End[str]:
        await asyncio.sleep(0.2)
        return End("Processed successfully")


NODE_TYPES: list[type[BaseNode[None, None, str]]] = [Start, Validate, HandleError, Recover, Process]
graph: Graph[None, None, str] = Graph[None, None, str](nodes=NODE_TYPES)
