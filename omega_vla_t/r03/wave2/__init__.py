"""Ω-VLA-T∞³ R0.3-OMEGA Wave 2.

Wave 2 expands the typed Operator Universe with sparse and matrix-free
semantics, stable bounded matrix-function baselines, operator genomes,
property-evidence inference, commutant solvers, rewrite saturation and
reproducible benchmark campaigns.

All outputs are research-software artifacts. They do not constitute theorem,
formal-proof or scientific-validation claims.
"""

from .campaigns import CampaignPlan, OperatorCampaignAddress, OperatorCampaignCodec
from .commutant import CommutantReport, commutant_basis, simultaneous_commutant_basis
from .egraph import EGraphBudget, EGraphReport, RewriteRule, saturate
from .families import OperatorFamily, OperatorFamilyCatalog, default_family_catalog
from .genome import OperatorGenome, OperatorGenomeRegistry
from .matrix_free import MatrixFreeAudit, MatrixFreeOperator
from .matrix_functions import (
    MatrixFunctionReport,
    matrix_exponential,
    matrix_logarithm,
    matrix_sign,
    matrix_square_root,
)
from .oak_wave2 import Wave2OAKReport, audit_wave2
from .properties import EvidenceLevel, PropertyEvidence, infer_properties
from .sparse import CSRMatrix, SparseOperator

__all__ = [
    "CSRMatrix",
    "CampaignPlan",
    "CommutantReport",
    "EGraphBudget",
    "EGraphReport",
    "EvidenceLevel",
    "MatrixFreeAudit",
    "MatrixFreeOperator",
    "MatrixFunctionReport",
    "OperatorCampaignAddress",
    "OperatorCampaignCodec",
    "OperatorFamily",
    "OperatorFamilyCatalog",
    "OperatorGenome",
    "OperatorGenomeRegistry",
    "PropertyEvidence",
    "RewriteRule",
    "SparseOperator",
    "Wave2OAKReport",
    "audit_wave2",
    "commutant_basis",
    "default_family_catalog",
    "infer_properties",
    "matrix_exponential",
    "matrix_logarithm",
    "matrix_sign",
    "matrix_square_root",
    "saturate",
    "simultaneous_commutant_basis",
]

__version__ = "0.3.2"
