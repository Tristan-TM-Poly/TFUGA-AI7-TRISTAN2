"""Small explainable Ω-ORG-FAM-T demonstration."""
from itertools import islice

from omega_org_fam_t import classify_features, iter_requested_cells

cells = list(islice(iter_requested_cells(262_144), 262_144))
result = classify_features(
    cells,
    {"alcohol_phenol", "O-H environment", "oxidation_reduction"},
    top_k=5,
)
for family_id, score in result.ranked_family_ids:
    print(f"{family_id}: {score:.3f}")
print(*result.warnings, sep="\n")
