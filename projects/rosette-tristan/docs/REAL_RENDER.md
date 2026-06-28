# Rosette Real Render

`rosette-real-render` is the first real image-rendering layer for Rosette equations.

It renders LaTeX-like math expressions to PNG using Matplotlib mathtext, then compares candidate and reference renderings with a simple pixel-space similarity metric.

## Command

```bash
rosette-real-render "\\frac{dx}{dt} = -k x + u(t)" --reference "\\frac{dx}{dt}=-kx+u(t)" --out out_real_render
```

## Outputs

```text
out_real_render/
  E1_candidate.png
  E1_reference.png
  real_render_report.json
```

## Report fields

- `candidate_png`
- `reference_png`
- `image_score`
- `symbol_score`
- `render_backend`
- `oak_status`
- `warnings`
- `memory_minus`
- `required_next_check`

## OAK lock

This is real rendering, but not full certification. The current backend is Matplotlib mathtext, not a complete system-LaTeX renderer. A future step must add source crop comparison, full LaTeX/PDF rendering when available, visual alignment metrics, and review gates.
