from __future__ import annotations

import asyncio
from dataclasses import dataclass

from pydantic_graph import BaseNode, End, Graph, GraphRunContext


def _tool_lookup(query: str) -> str:
    return f"tool result for '{query}'"


@dataclass
class Start(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> CallTool:
        await asyncio.sleep(0.1)
        return CallTool(query="status check")


@dataclass
class CallTool(BaseNode[None, None, str]):
    query: str

    async def run(self, ctx: GraphRunContext) -> Summarize:
        await asyncio.sleep(0.2)
        result = _tool_lookup(self.query)
        return Summarize(query=self.query, result=result)


@dataclass
class Summarize(BaseNode[None, None, str]):
    query: str
    result: str

    async def run(self, ctx: GraphRunContext) -> End[str]:
        await asyncio.sleep(0.2)
        return End(f"Used tool '{self.query}' -> {self.result}")


NODE_TYPES: list[type[BaseNode[None, None, str]]] = [Start, CallTool, Summarize]
graph: Graph[None, None, str] = Graph[None, None, str](nodes=NODE_TYPES)
