"""Shared deterministic data for Ω-MILLENNIUM-T∞ R0.2 generation."""
# Materialization trigger: generator semantics and emitted catalogs are unchanged.
from __future__ import annotations
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]

def write(path:str, value):
    target=ROOT/path
    target.parent.mkdir(parents=True,exist_ok=True)
    if isinstance(value,str):
        target.write_text(value.rstrip()+"\n",encoding="utf-8")
    else:
        target.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")

PROBLEMS={
"poincare":("Poincaré Conjecture","solved_benchmark","Every closed simply connected 3-manifold is homeomorphic to the 3-sphere.",["geometric_topology","geometric_analysis"],["reconstruct_dependency_program"],["ricci_flow","surgery","noncollapsing","geometrization"]),
"riemann":("Riemann Hypothesis","open","Every nontrivial zero of the Riemann zeta function has real part one half.",["analytic_number_theory","spectral_theory"],["prove_critical_line","construct_off_line_zero"],["zeta_function","explicit_formula","positivity","spectral_operator"]),
"p_vs_np":("P versus NP","open","Determine whether every language in NP is decidable in deterministic polynomial time.",["complexity_theory","circuit_complexity"],["prove_p_equals_np","prove_p_not_equal_np"],["reduction","circuit_family","proof_complexity","barriers"]),
"navier_stokes":("Navier–Stokes Existence and Smoothness","open","Establish global smoothness for admissible three-dimensional incompressible data or construct admissible finite-time breakdown.",["partial_differential_equations","fluid_dynamics"],["prove_global_regularity","construct_breakdown"],["velocity","vorticity","critical_space","blowup"]),
"yang_mills":("Yang–Mills Existence and Mass Gap","open","Construct four-dimensional quantum Yang–Mills theory and prove a positive mass gap.",["gauge_theory","constructive_qft"],["construct_theory_and_gap"],["gauge_invariance","continuum_limit","reflection_positivity","spectral_gap"]),
"hodge":("Hodge Conjecture","open","Every rational Hodge class on a smooth projective complex variety is a rational linear combination of algebraic cycle classes.",["algebraic_geometry","cohomology"],["prove_cycle_surjectivity","construct_counterexample"],["variety","hodge_class","cycle_class_map","deformation"]),
"birch_swinnerton_dyer":("Birch and Swinnerton-Dyer Conjecture","open","The rank of rational points equals the order of vanishing of the elliptic-curve L-function at one, with the predicted leading term.",["arithmetic_geometry","elliptic_curves"],["prove_rank_and_leading_term","construct_counterexample"],["elliptic_curve","L_function","selmer_group","sha"]),
}

STRATEGIES=[
"spectral_reformulation","positivity_kernel","trace_formula","renormalization_flow","critical_space_estimate","compactness_rigidity","blowup_contradiction","monotonicity_formula",
"energy_entropy_method","microlocal_analysis","harmonic_analysis","operator_algebra","geometric_measure_theory","algebraic_geometry","arithmetic_geometry","motivic_transfer",
"p_adic_deformation","euler_system","descent_method","selmer_control","circuit_lower_bound","proof_complexity","meta_complexity","communication_complexity",
"pseudorandomness","derandomization","geometric_complexity","representation_stability","lattice_regularization","constructive_field_theory","reflection_positivity","cluster_expansion",
"functional_integral","hamiltonian_reconstruction","spectral_gap_bound","gauge_invariant_observable","ricci_flow","surgery_control","minimal_surface","geometrization",
"local_global_principle","deformation_specialization","cycle_class_map","derived_category","category_theoretic_bridge","homological_algebra","cohomological_descent","intersection_theory",
"computer_assisted_interval","symbolic_identity","formal_proof_search","automated_lemma_synthesis","counterexample_guided_refinement","random_matrix_analogy","statistical_mechanics_bridge","integrable_model",
"discrete_continuum_bridge","finite_model_calibration","inverse_problem","variational_method","convexity_method","duality_transform","information_theoretic_bound","compression_invariant"]

LEMMAS=["existence","uniqueness","regularity","compactness","coercivity","positivity","monotonicity","rigidity","stability","continuity","analyticity","decay","growth","integrability","boundedness","concentration","nonconcentration","localization","delocalization","orthogonality","duality","interpolation","embedding","trace","extension","restriction","approximation","density","spectral_correspondence","gap_lower_bound","resolvent_bound","functional_calculus","normal_form","renormalization","scaling","blowup_exclusion","profile_decomposition","energy_identity","entropy_identity","virial_identity","index_formula","cycle_realization","descent","specialization","deformation","local_global","rank_bound","leading_term","circuit_lower_bound","proof_length_lower_bound","simulation","reduction","hardness_amplification","pseudorandom_generator","derandomization","barrier_escape","gauge_fixing","reflection_positivity","continuum_limit","constructive_measure","surgery_finiteness","noncollapsing","canonical_neighborhood","topology_recovery"]

FALSIFIERS=["boundary_case","degenerate_object","quantifier_flip","hidden_assumption","limit_exchange","compactness_gap","regularity_leak","circular_dependency","numerical_to_exact","finite_to_infinite","restricted_to_general","missing_equivalence_direction","formal_placeholder","source_provenance","definition_drift","notation_collision","scaling_mismatch","dimension_mismatch","sign_error","constant_nonuniformity","branch_cut","domain_error","counterexample_mutation","proof_step_deletion","independent_reconstruction","random_small_model","adversarial_large_parameter","singular_limit","local_global_mismatch","discrete_continuum_mismatch","generic_universal_mismatch","weak_strong_mismatch"]

TARGETS=["lean4","coq","isabelle_hol","hol_light","metamath","agda","smtlib","sage","sympy","interval_arithmetic","sat_certificate","drat","lfsc","mizar","acl2","human_latex"]
