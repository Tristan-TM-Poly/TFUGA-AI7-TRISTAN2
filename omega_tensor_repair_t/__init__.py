"""Ω-TENSOR-REPAIR-T — reconstructible multi-channel tensor products."""

from .blocks import BlockPartition, BlockRecord, BlockSpec, orbit_summary
from .compiler import CompileResult, compile_spec
from .frames import FrameChannel, FrameResult, TensorFrame, identity_frame
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
    "CompileResult",
    "FrameChannel",
    "FrameResult",
    "OAKReport",
    "RepairBundle",
    "RepairResult",
    "SymmetryTower",
    "TensorChannel",
    "TensorFrame",
    "analyze_2d",
    "analyze_square_outer",
    "antisymmetric_part",
    "audit_bundle",
    "audit_square",
    "audit_tower",
    "compile_spec",
    "compose_repairs",
    "decompose_square",
    "default_rank2_tower_2d",
    "dimension_identity",
    "group_average",
    "identity_frame",
    "isotropic_part",
    "orbit_summary",
    "repair_symmetry",
    "repair_trace",
    "symmetric_part",
    "symmetric_traceless_part",
    "validate_tower",
]
