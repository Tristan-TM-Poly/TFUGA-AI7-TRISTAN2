"""Ω-TENSOR-REPAIR-T — reconstructible multi-channel tensor products."""

from .blocks import BlockPartition, BlockRecord, BlockSpec, orbit_summary
from .clebsch_gordan import ClebschGordanBranch, SU2Irrep, su2_clebsch_gordan
from .compiler import CompileResult, compile_spec
from .contractions import (
    ContractionPlan,
    ContractionPlanResult,
    ContractionReceipt,
    ContractionStep,
    TensorState,
    contract_pair,
    double_trace_rank4,
    trace_matrix_tensor,
)
from .factorization import LowRankResult, RankOneFactor, dominant_rank_one, low_rank_approximation
from .frames import FrameChannel, FrameResult, TensorFrame, identity_frame
from .higher_order import DenseTensor, outer_many, permutation_sign
from .hypergraph import RepresentationHypergraph, bundle_hypergraph, tower_hypergraph
from .irreducible_basis import (
    BasisElement,
    IrreducibleCoordinates,
    analyze_square_irreducible,
    basis_gram_matrix,
    basis_orthonormality_error,
    coordinates,
    reconstruct_from_coordinates,
    square_irreducible_basis,
)
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
from .young import (
    YoungDiagram,
    column_antisymmetrize,
    partitions,
    row_symmetrize,
    young_dimension_atlas,
    young_operator,
)

__all__ = [
    "AuditCheck",
    "BasisElement",
    "BlockPartition",
    "BlockRecord",
    "BlockSpec",
    "ClebschGordanBranch",
    "CompileResult",
    "ContractionPlan",
    "ContractionPlanResult",
    "ContractionReceipt",
    "ContractionStep",
    "DenseTensor",
    "FrameChannel",
    "FrameResult",
    "IrreducibleCoordinates",
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
    "TensorState",
    "YoungDiagram",
    "analyze_2d",
    "analyze_square_irreducible",
    "analyze_square_outer",
    "antisymmetric_part",
    "audit_bundle",
    "audit_square",
    "audit_tower",
    "basis_gram_matrix",
    "basis_orthonormality_error",
    "bundle_hypergraph",
    "column_antisymmetrize",
    "compile_spec",
    "compose_repairs",
    "contract_pair",
    "coordinates",
    "decompose_square",
    "default_rank2_tower_2d",
    "dimension_identity",
    "dominant_rank_one",
    "double_trace_rank4",
    "group_average",
    "identity_frame",
    "isotropic_part",
    "low_rank_approximation",
    "orbit_summary",
    "outer_many",
    "partitions",
    "permutation_sign",
    "reconstruct_from_coordinates",
    "repair_symmetry",
    "repair_trace",
    "row_symmetrize",
    "square_irreducible_basis",
    "su2_clebsch_gordan",
    "symmetric_part",
    "symmetric_traceless_part",
    "tower_hypergraph",
    "trace_matrix_tensor",
    "validate_tower",
    "young_dimension_atlas",
    "young_operator",
]
