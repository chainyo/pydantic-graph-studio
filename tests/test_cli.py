from __future__ import annotations

import importlib.util
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

from pydantic_graph_studio import cli
from pydantic_graph_studio.cli import (
    CLIError,
    _has_explicit_port,
    _load_graph,
    _load_module,
    _parse_args,
    _parse_example_args,
    _parse_graph_ref,
    _resolve_attribute,
    _resolve_start_node,
    _run_server,
    _select_port,
)


@dataclass
class Alpha(BaseNode[None, None, int]):
    async def run(self, ctx: GraphRunContext) -> End[int]:
        return End(1)


@dataclass
class Beta(BaseNode[None, None, int]):
    async def run(self, ctx: GraphRunContext) -> End[int]:
        return End(2)


@dataclass
class NeedsArgs(BaseNode[None, None, int]):
    value: int

    async def run(self, ctx: GraphRunContext) -> End[int]:
        return End(self.value)


def test_parse_graph_ref_requires_colon() -> None:
    with pytest.raises(CLIError, match="module:var"):
        _parse_graph_ref("missing")


def test_parse_graph_ref_requires_target_and_attr() -> None:
    with pytest.raises(CLIError, match="include both target and attribute"):
        _parse_graph_ref(":attr")
    with pytest.raises(CLIError, match="include both target and attribute"):
        _parse_graph_ref("mod:")


def test_parse_args_defaults() -> None:
    args = _parse_args(["module:graph"])
    assert args.graph_ref == "module:graph"
    assert args.host == "127.0.0.1"
    assert args.port == 8000
    assert args.start is None
    assert args.no_open is False


def test_parse_args_overrides() -> None:
    args = _parse_args(["module:graph", "--host", "0.0.0.0", "--port", "9000", "--start", "Start", "--no-open"])
    assert args.host == "0.0.0.0"
    assert args.port == 9000
    assert args.start == "Start"
    assert args.no_open is True


def test_parse_example_args_defaults() -> None:
    args = _parse_example_args(["graph"])
    assert args.name == "graph"
    assert args.host == "127.0.0.1"
    assert args.port == 8000
    assert args.no_open is False


def test_has_explicit_port() -> None:
    assert _has_explicit_port(["--port", "9000"]) is True
    assert _has_explicit_port(["--port=9001"]) is True
    assert _has_explicit_port(["--host", "0.0.0.0"]) is False


def test_select_port_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_available(host: str, port: int) -> bool:
        return port == 8001

    monkeypatch.setattr(cli, "_is_port_available", fake_available)
    selected = _select_port("127.0.0.1", 8000, allow_fallback=True)
    assert selected == 8001


def test_select_port_no_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "_is_port_available", lambda *args, **kwargs: False)
    with pytest.raises(CLIError, match="already in use"):
        _select_port("127.0.0.1", 8000, allow_fallback=False)


def test_load_module_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.py"
    with pytest.raises(CLIError, match="File not found"):
        _load_module(str(missing))


def test_load_module_rejects_non_python_file(tmp_path: Path) -> None:
    path = tmp_path / "graph.txt"
    path.write_text("value = 1", encoding="utf-8")
    with pytest.raises(CLIError, match="must point to a .py file"):
        _load_module(str(path))


def test_load_module_module_not_found() -> None:
    with pytest.raises(CLIError, match="Module not found"):
        _load_module("does_not_exist_anywhere")


def test_load_module_imports_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module_path = tmp_path / "graph_mod.py"
    module_path.write_text("value = 41\n", encoding="utf-8")
    monkeypatch.syspath_prepend(tmp_path)
    module = _load_module("graph_mod")
    assert module.value == 41


def test_load_module_from_file_success(tmp_path: Path) -> None:
    module_path = tmp_path / "graph_file.py"
    module_path.write_text("value = 7\n", encoding="utf-8")
    module = _load_module(str(module_path))
    assert module.value == 7


def test_load_module_from_file_spec_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module_path = tmp_path / "graph_fail.py"
    module_path.write_text("value = 9\n", encoding="utf-8")
    monkeypatch.setattr(importlib.util, "spec_from_file_location", lambda *args, **kwargs: None)
    with pytest.raises(CLIError, match="Unable to load module from file"):
        _load_module(str(module_path))


def test_load_graph_requires_graph_instance(tmp_path: Path) -> None:
    module_path = tmp_path / "bad_graph.py"
    module_path.write_text("value = 123\n", encoding="utf-8")
    with pytest.raises(CLIError, match="Graph reference did not resolve"):
        _load_graph(f"{module_path}:value")


def test_load_graph_success_from_file(tmp_path: Path) -> None:
    module_path = tmp_path / "graph_ok.py"
    module_path.write_text(
        """
from dataclasses import dataclass
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

@dataclass
class Start(BaseNode[None, None, int]):
    async def run(self, ctx: GraphRunContext) -> End[int]:
        return End(1)

graph = Graph(nodes=[Start])
""".strip()
        + "\n",
        encoding="utf-8",
    )
    graph = _load_graph(f"{module_path}:graph")
    assert isinstance(graph, Graph)


def test_resolve_attribute_missing() -> None:
    module = types.SimpleNamespace(value=123)
    with pytest.raises(CLIError, match="Attribute 'missing'"):
        _resolve_attribute(module, "missing")


def test_resolve_start_node_unknown_start() -> None:
    nodes: list[type[BaseNode[None, None, int]]] = [Alpha, Beta]
    graph = Graph[None, None, int](nodes=nodes)
    with pytest.raises(CLIError, match="Unknown start node"):
        _resolve_start_node(graph, "unknown")


