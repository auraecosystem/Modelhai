# Recording Trace Structure

Based on:

- `agents/recorder.py`
- `agents/agent.py`
- `agents/templates/llm_agents.py`

## File format

Files in `recordings/` are newline-delimited JSON (`.recording.jsonl`).

Every line has the same outer wrapper:

```json
{
  "timestamp": "2026-07-03T13:35:57.101037+00:00",
  "data": { ... }
}
```

- `timestamp`: UTC ISO-8601 time written by the recorder
- `data`: the actual recorded event payload

## Event types in the sample trace

The sample trace contains 32 events:

- 11 frame events
- 20 token / assistant observation events
- 1 final LLM metadata event

## Frame event: game state

This is the main game-state record written from `FrameData` in `agents/agent.py`.

```json
{
  "game_id": "ls20-9607627b",
  "frame": [[[...]]],
  "state": "NOT_FINISHED",
  "levels_completed": 0,
  "win_levels": 7,
  "action_input": {
    "id": 1,
    "data": { "game_id": "ls20-9607627b" },
    "reasoning": { ... }
  },
  "guid": "bb151cbb-c71e-419d-9d60-015c53e5fd9e",
  "full_reset": false,
  "available_actions": [1, 2, 3, 4]
}
```

Fields:

- `game_id`: game instance id
- `frame`: 3D grid data shaped as `grids x rows x cols`
- `state`: game status such as `NOT_PLAYED`, `NOT_FINISHED`, `GAME_OVER`, `WON`
- `levels_completed`: current score / progress counter
- `win_levels`: number of levels needed to win
- `action_input`: action that produced this frame
- `guid`: run/session id emitted by the environment
- `full_reset`: whether this frame came from a full reset
- `available_actions`: action ids currently allowed by the environment

In the sampled Locksmith trace:

- `frame` shape is always `1 x 64 x 64`
- `state` is always `NOT_FINISHED`
- `available_actions` is always `[1, 2, 3, 4]`
- `full_reset` is always `false`
- observed tile values are `0, 1, 3, 4, 5, 8, 9, 11, 12`

## `action_input` fields

- `id`: numeric action id, for example `0=RESET`, `1=ACTION1`, `2=ACTION2`, `3=ACTION3`, `4=ACTION4`, `6=ACTION6`
- `data`: action arguments; usually at least `game_id`, and for click-style actions may also include `x` and `y`
- `reasoning`: optional agent metadata explaining why the action was chosen

In this trace, `reasoning` is often a JSON-encoded string containing fields such as:

- `model`
- `action_chosen`
- `reasoning_effort`
- `reasoning_tokens`
- `total_reasoning_tokens`
- `game_context`
- `agent_type`
- `game_rules`
- `response_preview`

## Token / observation events

These events are not game-state frames. They are auxiliary LLM trace entries written by `track_tokens()`:

```json
{
  "tokens": 13198,
  "total_tokens": 13198,
  "assistant": "..."
}
```

Fields:

- `tokens`: tokens consumed by this model response
- `total_tokens`: running token total for the session
- `assistant`: plain-text observation or reasoning snippet

## Final LLM metadata event

At cleanup, the LLM agent writes one final prompt/tool snapshot:

```json
{
  "llm_user_prompt": "...",
  "llm_tools": [...],
  "llm_tool_resp_prompt": "..."
}
```

Fields:

- `llm_user_prompt`: the main game instruction prompt
- `llm_tools`: tool/function schema exposed to the model
- `llm_tool_resp_prompt`: prompt used to elicit a textual observation from the latest frame

## Practical structure summary

If you are parsing these files, treat them as:

1. JSONL file
2. outer event wrapper with `timestamp` and `data`
3. `data` payload that can be one of:
   - frame/game-state event
   - token/assistant event
   - final LLM metadata event
