from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any

from pydantic_graph import BaseNode, End, Graph, GraphRunContext

from pydantic_graph_studio.runtime import resolve_interaction


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return max(1, int(raw))
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return max(0.1, float(raw))
    except ValueError:
        return default


MAX_TICKS = _int_env("STREAMING_TICKS", default=5)
CHUNK_DELAY_SECONDS = _float_env("STREAMING_CHUNK_DELAY_SECONDS", default=3.0)


def _interaction(ctx: GraphRunContext) -> Any:
    return resolve_interaction(getattr(ctx, "deps", None))


@dataclass
class Start(BaseNode[None, None, str]):
    async def run(self, ctx: GraphRunContext) -> Tick:
        await asyncio.sleep(0.1)
        return Tick(count=1)


@dataclass
class Tick(BaseNode[None, None, str]):
    count: int

    async def run(self, ctx: GraphRunContext) -> Tick | Done:
        interaction = _interaction(ctx)
        call_id = None
        if interaction is not None:
            call_id = await interaction.emit_tool_call(
                node_id=self.get_node_id(),
                tool_name="stream_chunk",
                arguments={"tick": self.count, "total": MAX_TICKS},
            )
        await asyncio.sleep(CHUNK_DELAY_SECONDS)
        chunk = f"Chunk {self.count}: lorem ipsum event payload"
        if interaction is not None and call_id is not None:
            await interaction.emit_tool_result(
                node_id=self.get_node_id(),
                tool_name="stream_chunk",
                call_id=call_id,
                output={
                    "tick": self.count,
                    "total": MAX_TICKS,
                    "chunk": chunk,
                    "is_final": self.count >= MAX_TICKS,
                },
                success=True,
            )
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
