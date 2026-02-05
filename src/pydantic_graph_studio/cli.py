"""Command-line entrypoint for launching the studio server."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import socket
import sys
import threading
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic_graph import Graph
from pydantic_graph.nodes import BaseNode

from pydantic_graph_studio.introspection import build_graph_model
from pydantic_graph_studio.server import create_app

from . import examples

BetaGraph: type[Any] | None = None
try:  # pragma: no cover - optional beta support
    from pydantic_graph.beta.graph import Graph as _BetaGraph
except ModuleNotFoundError:  # pragma: no cover
    pass
else:
    BetaGraph = _BetaGraph


@dataclass(slots=True)
class GraphRef:
    target: str
    attribute: str


class CLIError(RuntimeError):
    """Raised for user-facing CLI errors."""


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint for the `pgraph` launcher."""

    args_list = list(argv) if argv is not None else sys.argv[1:]
    try:
        if args_list and args_list[0] == "example":
            _run_example_command(args_list[1:])
            return

        args = _parse_args(args_list)
        graph = _load_graph(args.graph_ref)
        start_node = _resolve_start_node(graph, args.start)
        port = _select_port(args.host, args.port, allow_fallback=not _has_explicit_port(args_list))
        _run_server(graph, start_node, host=args.host, port=port, open_browser=not args.no_open)
    except CLIError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pgraph",
        description="Launch the local Pydantic Graph Studio for a graph reference.",
    )
    parser.add_argument(
        "graph_ref",
        help="Graph reference in the form module:var or path.py:var",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind the local server (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the local server (default: 8000)",
    )
    parser.add_argument(
        "--start",
        help="Explicit node id to use as the entry point",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Disable automatically opening the browser",
    )
    return parser.parse_args(argv)


def _parse_example_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pgraph example",
        description="Launch the local studio with a built-in example graph.",
    )
    parser.add_argument(
        "name",
        nargs="?",
        help="Example name or 'list' to show available examples",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind the local server (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the local server (default: 8000)",
    )
    parser.add_argument(
        "--start",
        help="Explicit node id to use as the entry point",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Disable automatically opening the browser",
    )
    return parser.parse_args(argv)


def _run_example_command(argv: list[str]) -> None:
    args = _parse_example_args(argv)
    if args.name is None or args.name == "list":
        _print_examples()
        return

    try:
        example = examples.get_example(args.name)
    except KeyError as exc:
        available = ", ".join(spec.name for spec in examples.list_examples())
        raise CLIError(f"Unknown example '{args.name}'. Available examples: {available}") from exc

    graph = example.loader()
    start_node = _resolve_start_node(graph, args.start)
    port = _select_port(args.host, args.port, allow_fallback=not _has_explicit_port(argv))
    _run_server(graph, start_node, host=args.host, port=port, open_browser=not args.no_open)


def _print_examples() -> None:
    for spec in examples.list_examples():
        print(f"{spec.name} - {spec.description}")


def _has_explicit_port(argv: list[str]) -> bool:
    for arg in argv:
        if arg == "--port" or arg.startswith("--port="):
            return True
    return False


def _load_graph(graph_ref: str) -> Any:
    parsed = _parse_graph_ref(graph_ref)
    module = _load_module(parsed.target)
    graph = _resolve_attribute(module, parsed.attribute)
    if not isinstance(graph, Graph) and not _is_beta_graph(graph):
        raise CLIError(
            "Graph reference did not resolve to a Graph instance. "
            "Ensure the reference points to a pydantic_graph.Graph object."
        )
    return graph


def _parse_graph_ref(graph_ref: str) -> GraphRef:
    if ":" not in graph_ref:
        raise CLIError("Graph reference must be in the form module:var or path.py:var")
    target, attribute = graph_ref.rsplit(":", 1)
    if not target or not attribute:
        raise CLIError("Graph reference must include both target and attribute")
    return GraphRef(target=target, attribute=attribute)


def _load_module(target: str) -> Any:
    path = Path(target)
    if _looks_like_path(target):
        if not path.exists():
            raise CLIError(f"File not found: {path}")
        if path.suffix != ".py":
            raise CLIError("File reference must point to a .py file")
        return _load_module_from_file(path)
    try:
        return importlib.import_module(target)
    except ModuleNotFoundError as exc:
        raise CLIError(f"Module not found: {target}") from exc


def _looks_like_path(target: str) -> bool:
    return "/" in target or "\\" in target or target.endswith(".py")


def _load_module_from_file(path: Path) -> Any:
    module_name = f"pgraph_user_{path.stem}_{abs(hash(path))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise CLIError(f"Unable to load module from file: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _resolve_attribute(module: Any, attribute: str) -> Any:
    current: Any = module
    for segment in attribute.split("."):
        if not hasattr(current, segment):
            raise CLIError(f"Attribute '{segment}' not found while resolving '{attribute}'")
        current = getattr(current, segment)
    return current


def _resolve_start_node(
    graph: Any,
    start_node_id: str | None,
) -> BaseNode[Any, Any, Any] | None:
    if _is_beta_graph(graph):
        if start_node_id:
            raise CLIError("Beta graphs use a fixed start node; --start is not supported.")
        return None

    node_defs = graph.node_defs
    if not node_defs:
        raise CLIError("Graph contains no nodes")

    if start_node_id:
        node_def = node_defs.get(start_node_id)
        if node_def is None:
            available = ", ".join(sorted(node_defs.keys()))
            raise CLIError(f"Unknown start node '{start_node_id}'. Available nodes: {available}")
    else:
        entry_nodes = build_graph_model(graph).entry_nodes
        if not entry_nodes:
            raise CLIError("Unable to infer an entry node. Use --start to specify one.")
        if len(entry_nodes) > 1:
            entries = ", ".join(entry_nodes)
            raise CLIError(f"Multiple entry nodes found: {entries}. Use --start to choose one.")
        node_def = node_defs[entry_nodes[0]]

    node_cls_or_instance = node_def.node
    if isinstance(node_cls_or_instance, BaseNode):
        return node_cls_or_instance
    if isinstance(node_cls_or_instance, type) and issubclass(node_cls_or_instance, BaseNode):
        try:
            instance = node_cls_or_instance()
        except TypeError as exc:
            raise CLIError(
                "Failed to instantiate the start node. "
                "Ensure it can be constructed with no arguments or provide a different entry node."
            ) from exc
        return instance

    raise CLIError("Start node did not resolve to a BaseNode instance")


def _run_server(
    graph: Any,
    start_node: BaseNode[Any, Any, Any] | None,
    *,
    host: str,
    port: int,
    open_browser: bool,
) -> None:
    if port <= 0 or port > 65535:
        raise CLIError("Port must be between 1 and 65535")

    app = create_app(graph, start_node)
    try:
        import uvicorn
    except ModuleNotFoundError as exc:
        raise CLIError("uvicorn is required to run the server") from exc

    url = f"http://{host}:{port}"
    print(f"Studio running at {url}")
    if open_browser:
        _open_browser(url)
    uvicorn.run(app, host=host, port=port, log_level="info")


def _is_beta_graph(graph: Any) -> bool:
    return BetaGraph is not None and isinstance(graph, BetaGraph)


def _select_port(host: str, port: int, *, allow_fallback: bool) -> int:
    if _is_port_available(host, port):
        return port
    fallback = port + 1
    if allow_fallback and fallback <= 65535 and _is_port_available(host, fallback):
        return fallback
    raise CLIError(f"Port {port} is already in use. Choose another port with --port.")


def _is_port_available(host: str, port: int) -> bool:
    try:
        with socket.create_server((host, port)) as server:
            server.settimeout(0.1)
            return True
    except OSError:
        return False


def _open_browser(url: str) -> None:
    def _open() -> None:
        try:
            webbrowser.open(url, new=2)
        except Exception:  # pragma: no cover - best effort
            return

    timer = threading.Timer(0.35, _open)
    timer.daemon = True
    timer.start()
