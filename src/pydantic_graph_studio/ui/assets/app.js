(() => {
  const e = React.createElement;
  const { useEffect, useMemo, useRef, useState } = React;
  const RF = ReactFlow;
  const {
    ReactFlow: Flow,
    Background,
    Controls,
    BaseEdge,
    Handle,
    MiniMap,
    getSmoothStepPath,
    useEdgesState,
    useNodesState,
  } = RF;

  const statusClasses = {
    idle: "studio-node--idle",
    active: "studio-node--active",
    done: "studio-node--done",
    error: "studio-node--error",
  };

  const edgeBaseStyle = {
    stroke: "#2563eb",
    strokeWidth: 2.5,
  };

  const edgeActiveStyle = {
    stroke: "#0ea5e9",
    strokeWidth: 3.2,
  };

  const badgeBase = "studio-badge";

  const nodeBase = "studio-node";

  function StudioNode({ data }) {
    const statusClass = statusClasses[data.status || "idle"] || statusClasses.idle;
    const badges = [];
    if (data.isEntry) {
      badges.push(
        e("span", { className: `${badgeBase} studio-badge--entry` }, "Entry"),
      );
    }
    if (data.isTerminal) {
      badges.push(
        e("span", { className: `${badgeBase} studio-badge--terminal` }, "Terminal"),
      );
    }
    if (data.isDynamic) {
      badges.push(
        e("span", { className: `${badgeBase} studio-badge--dynamic` }, "Dynamic"),
      );
    }

    return e(
      "div",
      { className: `${nodeBase} ${statusClass}` },
      e(Handle, { type: "target", position: "top", style: { opacity: 0 } }),
      e("div", { className: "text-sm font-semibold" }, data.label || data.id),
      badges.length
        ? e(
            "div",
            { className: "mt-2 flex flex-wrap gap-2" },
            badges,
          )
        : null,
      e(Handle, { type: "source", position: "bottom", style: { opacity: 0 } }),
    );
  }

  const nodeTypes = { studio: StudioNode };

  function StudioEdge({
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    style,
    data,
  }) {
    const [edgePath] = getSmoothStepPath({
      sourceX,
      sourceY,
      targetX,
      targetY,
      sourcePosition,
      targetPosition,
      borderRadius: 18,
    });
    const mergedStyle = {
      ...edgeBaseStyle,
      ...(data?.dynamic ? { strokeDasharray: "6 4" } : null),
      ...style,
    };
    return e(BaseEdge, { id, path: edgePath, style: mergedStyle });
  }

  const edgeTypes = { studio: StudioEdge };

  function buildFlowGraph(graph) {
    const nodes = [];
    const edges = [];
    const positions = new Map();
    const dynamicNodesBySource = new Map();
    const gapX = 240;
    const gapY = 180;
    const nodeOrder = graph.nodes.map((node) => node.node_id);
    const nodeById = new Map(graph.nodes.map((node) => [node.node_id, node]));
    const adjacency = new Map();
    nodeOrder.forEach((nodeId) => adjacency.set(nodeId, []));
    graph.edges.forEach((edge) => {
      if (!edge.target_node_id) return;
      if (!adjacency.has(edge.source_node_id)) {
        adjacency.set(edge.source_node_id, []);
      }
      adjacency.get(edge.source_node_id).push(edge.target_node_id);
    });

    const levels = new Map();
    const queue = [];
    graph.entry_nodes.forEach((nodeId) => {
      levels.set(nodeId, 0);
      queue.push(nodeId);
    });
    if (queue.length === 0 && nodeOrder.length) {
      levels.set(nodeOrder[0], 0);
      queue.push(nodeOrder[0]);
    }
    while (queue.length) {
      const current = queue.shift();
      const currentLevel = levels.get(current) ?? 0;
      const nextNodes = adjacency.get(current) || [];
      nextNodes.forEach((target) => {
        const nextLevel = currentLevel + 1;
        if (!levels.has(target) || levels.get(target) > nextLevel) {
          levels.set(target, nextLevel);
          queue.push(target);
        }
      });
    }

    let maxLevel = 0;
    levels.forEach((value) => {
      if (value > maxLevel) {
        maxLevel = value;
      }
    });
    nodeOrder.forEach((nodeId) => {
      if (!levels.has(nodeId)) {
        levels.set(nodeId, maxLevel + 1);
      }
    });

    const columns = new Map();
    nodeOrder.forEach((nodeId) => {
      const level = levels.get(nodeId) ?? 0;
      if (!columns.has(level)) {
        columns.set(level, []);
      }
      columns.get(level).push(nodeId);
    });

    const orderedLevels = Array.from(columns.keys()).sort((a, b) => a - b);
    const maxRowSize = Math.max(...Array.from(columns.values()).map((list) => list.length), 1);

    orderedLevels.forEach((level, rowIndex) => {
      const rowNodes = columns.get(level).slice();
      rowNodes.sort((a, b) => {
        const labelA = nodeById.get(a)?.label || a;
        const labelB = nodeById.get(b)?.label || b;
        return labelA.localeCompare(labelB);
      });
      const rowWidth = (rowNodes.length - 1) * gapX;
      const centerOffset = ((maxRowSize - 1) * gapX - rowWidth) / 2;
      rowNodes.forEach((nodeId, columnIndex) => {
        const position = {
          x: columnIndex * gapX + centerOffset,
          y: rowIndex * gapY,
        };
        positions.set(nodeId, position);
        const node = nodeById.get(nodeId);
        nodes.push({
          id: nodeId,
          type: "studio",
          position,
          sourcePosition: "bottom",
          targetPosition: "top",
          data: {
            id: nodeId,
            label: node?.label || nodeId,
            status: "idle",
            isEntry: graph.entry_nodes.includes(nodeId),
            isTerminal: graph.terminal_nodes.includes(nodeId),
          },
        });
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
        type: "studio",
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
            edgeTypes,
            fitView: true,
            fitViewOptions: { padding: 0.35 },
            minZoom: 0.2,
          },
          e(Background, {
            variant: RF.BackgroundVariant.Dots,
            gap: 26,
            size: 1.4,
            color: "#cbd5f5",
          }),
          e(Controls, { position: "top-right" }),
          e(MiniMap, {
            position: "bottom-right",
            nodeStrokeColor: "#cbd5f5",
            nodeColor: "#e2e8f0",
            maskColor: "rgba(248, 250, 252, 0.7)",
          }),
        )
      : e(
          "div",
          { className: "flex h-full items-center justify-center studio-empty" },
          status.error || "Loading graph…",
        );

    return e(
      "div",
      { className: "flex h-full flex-col studio-shell" },
      e(
        "header",
        { className: "flex items-center justify-between px-6 py-4 studio-header" },
        e(
          "div",
          { className: "space-y-1" },
          e("h1", { className: "text-lg font-semibold studio-title" }, "Pydantic Graph Studio"),
          e(
            "p",
            { className: "text-xs uppercase tracking-[0.2em] studio-status" },
            statusLabel,
          ),
        ),
        e(
          "div",
          { className: "flex items-center gap-3" },
          status.error
            ? e(
                "span",
                { className: "text-xs studio-error" },
                status.error,
              )
            : null,
          e(
            "button",
            {
              className: "rounded-md px-4 py-2 text-sm font-semibold studio-button",
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
