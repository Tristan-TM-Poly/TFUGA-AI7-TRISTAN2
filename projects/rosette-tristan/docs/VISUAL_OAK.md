# Rosette Visual OAK

`rosette-visual-oak` combines symbolic repair, real math rendering, and source-crop comparison into one visual OAK report.

## Existing crop

```bash
rosette-visual-oak "x=y" --reference "x=y" --source-crop source.png --out out_visual_oak
```

## PDF crop

```bash
rosette-visual-oak "\\frac{dx}{dt}=-kx+u(t)" --pdf paper.pdf --page 2 --bbox "100,200,420,260" --out out_visual_oak
```

## Output

```text
out_visual_oak/
  visual_oak_report.json
  real_render/
    E1_candidate.png
    E1_reference.png
  source_crop/
    E1_candidate.png
```

## OAK status values

- `visual_rendered_no_source_crop`
- `visual_match_not_certified`
- `visual_review_needed`
- `visual_mismatch`

## OAK lock

Visual OAK improves evidence, but it is not proof of mathematical equivalence. Certification still requires bbox validation, source context, symbolic equivalence checks, and human/OAK review.
