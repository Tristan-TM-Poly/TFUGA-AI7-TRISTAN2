"""Omega Patent Thesis T.

Small helpers that turn a patent record into a cautious thesis seed,
claim tree, review-risk map, prototype plan, and product hypothesis.
"""

from .seed import PatentThesisSeed, example_seed
from .claim_tree import claim_tree
from .risk import risk_level
from .company import product_map
from .gitpack import gitpack_paths

__all__ = [
    "PatentThesisSeed",
    "claim_tree",
    "example_seed",
    "gitpack_paths",
    "product_map",
    "risk_level",
]
