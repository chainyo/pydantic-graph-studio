from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, cast

from fastapi.testclient import TestClient
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

from pydantic_graph_studio.runtime import resolve_interaction
from pydantic_graph_studio.server import create_app


@dataclass
class Start(BaseNode[None, None, int]):
    async def run(self, ctx: GraphRunContext) -> Next:
        return Next()


@dataclass
class Next(BaseNode[None, None, int]):
    async def run(self, ctx: GraphRunContext) -> End[int]:
        return End(1)


@dataclass
class AwaitApproval(BaseNode[None, None, int]):
    async def run(self, ctx: GraphRunContext) -> End[int]:
        interaction = resolve_interaction(ctx.deps)
        assert interaction is not None
        choice = await interaction.request_input(
            node_id=self.get_node_id(),
            prompt="Approve this run?",
            options=["yes", "no"],
        )
        return End(1 if choice == "yes" else 0)


def _make_client() -> TestClient:
    nodes: list[type[BaseNode[None, None, int]]] = [Start, Next]
    graph = Graph[None, None, int](nodes=nodes)
    app = create_app(graph, Start())
    return TestClient(app)


def _make_interactive_client() -> TestClient:
    nodes: list[type[BaseNode[None, None, int]]] = [AwaitApproval]
    graph = Graph[None, None, int](nodes=nodes)
    app = create_app(graph, AwaitApproval())
    return TestClient(app)


def test_api_graph_returns_payload() -> None:
    with _make_client() as client:
        response = client.get("/api/graph")
        assert response.status_code == 200
        payload = response.json()
        assert "nodes" in payload
        assert "edges" in payload
        assert payload["entry_nodes"] == [Start.get_node_id()]


def test_start_run_and_stream_events() -> None:
    with _make_client() as client:
        run_response = client.post("/api/run")
        assert run_response.status_code == 200
        run_id = run_response.json()["run_id"]

        events: list[dict[str, object]] = []
        with client.stream("GET", f"/api/events?run_id={run_id}") as response:
            assert response.status_code == 200
            content_type = response.headers.get("content-type", "")
            assert content_type.startswith("text/event-stream")
            assert response.headers.get("cache-control") == "no-cache"
            for line in response.iter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    payload = json.loads(line[len("data: ") :])
                    events.append(payload)
                    if payload["event_type"] in {"run_end", "error"}:
                        break

        event_types = [event["event_type"] for event in events]
        assert event_types == [
            "node_start",
            "node_end",
            "edge_taken",
            "node_start",
            "node_end",
            "run_end",
        ]
        assert {event["run_id"] for event in events} == {run_id}


def test_events_unknown_run_id_returns_404() -> None:
    with _make_client() as client:
        response = client.get("/api/events?run_id=missing")
        assert response.status_code == 404


def test_input_unknown_run_id_returns_404() -> None:
    with _make_client() as client:
        response = client.post(
            "/api/input",
            json={"run_id": "missing", "request_id": "req", "response": "yes"},
        )
        assert response.status_code == 404


def test_interactive_input_flow() -> None:
    with _make_interactive_client() as client:
        run_response = client.post("/api/run")
        assert run_response.status_code == 200
        run_id = run_response.json()["run_id"]
        app = cast(Any, client.app)
        run_state = app.state.registry._runs[run_id]

        deadline = time.monotonic() + 2.0
        request_id = None
        while time.monotonic() < deadline:
            pending = list(run_state.interaction._pending.keys())
            if pending:
                request_id = pending[0]
                break
            time.sleep(0.01)

        assert request_id is not None

        wrong = client.post(
            "/api/input",
            json={
                "run_id": run_id,
                "request_id": "wrong-request",
                "response": "yes",
            },
        )
        assert wrong.status_code == 400

        submit = client.post(
            "/api/input",
            json={
                "run_id": run_id,
                "request_id": request_id,
                "response": "yes",
            },
        )
        assert submit.status_code == 200
        assert submit.json() == {"accepted": True}

        events: list[dict[str, object]] = []
        with client.stream("GET", f"/api/events?run_id={run_id}") as response:
            assert response.status_code == 200
            for line in response.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                payload = json.loads(line[len("data: ") :])
                events.append(payload)
                if payload["event_type"] in {"run_end", "error"}:
                    break

        event_types = [event["event_type"] for event in events]
        assert "input_request" in event_types
        assert "input_response" in event_types
        assert event_types[-1] == "run_end"


def test_index_route_serves_html() -> None:
    with _make_client() as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "<html" in response.text.lower()
