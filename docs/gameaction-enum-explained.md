# GameAction Enum Explained

`GameAction` is a Python `Enum`. An enum is a fixed set of named singleton
objects.

In `arcengine`, the class is shaped like this:

```python
class GameAction(Enum):
    RESET = (0, SimpleAction)
    ACTION1 = (1, SimpleAction)
    ACTION2 = (2, SimpleAction)
    ACTION3 = (3, SimpleAction)
    ACTION4 = (4, SimpleAction)
    ACTION5 = (5, SimpleAction)
    ACTION6 = (6, ComplexAction)
    ACTION7 = (7, SimpleAction)
```

The tuple on the right side is construction input for the enum member. It does
not mean `GameAction.RESET` is just the tuple `(0, SimpleAction)` at runtime.

Python roughly does this for each member:

```python
GameAction.RESET   -> GameAction.__init__(self, 0, SimpleAction)
GameAction.ACTION1 -> GameAction.__init__(self, 1, SimpleAction)
GameAction.ACTION6 -> GameAction.__init__(self, 6, ComplexAction)
```

The enum initializer is:

```python
def __init__(self, action_id: int, action_type):
    self._value_ = action_id
    self.action_type = action_type
    self.action_data = action_type()
```

So `GameAction.ACTION6` becomes an enum member with:

```python
GameAction.ACTION6.value       # 6
GameAction.ACTION6.name        # "ACTION6"
GameAction.ACTION6.action_type # ComplexAction
GameAction.ACTION6.action_data # ComplexAction(game_id="", x=0, y=0)
```

For `ACTION1`:

```python
GameAction.ACTION1.value       # 1
GameAction.ACTION1.name        # "ACTION1"
GameAction.ACTION1.action_type # SimpleAction
GameAction.ACTION1.action_data # SimpleAction(game_id="")
```

The tuple is a compact way to say: this action has numeric id `6` and uses the
`ComplexAction` data model.

## Singleton Behavior

Each enum member is a singleton:

```python
GameAction.ACTION6 is GameAction.ACTION6  # True
```

There is only one `ACTION6` object in the process.

That matters because `set_data()` mutates the enum member:

```python
def set_data(self, data):
    self.action_data = self.action_type(**data)
```

Example:

```python
action = GameAction.ACTION6
action.set_data({"x": 12, "y": 34})

GameAction.ACTION6.action_data.x  # 12
GameAction.ACTION6.action_data.y  # 34
```

The repo can return only a `GameAction` from `choose_action()` because the
chosen enum member carries its payload in `action.action_data`.

Mental model:

```text
GameAction.ACTION6
  name: "ACTION6"
  value: 6
  action_type: ComplexAction
  action_data: ComplexAction(x=12, y=34)
```

For simple actions, `action_data` usually only contains `game_id`, so there is
often nothing meaningful to set. For complex actions like clicks,
`action_data` carries coordinates.

## Important Caveat

Because enum members are singletons, mutable fields on them are shared. Calling
`GameAction.ACTION6.set_data(...)` changes the process-wide `ACTION6` member.

That pattern works when the code sets data and immediately submits the action,
but it is fragile in concurrent code. If two threads mutate the same enum member
at the same time, or if a later action reuses an enum member without resetting
its payload, stale data can leak.
