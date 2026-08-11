"""Ω-ROOTFLOW-T∞ — differential, spectral and global geometry of polynomial zeros."""

from .adaptive import AdaptiveContinuationResult, AdaptiveContinuationStep, continue_roots_adaptive
from .basis import SUPPORTED_BASES, BasisConditionAtlas, BasisConditionRecord, basis_to_monomial, basis_values_at, bernstein_to_monomial, conditioning_atlas, monomial_to_basis, monomial_to_bernstein, native_root_jacobian
from .collision_manifold import CollisionTangentSpace, TangentPredictionAudit, audit_tangent_prediction, collision_tangent_space
from .continuation import ContinuationResult, ContinuationStep, continue_roots, match_roots, newton_refine
from .core import RootCondition, basis_root_differential, degree_perturbation_sensitivity, derivative_coefficients, derivative_value, polynomial_value, projective_scaling_residual, root_conditions, root_differential, root_hessian, root_jacobian, root_velocity, roots
from .exact import ExactAlgebraAudit, audit_exact_algebra, exact_coefficients, exact_derivative, exact_determinant, exact_discriminant, exact_monic_gcd, exact_newton_power_sums, exact_polydivmod, exact_resultant
from .exact_hermite import ExactHermiteDesign, ExactMultiClusterTangent, ExactRootCluster, exact_affine_solve, exact_confluent_evaluation, exact_fixed_hermite_matrix, exact_hermite_design, exact_mobile_cluster_matrix, exact_multi_cluster_tangent, exact_nullspace, exact_rank, exact_rref
from .invariants import InvariantAudit, audit_invariants, elementary_symmetric_from_coefficients, elementary_symmetric_from_roots, newton_power_sums, power_sum_jacobian, power_sums_from_roots, residue_moments, triangular_power_sum_sensitivity, vieta_jacobian
from .kinematics import RootKinematicState, RootKinematics, parameter_root_kinematics, taylor_predict_roots
from .monodromy import MonodromyResult, PathTrackingStep, quadratic_square_root_loop, track_coefficient_path
from .monodromy_group import MonodromyGroup, compose_permutations, generate_monodromy_group, identity_permutation, inverse_permutation, permutation_cycles, validate_permutation
from .multicluster import HermiteInverseDesign, MultiClusterPredictionAudit, MultiClusterTangentSpace, RootCluster, audit_multi_cluster_prediction, confluent_evaluation, fixed_cluster_hermite_matrix, hermite_inverse_design, mobile_cluster_constraint_matrix, multi_cluster_tangent_space
from .multiplicity_atlas import ExactMultiplicityAtlas, PartitionLattice, PartitionNeighborhood, SquareFreeFactor, build_partition_lattice, derivative_gcd_tower, exact_multiplicity_atlas, immediate_less_singular, immediate_more_singular, integer_partitions, partition_neighborhood, square_free_decomposition
from .multiplicity_strata import MultiplicityPredictionAudit, MultiplicityTangentSpace, audit_multiplicity_prediction, exact_root_multiplicity, falling_factorial, multiplicity_tangent_space
from .oak import RootFlowAudit, audit_rootflow, finite_difference_root_jacobian
from .projective import ProjectiveRoot, ProjectiveSpectrum, chordal_distance, homogeneous_value, projective_roots
from .projective_flow import ProjectiveFlowResult, ProjectiveFlowStep, cubic_degree_collapse_path, match_projective_roots, track_projective_path
from .puiseux import PuiseuxFit, PuiseuxSample, canonical_collision_family, canonical_puiseux_fit, estimate_puiseux_exponent
from .resultant import CollisionCandidate, DiscriminantAudit, SingleCoefficientCollisionAtlas, audit_discriminant, discriminant_from_resultant, discriminant_from_roots, polynomial_resultant, single_coefficient_collision_atlas, sylvester_matrix
from .spectral import CompanionCrosscheck, InverseDesignResult, InverseDesignStep, LinearizedInverseDesign, SpectralGeometry, audit_spectral_geometry, companion_crosscheck, companion_matrix, inverse_design_roots, linearized_inverse_design, log_abs_discriminant, propagate_root_covariance, root_separations
from .spectral_hgfm import SpectralHGFM, build_spectral_hgfm, compile_projective_flow_hgfm
from .versal import LocalUnfoldingMap, RealifiedTangentSpace, UnfoldingDirection, analyze_unfolding_direction, complex_parameter_realification, local_unfolding_map, local_unfolding_roots, real_parameter_constraint_matrix, real_parameter_tangent_space

__all__ = [name for name in globals() if not name.startswith("_")]
