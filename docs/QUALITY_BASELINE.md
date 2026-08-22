# NEOS Quality Baseline

The canonical runtime/source quality gate is:

```text
python -m ruff check src tests
python -m mypy src
python -m pytest -q
```

`python -m mypy src` is the supported NEOS source type check. The repository
also contains a top-level `neos/` compatibility package and the real
`src/neos/` source package. A filesystem-wide `python -m mypy .` scan treats
both locations as independent copies of the `neos` module and is therefore not
a supported quality gate.

Test annotation debt is tracked separately from the runtime/source gate. The
current controlled backlog contains 10 findings from `python -m mypy src tests`;
it does not block the runtime source gate or MCP-02C validation.
