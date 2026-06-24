# Reusable Value Engine Bridge

This repository can reuse the value-engine workflow from the central repository.

Central implementation:

- `docs/REUSABLE_VALUE_ENGINE.md`
- `scripts/reusable_value_engine.py`
- `scripts/value_pipeline_oakbench.py`
- `configs/value_pipeline_schema.json`

Portable loop:

```text
artifact -> card -> score -> packet -> review -> recorded outcome
```

Default mode: local draft and review only. No external delivery is performed by this bridge.
