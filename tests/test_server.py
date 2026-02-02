from __future__ import annotations

import json
from dataclasses import dataclass

from fastapi.testclient import TestClient
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

from pydantic_graph_studio.server import create_app


@dataclass
class Start(BaseNode[None, None, int]):
    async def run(self, ctx: GraphRunContext) -> Next:
        return Next()


@dataclass
class Next(BaseNode[None, None, int]):
    async def run(self, ctx: GraphRunContext) -> End[int]:
        return End(1)


def _make_client() -> TestClient:
    nodes: list[type[BaseNode[None, None, int]]] = [Start, Next]
    graph = Graph[None, None, int](nodes=nodes)
    app = create_app(graph, Start())
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


def test_index_route_serves_html() -> None:
    with _make_client() as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "<html" in response.text.lower()
