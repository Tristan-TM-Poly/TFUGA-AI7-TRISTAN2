"""Ω-TENSOR-REPAIR-T — reconstructible multi-channel tensor products."""

from .blocks import BlockPartition, BlockRecord, BlockSpec, orbit_summary
from .clebsch_gordan import ClebschGordanBranch, SU2Irrep, su2_clebsch_gordan
from .compiler import CompileResult, compile_spec
from .factorization import LowRankResult, RankOneFactor, dominant_rank_one, low_rank_approximation
from .frames import FrameChannel, FrameResult, TensorFrame, identity_frame
from .higher_order import DenseTensor, outer_many, permutation_sign
from .hypergraph import RepresentationHypergraph, bundle_hypergraph, tower_hypergraph
from .models import AuditCheck, OAKReport, RepairBundle, SymmetryTower, TensorChannel
from .oak import audit_bundle, audit_square, audit_tower
from .projectors import (
    analyze_2d,
    analyze_square_outer,
    antisymmetric_part,
    decompose_square,
    dimension_identity,
    isotropic_part,
    symmetric_part,
    symmetric_traceless_part,
)
from .repair import RepairResult, compose_repairs, repair_symmetry, repair_trace
from .symmetry import default_rank2_tower_2d, group_average, validate_tower

__all__ = [
    "AuditCheck",
    "BlockPartition",
    "BlockRecord",
    "BlockSpec",
    "ClebschGordanBranch",
    "CompileResult",
    "DenseTensor",
    "FrameChannel",
    "FrameResult",
    "LowRankResult",
    "OAKReport",
    "RankOneFactor",
    "RepairBundle",
    "RepairResult",
    "RepresentationHypergraph",
    "SU2Irrep",
    "SymmetryTower",
    "TensorChannel",
    "TensorFrame",
    "analyze_2d",
    "analyze_square_outer",
    "antisymmetric_part",
    "audit_bundle",
    "audit_square",
    "audit_tower",
    "bundle_hypergraph",
    "compile_spec",
    "compose_repairs",
    "decompose_square",
    "default_rank2_tower_2d",
    "dimension_identity",
    "dominant_rank_one",
    "group_average",
    "identity_frame",
    "isotropic_part",
    "low_rank_approximation",
    "orbit_summary",
    "outer_many",
    "permutation_sign",
    "repair_symmetry",
    "repair_trace",
    "su2_clebsch_gordan",
    "symmetric_part",
    "symmetric_traceless_part",
    "tower_hypergraph",
    "validate_tower",
]
