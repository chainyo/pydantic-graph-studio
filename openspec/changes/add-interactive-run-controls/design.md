# Design: Interactive Run Controls

## Overview
Introduce structured runtime events for tool usage and human approvals, plus a small request/response channel between the UI and the running graph. The UI will surface tool activity and pause on approval requests until a user responds.

## Event Types
Add new event payloads to the runtime stream and schema:
- `tool_call`: emitted when a node invokes an external tool.
  - Fields: `run_id`, `event_type`, `node_id`, `tool_name`, `arguments`, `call_id`.
- `tool_result`: emitted when a tool call completes.
  - Fields: `run_id`, `event_type`, `node_id`, `tool_name`, `call_id`, `output`, `success`.
- `input_request`: emitted when a node requests human approval.
  - Fields: `run_id`, `event_type`, `node_id`, `request_id`, `prompt`, `options`.
- `input_response`: emitted when the user responds.
  - Fields: `run_id`, `event_type`, `node_id`, `request_id`, `response`.

Existing event ordering remains intact; interactive events interleave with node events and share the same `run_id`.

## Runtime Interaction Hub
Create a per-run interaction hub that:
- Emits tool and input events into the same event queue as node events.
- Tracks pending input requests by `request_id`.
- Provides an awaitable API (`request_approval`) to block node execution until a response is posted.

This hub is passed to the graph run via `inputs` (or `deps` if `inputs` is unavailable), so example nodes can call it through `ctx.inputs` (or `ctx.deps`).

## Server API
Add a new endpoint to submit interactive responses:
- `POST /api/input`
  - Body: `{ run_id, request_id, response }`
  - Responds `200` on success, `404` for unknown run, `400` for unknown request.

The server resolves the pending request in the interaction hub and emits `input_response` to the event stream.

## UI Updates
- Add a right-side panel for tool activity (list of tool calls/results).
- Show an approval prompt when `input_request` arrives. The run remains blocked until the user clicks an option.
- Post the response to `/api/input` and optimistically update the panel once `input_response` is received.

## Backwards Compatibility
- If graphs never emit tool or input events, the UI behaves as before.
- Examples that do not use the interaction hub remain unchanged.
