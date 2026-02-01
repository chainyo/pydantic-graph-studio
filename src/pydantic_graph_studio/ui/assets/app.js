(() => {
  const e = React.createElement;
  const { useEffect, useMemo, useRef, useState } = React;
  const RF = ReactFlow;
  const {
    ReactFlow: Flow,
    Background,
    Controls,
    MiniMap,
    useEdgesState,
    useNodesState,
  } = RF;

  const statusClasses = {
    idle: "border-slate-700 bg-slate-900 text-slate-100",
    active: "border-sky-400 bg-sky-900/40 text-sky-100",
    done: "border-emerald-400 bg-emerald-900/40 text-emerald-100",
    error: "border-rose-400 bg-rose-900/40 text-rose-100",
  };

  const edgeBaseStyle = {
    stroke: "#64748b",
    strokeWidth: 1.5,
  };

  const edgeActiveStyle = {
    stroke: "#38bdf8",
    strokeWidth: 2.5,
  };

  const badgeBase =
    "inline-flex items-center rounded-full border border-slate-600 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide";

  const nodeBase = "rounded-lg border px-3 py-2 shadow-sm";

  function StudioNode({ data }) {
    const statusClass = statusClasses[data.status || "idle"] || statusClasses.idle;
    const badges = [];
    if (data.isEntry) {
      badges.push(
        e("span", { className: `${badgeBase} text-sky-200` }, "Entry"),
      );
    }
    if (data.isTerminal) {
      badges.push(
        e("span", { className: `${badgeBase} text-emerald-200` }, "Terminal"),
      );
    }
    if (data.isDynamic) {
      badges.push(
        e("span", { className: `${badgeBase} text-amber-200` }, "Dynamic"),
      );
    }

    return e(
      "div",
      { className: `${nodeBase} ${statusClass}` },
      e("div", { className: "text-sm font-semibold" }, data.label || data.id),
      badges.length
        ? e(
            "div",
            { className: "mt-2 flex flex-wrap gap-2" },
            badges,
          )
        : null,
    );
  }

  const nodeTypes = { studio: StudioNode };

  function buildFlowGraph(graph) {
    const nodes = [];
    const edges = [];
    const positions = new Map();
    const dynamicNodesBySource = new Map();
    const count = graph.nodes.length || 1;
    const columns = Math.max(1, Math.ceil(Math.sqrt(count)));
    const gapX = 260;
    const gapY = 160;

    graph.nodes.forEach((node, index) => {
      const position = {
        x: (index % columns) * gapX,
        y: Math.floor(index / columns) * gapY,
      };
      positions.set(node.node_id, position);
      nodes.push({
        id: node.node_id,
        type: "studio",
        position,
        data: {
          id: node.node_id,
          label: node.label || node.node_id,
          status: "idle",
          isEntry: graph.entry_nodes.includes(node.node_id),
          isTerminal: graph.terminal_nodes.includes(node.node_id),
        },
      });
    });

    graph.edges.forEach((edge, index) => {
      let target = edge.target_node_id;
      if (!target) {
        let dynamicId = dynamicNodesBySource.get(edge.source_node_id);
        if (!dynamicId) {
          dynamicId = `dynamic-${edge.source_node_id}`;
          dynamicNodesBySource.set(edge.source_node_id, dynamicId);
          const sourcePosition = positions.get(edge.source_node_id) || { x: 0, y: 0 };
          nodes.push({
            id: dynamicId,
            type: "studio",
            position: {
              x: sourcePosition.x + gapX * 0.7,
              y: sourcePosition.y + gapY * 0.4,
            },
            data: {
              id: dynamicId,
              label: "Dynamic target",
              status: "idle",
              isDynamic: true,
            },
          });
        }
        target = dynamicId;
      }

      edges.push({
        id: `e-${edge.source_node_id}-${target}-${index}`,
        source: edge.source_node_id,
        target,
        animated: false,
        style: {
          ...edgeBaseStyle,
          ...(edge.dynamic ? { strokeDasharray: "4 3" } : null),
        },
        data: {
          dynamic: edge.dynamic,
        },
      });
    });

    return { nodes, edges };
  }

  function App() {
    const [graph, setGraph] = useState(null);
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [status, setStatus] = useState({ phase: "idle", runId: null, error: null });
    const eventSourceRef = useRef(null);

    const statusLabel = useMemo(() => {
      if (status.phase === "running") return `Running ${status.runId || ""}`.trim();
      if (status.phase === "error") return "Error";
      if (status.phase === "loading") return "Loading";
      if (status.phase === "ready") return "Ready";
      return "Idle";
    }, [status]);

    useEffect(() => {
      let active = true;

      const load = async () => {
        setStatus((current) => ({ ...current, phase: "loading", error: null }));
        try {
          const response = await fetch("/api/graph");
          if (!response.ok) {
            throw new Error(`Failed to load graph (${response.status})`);
          }
          const data = await response.json();
          if (!active) return;
          const { nodes: nextNodes, edges: nextEdges } = buildFlowGraph(data);
          setGraph(data);
          setNodes(nextNodes);
          setEdges(nextEdges);
          setStatus((current) => ({ ...current, phase: "ready", error: null }));
        } catch (error) {
          if (!active) return;
          setStatus({ phase: "error", runId: null, error: error.message });
        }
      };

      load();

      return () => {
        active = false;
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
      };
    }, [setNodes, setEdges]);

    const resetRunVisuals = () => {
      setNodes((current) =>
        current.map((node) => ({
          ...node,
          data: { ...node.data, status: "idle" },
        })),
      );
      setEdges((current) =>
        current.map((edge) => ({
          ...edge,
          animated: false,
          style: {
            ...edge.style,
            ...edgeBaseStyle,
            ...(edge.data?.dynamic ? { strokeDasharray: "4 3" } : null),
          },
        })),
      );
    };

    const handleEvent = (payload) => {
      switch (payload.event_type) {
        case "node_start":
          setNodes((current) =>
            current.map((node) =>
              node.id === payload.node_id
                ? { ...node, data: { ...node.data, status: "active" } }
                : node,
            ),
          );
          break;
        case "node_end":
          setNodes((current) =>
            current.map((node) =>
              node.id === payload.node_id
                ? { ...node, data: { ...node.data, status: "done" } }
                : node,
            ),
          );
          break;
        case "edge_taken":
          setEdges((current) =>
            current.map((edge) => {
              if (edge.source !== payload.source_node_id) {
                return edge;
              }
              if (payload.target_node_id && edge.target !== payload.target_node_id) {
                return edge;
              }
              if (!payload.target_node_id && !edge.data?.dynamic) {
                return edge;
              }
              return {
                ...edge,
                animated: true,
                style: { ...edge.style, ...edgeActiveStyle },
              };
            }),
          );
          break;
        case "run_end":
          setStatus((current) => ({ ...current, phase: "ready" }));
          if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
          }
          break;
        case "error":
          if (payload.node_id) {
            setNodes((current) =>
              current.map((node) =>
                node.id === payload.node_id
                  ? { ...node, data: { ...node.data, status: "error" } }
                  : node,
              ),
            );
          }
          setStatus((current) => ({
            ...current,
            phase: "error",
            error: payload.message || "Execution error",
          }));
          if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
          }
          break;
        default:
          break;
      }
    };

    const startRun = async () => {
      if (!graph || status.phase === "loading") {
        return;
      }
      resetRunVisuals();
      setStatus((current) => ({ ...current, phase: "running", error: null }));
      try {
        const response = await fetch("/api/run", { method: "POST" });
        if (!response.ok) {
          throw new Error(`Failed to start run (${response.status})`);
        }
        const payload = await response.json();
        const runId = payload.run_id;
        setStatus((current) => ({ ...current, runId, phase: "running" }));
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
        }
        const stream = new EventSource(`/api/events?run_id=${runId}`);
        eventSourceRef.current = stream;
        stream.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            handleEvent(data);
          } catch (error) {
            setStatus((current) => ({
              ...current,
              phase: "error",
              error: "Malformed event payload",
            }));
          }
        };
        stream.onerror = () => {
          setStatus((current) => ({
            ...current,
            phase: current.phase === "running" ? "error" : current.phase,
            error: current.phase === "running" ? "Event stream disconnected" : current.error,
          }));
          stream.close();
          eventSourceRef.current = null;
        };
      } catch (error) {
        setStatus((current) => ({
          ...current,
          phase: "error",
          error: error.message,
        }));
      }
    };

    const content = graph
      ? e(
          Flow,
          {
            nodes,
            edges,
            onNodesChange,
            onEdgesChange,
            nodeTypes,
            fitView: true,
            minZoom: 0.2,
          },
          e(Background, { variant: RF.BackgroundVariant.Dots, gap: 22, size: 1 }),
          e(Controls, { position: "top-right" }),
          e(MiniMap, { position: "bottom-right" }),
        )
      : e(
          "div",
          { className: "flex h-full items-center justify-center text-slate-400" },
          status.error || "Loading graph…",
        );

    return e(
      "div",
      { className: "flex h-full flex-col" },
      e(
        "header",
        { className: "flex items-center justify-between border-b border-slate-800 px-6 py-4" },
        e(
          "div",
          { className: "space-y-1" },
          e("h1", { className: "text-lg font-semibold" }, "Pydantic Graph Studio"),
          e(
            "p",
            { className: "text-xs uppercase tracking-[0.2em] text-slate-400" },
            statusLabel,
          ),
        ),
        e(
          "div",
          { className: "flex items-center gap-3" },
          status.error
            ? e(
                "span",
                { className: "text-xs text-rose-300" },
                status.error,
              )
            : null,
          e(
            "button",
            {
              className:
                "rounded-md bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 shadow transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400",
              onClick: startRun,
              disabled: status.phase === "loading" || status.phase === "running",
            },
            status.phase === "running" ? "Running…" : "Run",
          ),
        ),
      ),
      e(
        "main",
        { className: "flex-1" },
        content,
      ),
    );
  }

  const rootEl = document.getElementById("root");
  if (ReactDOM.createRoot) {
    ReactDOM.createRoot(rootEl).render(e(App));
  } else {
    ReactDOM.render(e(App), rootEl);
  }
})();
