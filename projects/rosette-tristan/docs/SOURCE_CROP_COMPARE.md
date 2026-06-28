# Rosette Source Crop Compare

`rosette-source-crop` compares a generated equation render against a source crop image.

It can either compare against an existing PNG crop, or extract a crop from a PDF using PyMuPDF when PDF support is installed.

## Compare against an existing crop

```bash
rosette-source-crop "x=y" --source-crop source.png --out out_source_crop
```

## Extract crop from PDF, then compare

```bash
rosette-source-crop "\\frac{dx}{dt}=-kx+u(t)" --pdf paper.pdf --page 2 --bbox "100,200,420,260" --out out_source_crop
```

## Outputs

```text
out_source_crop/
  E1_candidate.png
  E1_source_crop.png        # only when extracted from PDF
  source_crop_compare_report.json
```

## OAK status values

- `source_crop_match_not_certified`
- `source_crop_review_needed`
- `source_crop_mismatch`
- `source_crop_compare_failed`

## OAK lock

A high image score improves confidence, but it is not proof. The bbox may be wrong, the source crop may not contain the full equation, and MathText rendering is not a full LaTeX engine. Certification still requires bbox validation, symbolic checks, and OAK/human review.
