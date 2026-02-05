## 1. Runtime + Schema
- [ ] Add new event models to `src/pydantic_graph_studio/schemas.py` for tool calls and input requests/responses.
- [ ] Extend `src/pydantic_graph_studio/runtime.py` to emit tool/input events via an interaction hub per run.

## 2. Server API
- [ ] Add `POST /api/input` to `src/pydantic_graph_studio/server.py` to resolve pending input requests.
- [ ] Wire the interaction hub into `iter_run_events` so events and responses share the run queue.

## 3. UI
- [ ] Add UI components in `src/pydantic_graph_studio/ui/assets/app.js` for tool activity and approval prompts.
- [ ] Handle new event types and POST responses from the UI.

## 4. Examples
- [ ] Update `examples/tool_usage.py` to emit tool call/result events.
- [ ] Update `examples/human_in_the_loop.py` to request approval and block until a response arrives.

## 5. Verification
- [ ] Manually run `pgraph example tool-usage` and confirm tool activity appears.
- [ ] Manually run `pgraph example human-in-the-loop` and confirm the run blocks until approval is clicked.
