# GameAction And ActionInput Relationship

`GameAction.action_data` and `ActionInput.data` are the same logical payload at
different points in the action flow.

Short version:

```text
GameAction.action_data = outbound payload being prepared
ActionInput.data       = payload that was actually submitted and is echoed in a frame
```

## The Types

`GameAction` is the outbound action choice. It is an enum member such as
`RESET`, `ACTION1`, or `ACTION6`.

Each `GameAction` has an `action_data` model:

```text
simple actions  -> SimpleAction(game_id="")
complex actions -> ComplexAction(game_id="", x=0, y=0)
```

`ActionInput` is the historical or echoed representation of an action. It is
stored on returned frames as `frame.action_input`.

It contains:

```python
class ActionInput(BaseModel):
    id: GameAction
    data: dict[str, Any]
    reasoning: Optional[Any]
```

The fields mean:

```text
id        which GameAction was submitted
data      the data payload used for that action
reasoning optional metadata supplied alongside the action
```

## Outbound Flow

Agents choose a `GameAction`.

For simple actions, they often return the enum member directly:

```python
action = GameAction.ACTION1
```

For complex actions, they fill the action payload first:

```python
action = GameAction.ACTION6
action.set_data({"x": 12, "y": 34})
```

That writes to:

```python
action.action_data
```

In this repo, [agents/agent.py](../agents/agent.py) submits the action in
`Agent.do_action_request()`:

```python
data = action.action_data.model_dump()

reasoning = getattr(action, "reasoning", None)
if reasoning is not None and not isinstance(reasoning, dict):
    reasoning = {"text": str(reasoning)}

raw = self.arc_env.step(action, data=data, reasoning=reasoning)
```

So the outbound conversion is:

```text
GameAction.ACTION6.action_data
  -> model_dump()
  -> data dict passed to arc_env.step()
```

## Local Environment Flow

For local games, `arc_agi.LocalEnvironmentWrapper.step()` creates an
`ActionInput`:

```python
action_input = ActionInput(
    id=action,
    data=data or {},
    reasoning=reasoning,
)
```

Then the underlying game receives:

```python
self._game.perform_action(action_input, raw=True)
```

Inside `arcengine.ARCBaseGame.perform_action()`, that same `ActionInput` is
stored in the returned frame:

```python
frame_raw.action_input = action_input
```

So the local path is:

```text
GameAction.action_data
  -> dict passed as data
  -> ActionInput.data
  -> FrameDataRaw.action_input.data
  -> FrameData.action_input.data
```

## Remote Environment Flow

For remote games, `arc_agi.RemoteEnvironmentWrapper.step()` sends the data to
the ARC API endpoint.

It builds a JSON payload like:

```python
payload = {
    "game_id": self.environment_info.game_id,
    "guid": self._guid,
}
```

For complex actions, it adds coordinates:

```python
if data:
    if "x" in data:
        payload["x"] = data["x"]
    if "y" in data:
        payload["y"] = data["y"]
```

If reasoning exists, it is sent separately:

```python
if reasoning:
    payload["reasoning"] = json.dumps(reasoning)
```

The remote API response is converted back to `FrameDataRaw`. The response
contains the echoed `action_input`, so the returned frame again carries:

```text
FrameDataRaw.action_input.id
FrameDataRaw.action_input.data
FrameDataRaw.action_input.reasoning
```

## Reasoning Is Separate From action_data

`reasoning` is not part of `GameAction.action_data`.

Agents attach it dynamically to the enum member:

```python
action.reasoning = {
    "desired_action": "6",
    "my_reason": "Clicking the target object",
}
```

`Agent.do_action_request()` reads it separately:

```python
reasoning = getattr(action, "reasoning", None)
```

Then it passes it separately to `arc_env.step()`:

```python
self.arc_env.step(action, data=data, reasoning=reasoning)
```

This is intentional in the current repo. Action payload and reasoning metadata
travel together, but they are separate fields:

```text
action_data / data -> mechanical input payload
reasoning          -> optional explanation or metadata
```

## How The Current Repo Uses It

The current repo's main action path is wired correctly:

1. Agents choose a `GameAction`.
2. Complex-action agents call `set_data(...)`.
3. `Agent.do_action_request()` extracts `action.action_data.model_dump()`.
4. `Agent.do_action_request()` separately extracts `action.reasoning`.
5. `arc_env.step(action, data=data, reasoning=reasoning)` submits both.
6. Returned raw frames preserve `raw.action_input`.
7. `Agent._convert_raw_frame_data()` copies `raw.action_input` into the public
   `FrameData`.
8. Recordings include `frame.action_input`.
9. Playback reads recorded `action_input.data` and writes it back into
   `GameAction.action_data` with `set_data(...)`.

Concrete repo examples:

```text
agents/templates/random_agent.py
  sets ACTION6 x/y with action.set_data(...)
  attaches action.reasoning

agents/templates/llm_agents.py
  parses tool/function arguments
  calls action.set_data(data)

agents/agent.py
  converts action.action_data to data
  forwards reasoning separately
  preserves raw.action_input in converted FrameData

agents/agent.py Playback
  reads recorded action_input.data
  calls action.set_data(data)
  restores action.reasoning when present
```

## Caveat

`GameAction` enum members are singletons. `set_data()` mutates the enum member,
and `action.reasoning` is also attached to the enum member.

That means this pattern can be fragile in threaded or multi-agent runs:

```text
Thread A mutates GameAction.ACTION6.action_data
Thread B mutates GameAction.ACTION6.action_data
Thread A submits later and may see Thread B's data
```

Most current agents set data and reasoning immediately before submission, so the
normal path works. The design is still worth treating carefully because stale or
cross-thread enum state can leak if an action is reused without resetting its
payload and reasoning.
