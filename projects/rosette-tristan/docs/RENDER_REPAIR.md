# Rosette Render-Diff-Repair

`rosette-render` is a lightweight OAK-safe scaffold for LaTeX repair scoring.

It does not render real LaTeX yet. It normalizes symbolic layout, applies a small registry of common symbol confusions, compares candidate and reference strings, and marks the result as provisional.

## Command

```bash
rosette-render "\\frac{dx}{dt} = -k x + u(t)" --reference "\\frac{dx}{dt}=-kx+u(t)" --out render.json
```

## Output fields

- `latex_candidate`
- `repaired_latex`
- `reference_latex`
- `render_score`
- `symbol_score`
- `layout_score`
- `oak_status`
- `repair_history`
- `memory_minus`
- `required_next_check`

## OAK lock

This is not certification. A future phase must add real LaTeX rendering, source crop comparison, image metrics, and manual review gates for low similarity.
