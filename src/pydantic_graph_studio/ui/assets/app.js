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
  const dagreLib = window.dagre;
  const hasDagre = dagreLib && dagreLib.graphlib && typeof dagreLib.layout === "function";

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

  function formatApprovalContext(context) {
    if (context === null || context === undefined) {
      return "";
    }
    if (typeof context === "string") {
      return context;
    }
    try {
      return JSON.stringify(context, null, 2);
    } catch (_error) {
      return String(context);
    }
  }

  function extractNumber(value) {
    if (typeof value === "number" && Number.isFinite(value)) {
      return value;
    }
    if (typeof value === "string") {
      const parsed = Number(value);
      if (Number.isFinite(parsed)) {
        return parsed;
      }
    }
    return null;
  }

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
      centerX: typeof data?.routeX === "number" ? data.routeX : undefined,
    });
    const mergedStyle = {
      ...edgeBaseStyle,
      ...(data?.dynamic ? { strokeDasharray: "6 4" } : null),
      ...style,
    };
    return e(BaseEdge, { id, path: edgePath, style: mergedStyle });
  }

  const edgeTypes = { studio: StudioEdge };

  function estimateNodeSize(data) {
    const labelLength = (data.label || data.id || "").length;
    const badgeCount =
      (data.isEntry ? 1 : 0) + (data.isTerminal ? 1 : 0) + (data.isDynamic ? 1 : 0);
    const width = Math.min(260, Math.max(160, labelLength * 7 + 90));
    const height = 64 + badgeCount * 18;
    return { width, height };
  }

  function buildFlowGraphDagre(graph) {
    const nodes = [];
    const edges = [];
    const nodeData = new Map();
    const sizeById = new Map();
    const dynamicNodesBySource = new Map();
    const entrySet = new Set(graph.entry_nodes || []);
    const terminalSet = new Set(graph.terminal_nodes || []);

    graph.nodes.forEach((node) => {
      nodeData.set(node.node_id, {
        id: node.node_id,
        label: node.label || node.node_id,
        isEntry: entrySet.has(node.node_id),
        isTerminal: terminalSet.has(node.node_id),
        isDynamic: false,
      });
    });

    const edgesInput = [];
    graph.edges.forEach((edge) => {
      let target = edge.target_node_id;
      if (!target) {
        let dynamicId = dynamicNodesBySource.get(edge.source_node_id);
        if (!dynamicId) {
          dynamicId = `dynamic-${edge.source_node_id}`;
          dynamicNodesBySource.set(edge.source_node_id, dynamicId);
          nodeData.set(dynamicId, {
            id: dynamicId,
            label: "Dynamic target",
            isEntry: false,
            isTerminal: false,
            isDynamic: true,
          });
        }
        target = dynamicId;
      }
      edgesInput.push({
        source: edge.source_node_id,
        target,
        dynamic: edge.dynamic,
      });
    });

    const dagreGraph = new dagreLib.graphlib.Graph();
    dagreGraph.setGraph({
      rankdir: "TB",
      ranksep: 120,
      nodesep: 70,
      marginx: 40,
      marginy: 40,
    });
    dagreGraph.setDefaultEdgeLabel(() => ({}));

    nodeData.forEach((data, nodeId) => {
      const size = estimateNodeSize(data);
      sizeById.set(nodeId, size);
      dagreGraph.setNode(nodeId, size);
    });

    edgesInput.forEach((edge) => {
      dagreGraph.setEdge(edge.source, edge.target);
    });

    dagreLib.layout(dagreGraph);

    nodeData.forEach((data, nodeId) => {
      const layout = dagreGraph.node(nodeId) || { x: 0, y: 0 };
      const size = sizeById.get(nodeId) || { width: 180, height: 72 };
      nodes.push({
        id: nodeId,
        type: "studio",
        position: {
          x: layout.x - size.width / 2,
          y: layout.y - size.height / 2,
        },
        sourcePosition: "bottom",
        targetPosition: "top",
        data: {
          id: nodeId,
          label: data.label || nodeId,
          status: "idle",
          isEntry: data.isEntry,
          isTerminal: data.isTerminal,
          isDynamic: data.isDynamic,
        },
      });
    });

    edgesInput.forEach((edge, index) => {
      edges.push({
        id: `e-${edge.source}-${edge.target}-${index}`,
        source: edge.source,
        target: edge.target,
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

  function buildFlowGraphHeuristic(graph) {
    const nodes = [];
    const edges = [];
    const positions = new Map();
    const dynamicNodesBySource = new Map();
    const terminalSet = new Set(graph.terminal_nodes || []);
    const gapX = 260;
    const gapY = 190;
    const nodeWidth = 160;
    const nodeOrder = graph.nodes.map((node) => node.node_id);
    const nodeById = new Map(graph.nodes.map((node) => [node.node_id, node]));
    const adjacency = new Map();
    const incoming = new Map();
    nodeOrder.forEach((nodeId) => adjacency.set(nodeId, []));
    nodeOrder.forEach((nodeId) => incoming.set(nodeId, []));
    graph.edges.forEach((edge) => {
      if (!edge.target_node_id) return;
      if (!adjacency.has(edge.source_node_id)) {
        adjacency.set(edge.source_node_id, []);
      }
      if (!incoming.has(edge.target_node_id)) {
        incoming.set(edge.target_node_id, []);
      }
      adjacency.get(edge.source_node_id).push(edge.target_node_id);
      incoming.get(edge.target_node_id).push(edge.source_node_id);
    });

    const levels = new Map();
    const entryNodes = graph.entry_nodes.length ? graph.entry_nodes : nodeOrder.slice(0, 1);
    entryNodes.forEach((nodeId) => {
      levels.set(nodeId, 0);
    });
    const maxIterations = Math.max(nodeOrder.length * 2, 1);
    for (let iteration = 0; iteration < maxIterations; iteration += 1) {
      let updated = false;
      graph.edges.forEach((edge) => {
        if (!edge.target_node_id) return;
        const sourceLevel = levels.get(edge.source_node_id);
        if (sourceLevel === undefined) return;
        const candidate = sourceLevel + 1;
        const current = levels.get(edge.target_node_id);
        if (current === undefined || current < candidate) {
          levels.set(edge.target_node_id, Math.min(candidate, nodeOrder.length));
          updated = true;
        }
      });
      if (!updated) break;
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
    let maxNonTerminalLevel = -1;
    nodeOrder.forEach((nodeId) => {
      if (terminalSet.has(nodeId)) return;
      const level = levels.get(nodeId) ?? 0;
      if (level > maxNonTerminalLevel) {
        maxNonTerminalLevel = level;
      }
    });
    if (maxNonTerminalLevel < 0) {
      maxNonTerminalLevel = maxLevel;
    }
    terminalSet.forEach((nodeId) => {
      levels.set(nodeId, maxNonTerminalLevel + 1);
    });
    if (maxNonTerminalLevel >= 0) {
      nodeOrder.forEach((nodeId) => {
        if (terminalSet.has(nodeId)) return;
        const targets = adjacency.get(nodeId) || [];
        if (targets.length === 0) return;
        const allTerminal = targets.every((target) => terminalSet.has(target));
        if (allTerminal) {
          levels.set(nodeId, Math.max(levels.get(nodeId) ?? 0, maxNonTerminalLevel));
        }
      });
    }

    const columns = new Map();
    nodeOrder.forEach((nodeId) => {
      const level = levels.get(nodeId) ?? 0;
      if (!columns.has(level)) {
        columns.set(level, []);
      }
      columns.get(level).push(nodeId);
    });

    const orderedLevels = Array.from(columns.keys()).sort((a, b) => a - b);
    const labelFor = (nodeId) => nodeById.get(nodeId)?.label || nodeId;
    const layers = orderedLevels.map((level) => columns.get(level).slice());
    layers.forEach((layer) => layer.sort((a, b) => labelFor(a).localeCompare(labelFor(b))));

    const nodeIndex = new Map();
    const refreshIndex = () => {
      layers.forEach((layer) => {
        layer.forEach((nodeId, index) => {
          nodeIndex.set(nodeId, index);
        });
      });
    };
    const barycenterSort = (layerIndex, useIncoming) => {
      const layer = layers[layerIndex];
      const scores = new Map();
      layer.forEach((nodeId, index) => {
        const neighbors = useIncoming ? incoming.get(nodeId) : adjacency.get(nodeId);
        const indices = (neighbors || [])
          .map((neighbor) => nodeIndex.get(neighbor))
          .filter((value) => value !== undefined);
        const score = indices.length
          ? indices.reduce((sum, value) => sum + value, 0) / indices.length
          : index;
        scores.set(nodeId, score);
      });
      layer.sort((a, b) => {
        const diff = (scores.get(a) ?? 0) - (scores.get(b) ?? 0);
        if (Math.abs(diff) > 0.0001) {
          return diff;
        }
        return labelFor(a).localeCompare(labelFor(b));
      });
    };

    refreshIndex();
    for (let pass = 0; pass < 3; pass += 1) {
      for (let i = 1; i < layers.length; i += 1) {
        barycenterSort(i, true);
        refreshIndex();
      }
      for (let i = layers.length - 2; i >= 0; i -= 1) {
        barycenterSort(i, false);
        refreshIndex();
      }
    }

    const maxRowSize = Math.max(...layers.map((list) => list.length), 1);
    const rowBounds = new Map();
    let globalMinX = Infinity;
    let globalMaxX = -Infinity;

    orderedLevels.forEach((level, rowIndex) => {
      const rowNodes = layers[rowIndex] || columns.get(level).slice();
      let minX = Infinity;
      let maxX = -Infinity;
      const rowWidth = (rowNodes.length - 1) * gapX;
      const centerOffset = ((maxRowSize - 1) * gapX - rowWidth) / 2;
      rowNodes.forEach((nodeId, columnIndex) => {
        const position = {
          x: columnIndex * gapX + centerOffset,
          y: rowIndex * gapY,
        };
        positions.set(nodeId, position);
        minX = Math.min(minX, position.x);
        maxX = Math.max(maxX, position.x);
        globalMinX = Math.min(globalMinX, position.x);
        globalMaxX = Math.max(globalMaxX, position.x);
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
      if (rowNodes.length) {
        rowBounds.set(level, {
          minX: minX - nodeWidth / 2,
          maxX: maxX + nodeWidth / 2,
        });
      }
    });
    if (!Number.isFinite(globalMinX) || !Number.isFinite(globalMaxX)) {
      globalMinX = 0;
      globalMaxX = 0;
    }
    const sideLaneOffset = gapX * 1.1;
    const sideLaneSpacing = gapX * 0.35;
    let leftLaneCount = 0;
    let rightLaneCount = 0;

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

      let routeX;
      const sourceLevel = levels.get(edge.source_node_id) ?? 0;
      const targetLevel = levels.get(target) ?? 0;
      if (Math.abs(targetLevel - sourceLevel) > 1) {
        const sourcePos = positions.get(edge.source_node_id);
        const targetPos = positions.get(target);
        if (sourcePos && targetPos) {
          const defaultCenter = (sourcePos.x + targetPos.x) / 2;
          let needsDetour = false;
          for (
            let level = Math.min(sourceLevel, targetLevel) + 1;
            level <= Math.max(sourceLevel, targetLevel) - 1;
            level += 1
          ) {
            const bounds = rowBounds.get(level);
            if (!bounds) continue;
            if (defaultCenter >= bounds.minX && defaultCenter <= bounds.maxX) {
              needsDetour = true;
              break;
            }
          }
          if (needsDetour) {
            const useRight = sourcePos.x >= targetPos.x;
            if (useRight) {
              rightLaneCount += 1;
              routeX = globalMaxX + sideLaneOffset + (rightLaneCount - 1) * sideLaneSpacing;
            } else {
              leftLaneCount += 1;
              routeX = globalMinX - sideLaneOffset - (leftLaneCount - 1) * sideLaneSpacing;
            }
          }
        }
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
          routeX,
        },
      });
    });

    return { nodes, edges };
  }

  function buildFlowGraph(graph) {
    if (hasDagre) {
      return buildFlowGraphDagre(graph);
    }
    return buildFlowGraphHeuristic(graph);
  }

  function App() {
    const [graph, setGraph] = useState(null);
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [status, setStatus] = useState({ phase: "idle", runId: null, error: null });
    const [toolActivity, setToolActivity] = useState([]);
    const [pendingInput, setPendingInput] = useState(null);
    const [streaming, setStreaming] = useState({ current: 0, total: null, chunks: [] });
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
      setToolActivity([]);
      setPendingInput(null);
      setStreaming({ current: 0, total: null, chunks: [] });
    };

    const submitInput = async (response) => {
      if (!status.runId || !pendingInput) {
        return;
      }
      const requestId = pendingInput.requestId;
      setPendingInput((current) => {
        if (!current || current.requestId !== requestId) {
          return current;
        }
        return { ...current, submitting: true, error: null };
      });
      try {
        const httpResponse = await fetch("/api/input", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            run_id: status.runId,
            request_id: requestId,
            response,
          }),
        });
        if (!httpResponse.ok) {
          const message = await httpResponse.text();
          throw new Error(message || `Failed to submit input (${httpResponse.status})`);
        }
        setPendingInput(null);
      } catch (error) {
        setPendingInput((current) => {
          if (!current || current.requestId !== requestId) {
            return current;
          }
          return {
            ...current,
            submitting: false,
            error: error.message || "Failed to submit input",
          };
        });
      }
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
        case "tool_call":
          setToolActivity((current) => {
            const existingIndex = current.findIndex((item) => item.callId === payload.call_id);
            const entry = {
              callId: payload.call_id,
              nodeId: payload.node_id,
              toolName: payload.tool_name,
              arguments: payload.arguments,
              output: null,
              success: null,
            };
            if (existingIndex >= 0) {
              const next = [...current];
              next[existingIndex] = { ...next[existingIndex], ...entry };
              return next;
            }
            return [entry, ...current];
          });
          break;
        case "tool_result":
          setToolActivity((current) => {
            const existingIndex = current.findIndex((item) => item.callId === payload.call_id);
            const entry = {
              callId: payload.call_id,
              nodeId: payload.node_id,
              toolName: payload.tool_name,
              output: payload.output,
              success: payload.success,
            };
            if (existingIndex >= 0) {
              const next = [...current];
              next[existingIndex] = { ...next[existingIndex], ...entry };
              return next;
            }
            return [entry, ...current];
          });
          if (payload.tool_name === "stream_chunk") {
            setStreaming((current) => {
              const output = payload.output && typeof payload.output === "object" ? payload.output : {};
              const tick = extractNumber(output.tick) ?? current.current;
              const total = extractNumber(output.total) ?? current.total;
              const chunkText = typeof output.chunk === "string" ? output.chunk : null;
              const chunks = chunkText
                ? [chunkText, ...current.chunks.filter((item) => item !== chunkText)].slice(0, 8)
                : current.chunks;
              return {
                current: Math.max(current.current, tick || 0),
                total,
                chunks,
              };
            });
          }
          break;
        case "input_request":
          setPendingInput({
            requestId: payload.request_id,
            nodeId: payload.node_id,
            prompt: payload.prompt,
            context: payload.context,
            options: payload.options?.length ? payload.options : ["yes", "no"],
            submitting: false,
            error: null,
          });
          break;
        case "input_response":
          setPendingInput((current) =>
            current && current.requestId === payload.request_id ? null : current,
          );
          break;
        case "run_end":
          setStatus((current) => ({ ...current, phase: "ready" }));
          setPendingInput(null);
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
          setPendingInput(null);
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

    const graphCanvas = graph
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

    const toolFeed = e(
      "aside",
      { className: "studio-sidebar" },
      e(
        "section",
        { className: "studio-stream-panel" },
        e("p", { className: "studio-sidebar-title" }, "Streaming"),
        e(
          "p",
          { className: "studio-stream-counter" },
          streaming.total ? `${streaming.current}/${streaming.total} chunks` : `${streaming.current} chunks`,
        ),
        streaming.chunks.length
          ? e(
              "div",
              { className: "studio-stream-list" },
              streaming.chunks.map((chunk, index) =>
                e("p", { key: `${index}-${chunk}`, className: "studio-stream-item" }, chunk),
              ),
            )
          : e("p", { className: "studio-sidebar-empty" }, "No stream chunks yet"),
      ),
      e("p", { className: "studio-sidebar-title" }, "Tool Activity"),
      toolActivity.length
        ? e(
            "div",
            { className: "studio-tool-list" },
            toolActivity.map((item) =>
              e(
                "article",
                { key: item.callId, className: "studio-tool-item" },
                e("p", { className: "studio-tool-name" }, item.toolName),
                e("p", { className: "studio-tool-meta" }, `node ${item.nodeId}`),
                item.arguments !== undefined
                  ? e(
                      "pre",
                      { className: "studio-tool-json" },
                      JSON.stringify(item.arguments, null, 2),
                    )
                  : null,
                item.output !== null
                  ? e(
                      "pre",
                      { className: "studio-tool-json" },
                      JSON.stringify(item.output, null, 2),
                    )
                  : e("p", { className: "studio-tool-pending" }, "Waiting for result…"),
              ),
            ),
          )
        : e("p", { className: "studio-sidebar-empty" }, "No tool calls yet"),
    );

    const content = e(
      "div",
      { className: "studio-main" },
      e("section", { className: "studio-canvas" }, graphCanvas),
      toolFeed,
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
      pendingInput
        ? e(
            "div",
            { className: "studio-modal-backdrop" },
            e(
              "div",
              { className: "studio-modal" },
              e("p", { className: "studio-modal-title" }, "Approval Required"),
              e("p", { className: "studio-modal-node" }, `Node: ${pendingInput.nodeId}`),
              e("p", { className: "studio-modal-prompt" }, pendingInput.prompt),
              pendingInput.context !== null && pendingInput.context !== undefined
                ? e(
                    "pre",
                    { className: "studio-modal-context" },
                    formatApprovalContext(pendingInput.context),
                  )
                : null,
              pendingInput.error
                ? e("p", { className: "studio-modal-error" }, pendingInput.error)
                : null,
              e(
                "div",
                { className: "studio-modal-actions" },
                pendingInput.options.map((option) =>
                  e(
                    "button",
                    {
                      key: option,
                      className: "studio-modal-button",
                      disabled: pendingInput.submitting,
                      onClick: () => submitInput(option),
                    },
                    option,
                  ),
                ),
              ),
            ),
          )
        : null,
    );
  }

  const rootEl = document.getElementById("root");
  if (ReactDOM.createRoot) {
    ReactDOM.createRoot(rootEl).render(e(App));
  } else {
    ReactDOM.render(e(App), rootEl);
  }
})();
