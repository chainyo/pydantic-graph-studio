from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from pydantic_graph import BaseNode, End, Graph, GraphRunContext

from pydantic_graph_studio.runtime import resolve_interaction


def _tool_lookup(query: str) -> str:
    return f"tool result for '{query}'"


def _interaction(ctx: GraphRunContext) -> Any:
    return resolve_interaction(getattr(ctx, "deps", None))


@dataclass
class Start(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> CallTool:
        await asyncio.sleep(0.1)
        return CallTool(query="status check")


@dataclass
class CallTool(BaseNode[None, None, str]):
    query: str

    async def run(self, ctx: GraphRunContext) -> Summarize:
        interaction = _interaction(ctx)
        call_id = None
        if interaction is not None:
            call_id = await interaction.emit_tool_call(
                node_id=self.get_node_id(),
                tool_name="status_lookup",
                arguments={"query": self.query},
            )
        await asyncio.sleep(0.2)
        result = _tool_lookup(self.query)
        if interaction is not None and call_id is not None:
            await interaction.emit_tool_result(
                node_id=self.get_node_id(),
                tool_name="status_lookup",
                call_id=call_id,
                output={"result": result},
                success=True,
            )
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