def test_resolve_start_node_empty_graph() -> None:
    graph = Graph[None, None, int](nodes=[])
    with pytest.raises(CLIError, match="Graph contains no nodes"):
        _resolve_start_node(graph, None)


def test_resolve_start_node_multiple_entries() -> None:
    nodes: list[type[BaseNode[None, None, int]]] = [Alpha, Beta]
    graph = Graph[None, None, int](nodes=nodes)
    with pytest.raises(CLIError, match="Multiple entry nodes"):
        _resolve_start_node(graph, None)


def test_resolve_start_node_infer_single_entry() -> None:
    nodes: list[type[BaseNode[None, None, int]]] = [Alpha]
    graph = Graph[None, None, int](nodes=nodes)
    start_node = _resolve_start_node(graph, None)
    assert isinstance(start_node, Alpha)


def test_resolve_start_node_infer_none_entry() -> None:
    @dataclass
    class LoopA(BaseNode[None, None, int]):
        async def run(self, ctx: GraphRunContext) -> LoopB:
            return LoopB()

    @dataclass
    class LoopB(BaseNode[None, None, int]):
        async def run(self, ctx: GraphRunContext) -> LoopA:
            return LoopA()

    nodes: list[type[BaseNode[None, None, int]]] = [LoopA, LoopB]
    graph = Graph[None, None, int](nodes=nodes)
    with pytest.raises(CLIError, match="Unable to infer an entry node"):
        _resolve_start_node(graph, None)


def test_resolve_start_node_returns_instance() -> None:
    nodes: list[type[BaseNode[None, None, int]]] = [Alpha]
    graph = Graph[None, None, int](nodes=nodes)
    node_def = graph.node_defs[Alpha.get_node_id()]
    node_def_any = cast(Any, node_def)
    node_def_any.node = Alpha()
    start_node = _resolve_start_node(graph, Alpha.get_node_id())
    assert isinstance(start_node, Alpha)


def test_resolve_start_node_requires_no_args() -> None:
    nodes: list[type[BaseNode[None, None, int]]] = [NeedsArgs]
    graph = Graph[None, None, int](nodes=nodes)
    with pytest.raises(CLIError, match="Failed to instantiate"):
        _resolve_start_node(graph, None)


def test_run_server_rejects_invalid_port() -> None:
    nodes: list[type[BaseNode[None, None, int]]] = [Alpha]
    graph = Graph[None, None, int](nodes=nodes)
    with pytest.raises(CLIError, match="Port must be between"):
        _run_server(graph, Alpha(), host="127.0.0.1", port=0, open_browser=False)


def test_run_server_imports_uvicorn(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    nodes: list[type[BaseNode[None, None, int]]] = [Alpha]
    graph = Graph[None, None, int](nodes=nodes)

    called: dict[str, object] = {}

    def fake_run(app: object, host: str, port: int, log_level: str) -> None:
        called["app"] = app
        called["host"] = host
        called["port"] = port
        called["log_level"] = log_level

    monkeypatch.setitem(sys.modules, "uvicorn", types.SimpleNamespace(run=fake_run))
    _run_server(graph, Alpha(), host="127.0.0.1", port=8001, open_browser=False)

    assert called["host"] == "127.0.0.1"
    assert called["port"] == 8001
    assert called["log_level"] == "info"
    out = capsys.readouterr().out
    assert "Studio running at http://127.0.0.1:8001" in out


def test_run_server_missing_uvicorn(monkeypatch: pytest.MonkeyPatch) -> None:
    nodes: list[type[BaseNode[None, None, int]]] = [Alpha]
    graph = Graph[None, None, int](nodes=nodes)
    monkeypatch.setitem(sys.modules, "uvicorn", None)
    with pytest.raises(CLIError, match="uvicorn is required"):
        _run_server(graph, Alpha(), host="127.0.0.1", port=8002, open_browser=False)


def test_main_happy_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module_path = tmp_path / "main_graph.py"
    module_path.write_text(
        """
from dataclasses import dataclass
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

@dataclass
class Start(BaseNode[None, None, int]):
    async def run(self, ctx: GraphRunContext) -> End[int]:
        return End(1)

graph = Graph(nodes=[Start])
""".strip()
        + "\n",
        encoding="utf-8",
    )

    called: dict[str, object] = {}

    def fake_run_server(
        graph: object,
        start_node: object,
        host: str,
        port: int,
        open_browser: bool,
    ) -> None:
        called["graph"] = graph
        called["start_node"] = start_node
        called["host"] = host
        called["port"] = port
        called["open_browser"] = open_browser

    monkeypatch.setattr(cli, "_run_server", fake_run_server)
    cli.main([f"{module_path}:graph", "--host", "0.0.0.0", "--port", "9001", "--no-open"])

    assert called["host"] == "0.0.0.0"
    assert called["port"] == 9001
    assert called["open_browser"] is False


def test_main_example_list(capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["example", "list"])
    out = capsys.readouterr().out
    assert "graph" in out


def test_main_example_run(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, object] = {}

    def fake_run_server(
        graph: object,
        start_node: object,
        host: str,
        port: int,
        open_browser: bool,
    ) -> None:
        called["host"] = host
        called["port"] = port
        called["open_browser"] = open_browser

    monkeypatch.setattr(cli, "_run_server", fake_run_server)
    monkeypatch.setattr(cli, "_select_port", lambda *args, **kwargs: 8010)
    cli.main(["example", "graph", "--no-open"])

    assert called["host"] == "127.0.0.1"
    assert called["port"] == 8010
    assert called["open_browser"] is False


def test_main_example_unknown(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["example", "nope"])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "Unknown example" in captured.err


def test_main_error_prints_and_exits(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["badref"])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "error: Graph reference must be in the form module:var or path.py:var" in captured.err
