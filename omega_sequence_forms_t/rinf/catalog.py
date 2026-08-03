"""Deterministic 256/512/1024 R∞ catalog factory.

The catalog is generated from scientifically meaningful seeds and orthogonal
variants.  This provides a large, stable logical address space without copying
thousands of nearly identical source files into the repository.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import json
from typing import Iterable, Iterator

from .models import (
    AnalyticFamily,
    AntiPatternSpec,
    EvidenceLevel,
    FamilyClass,
    Maturity,
    TransformationClass,
    TransformationSpec,
    canonical_digest,
)


FAMILY_VARIANTS: tuple[str, ...] = (
    "scalar_exact",
    "scalar_noisy",
    "vector_exact",
    "multivariate_exact",
    "modular",
    "symbolic_parameter",
    "piecewise",
    "asymptotic_residual",
)

TRANSFORMATION_MODES: tuple[str, ...] = (
    "forward",
    "inverse",
    "restricted",
    "multivariate",
    "modular",
    "symbolic",
    "numerical_guarded",
    "residual_aware",
)

ANTIPATTERN_CONTEXTS: tuple[str, ...] = (
    "exact_integer",
    "exact_rational",
    "floating_point",
    "complex",
    "multivariate",
    "modular",
    "asymptotic",
    "formal_bridge",
)


@dataclass(frozen=True)
class FamilySeed:
    slug: str
    label: str
    family_class: FamilyClass
    representation: str
    detector: str
    compiler: str
    invariants: tuple[str, ...]
    obligations: tuple[str, ...]
    risks: tuple[str, ...]
    exact_capable: bool
    multivariate_capable: bool = False


@dataclass(frozen=True)
class TransformationSeed:
    slug: str
    label: str
    transformation_class: TransformationClass
    source: tuple[FamilyClass, ...]
    target: tuple[FamilyClass, ...]
    exact_when: tuple[str, ...]
    obligations: tuple[str, ...]
    risks: tuple[str, ...]
    invertible: bool = False
    lossy: bool = False


@dataclass(frozen=True)
class AntiPatternSeed:
    slug: str
    name: str
    detector: str
    countercheck: str
    severity: int
    block: EvidenceLevel
    explanation: str


FAMILY_SEEDS: tuple[FamilySeed, ...] = (
    FamilySeed("newton_polynomial", "Newton polynomial", FamilyClass.EXPLICIT, "a_n=sum_k c_k binom(n,k)", "finite_difference_rank", "newton_to_ordinary_gf", ("difference_order", "integer_valued_basis"), ("prove_difference_termination", "validate_index_origin"), ("vacuous_interpolation",), True),
    FamilySeed("quasi_polynomial", "Quasi-polynomial", FamilyClass.EXPLICIT, "a_n=P_{n mod m}(n)", "periodic_difference_search", "quasi_to_rational_gf", ("period", "branch_degrees"), ("prove_period", "cover_all_residue_classes"), ("short_period_alias",), True),
    FamilySeed("rational_index", "Rational function of n", FamilyClass.EXPLICIT, "a_n=P(n)/Q(n)", "rational_interpolation", "rational_index_normal_form", ("numerator_degree", "denominator_degree", "poles"), ("exclude_singular_indices", "prove_reduced_fraction"), ("pole_cancellation", "rational_overfit"), True),
    FamilySeed("exp_polynomial", "Exponential polynomial", FamilyClass.SPECTRAL, "a_n=sum_j P_j(n) lambda_j^n", "hankel_prony", "spectral_to_recurrence", ("spectral_rank", "root_multiplicity"), ("prove_characteristic_factorization",), ("near_colliding_roots",), True),
    FamilySeed("constant_recurrence", "Constant-coefficient recurrence", FamilyClass.RECURRENT, "sum_j c_j a_{n+j}=0", "minimal_hankel_recurrence", "recurrence_to_rational_gf", ("order", "hankel_rank"), ("prove_all_n", "validate_initial_conditions"), ("high_order_memorization",), True),
    FamilySeed("p_recursive", "P-recursive sequence", FamilyClass.RECURRENT, "sum_j p_j(n)a_{n+j}=0", "ore_guess", "ore_to_dfinite", ("order", "coefficient_degree", "singular_indices"), ("prove_operator_annihilation",), ("insufficient_equations", "apparent_singularity"), True),
    FamilySeed("hypergeometric", "Hypergeometric term", FamilyClass.EXPLICIT, "a_{n+1}/a_n=R(n)", "ratio_rational_fit", "ratio_to_gamma_pochhammer", ("ratio_degrees", "zero_pattern"), ("handle_zeros", "prove_ratio_identity"), ("division_by_zero",), True),
    FamilySeed("q_hypergeometric", "q-hypergeometric term", FamilyClass.EXPLICIT, "a_{n+1}/a_n=R(q^n)", "q_ratio_fit", "q_ratio_to_products", ("q_parameter", "ratio_degrees"), ("identify_q_domain",), ("q_aliasing",), True),
    FamilySeed("rational_ogf", "Rational ordinary generating function", FamilyClass.GENERATING, "A(z)=P(z)/Q(z)", "pade_exact", "ogf_to_recurrence", ("pole_locations", "denominator_degree"), ("prove_formal_series_identity",), ("analytic_formal_confusion",), True),
    FamilySeed("algebraic_ogf", "Algebraic generating function", FamilyClass.GENERATING, "P(z,A(z))=0", "algebraic_lift_relation", "algebraic_to_p_recursive", ("algebraic_degree", "branch"), ("select_correct_branch", "prove_initial_series"), ("branch_cut",), True),
    FamilySeed("dfinite_ogf", "D-finite generating function", FamilyClass.GENERATING, "sum_k q_k(z)A^(k)(z)=0", "differential_operator_guess", "dfinite_to_p_recursive", ("operator_order", "polynomial_degree"), ("prove_differential_annihilator",), ("operator_nonminimality",), True),
    FamilySeed("differential_algebraic", "Differentially algebraic generating function", FamilyClass.GENERATING, "P(z,A,A',...)=0", "nonlinear_differential_lift", "dalg_certificate", ("jet_order", "algebraic_degree"), ("prove_nonlinear_identity",), ("lift_explosion",), False),
    FamilySeed("exponential_gf", "Exponential generating function", FamilyClass.GENERATING, "E(z)=sum_n a_n z^n/n!", "egf_operator_guess", "egf_to_recurrence", ("analytic_order", "factorial_scaling"), ("prove_coefficient_extraction",), ("factorial_overflow",), True),
    FamilySeed("dirichlet_series", "Dirichlet generating series", FamilyClass.ARITHMETIC, "D(s)=sum_n a_n n^{-s}", "dirichlet_feature_search", "dirichlet_to_euler", ("abscissa", "multiplicativity"), ("prove_convergence_domain",), ("formal_analytic_confusion",), False),
    FamilySeed("multiplicative", "Multiplicative arithmetic sequence", FamilyClass.ARITHMETIC, "a_{mn}=a_ma_n for gcd(m,n)=1", "coprime_product_audit", "prime_power_reconstruction", ("prime_power_table",), ("prove_coprime_identity",), ("finite_prime_bias",), True),
    FamilySeed("dirichlet_convolution", "Dirichlet convolution form", FamilyClass.ARITHMETIC, "a=b*c", "divisor_convolution_factor", "mobius_inversion", ("divisor_support",), ("prove_factorization",), ("nonunique_factorization",), True),
    FamilySeed("automatic", "k-automatic sequence", FamilyClass.AUTOMATIC, "a_n=output(automaton(digits_k(n)))", "k_kernel_minimization", "automaton_to_linear_representation", ("base", "state_count"), ("prove_kernel_finiteness",), ("base_dependence",), True),
    FamilySeed("k_regular", "k-regular sequence", FamilyClass.AUTOMATIC, "v(kn+r)=M_r v(n)", "kernel_module_rank", "regular_to_matrix_product", ("module_rank", "base"), ("prove_matrix_representation",), ("rank_alias",), True),
    FamilySeed("morphic", "Morphic sequence", FamilyClass.AUTOMATIC, "w=limit sigma^n(a)", "substitution_inference", "morphism_to_automaton", ("alphabet_size", "substitution_length"), ("prove_fixed_point",), ("prefix_nonidentifiability",), True),
    FamilySeed("nonlinear_recurrence", "Nonlinear recurrence", FamilyClass.RECURRENT, "a_{n+r}=F(n,a_n,...)", "polynomial_rational_lift", "recurrence_to_tensor_lift", ("order", "nonlinear_degree"), ("prove_domain_invariance",), ("chaotic_sensitivity",), False),
    FamilySeed("koopman_lift", "Koopman/Carleman lifted dynamics", FamilyClass.OPERATOR, "Phi(x_{n+1})=K Phi(x_n)+R", "sparse_operator_fit", "lift_to_recurrence", ("lift_degree", "residual_norm"), ("bound_truncation_residual",), ("truncation_as_exact",), False, True),
    FamilySeed("moment_sequence", "Moment sequence", FamilyClass.INTEGRAL, "a_n=int x^n dmu(x)", "hankel_positivity", "moments_to_j_fraction", ("hankel_signatures", "support_rank"), ("prove_measure_existence",), ("indeterminate_moment_problem",), False),
    FamilySeed("orthogonal_polynomial", "Orthogonal-polynomial coefficients", FamilyClass.RECURRENT, "P_{n+1}=(x-alpha_n)P_n-beta_nP_{n-1}", "three_term_recurrence", "recurrence_to_measure", ("jacobi_parameters",), ("prove_positivity_beta",), ("signed_measure",), True),
    FamilySeed("continued_fraction", "Continued-fraction generating form", FamilyClass.GENERATING, "A(z)=JFrac(alpha,beta)", "pade_j_fraction", "fraction_to_moments", ("convergents", "jacobi_parameters"), ("prove_fraction_identity",), ("spurious_pade_pattern",), True),
    FamilySeed("integral_representation", "Integral representation", FamilyClass.INTEGRAL, "a_n=int_Gamma f(z)g(z)^n dz", "moment_kernel_search", "integral_to_asymptotic", ("contour", "kernel"), ("justify_contour_and_exchange",), ("illegal_sum_integral_swap",), False),
    FamilySeed("mellin_laplace", "Mellin/Laplace representation", FamilyClass.INTEGRAL, "a_n=M^{-1}[F](n)", "transform_signature", "transform_to_asymptotic", ("poles", "residues"), ("prove_inversion_domain",), ("contour_shift_gap",), False),
    FamilySeed("classical_asymptotic", "Classical asymptotic expansion", FamilyClass.ASYMPTOTIC, "C lambda^n n^alpha log(n)^beta sum c_k n^{-k/q}", "ratio_richardson", "singularity_to_asymptotic", ("growth_base", "power", "log_power"), ("state_remainder",), ("asymptotic_as_equality",), False),
    FamilySeed("transseries", "Transseries", FamilyClass.ASYMPTOTIC, "sum_j exp(-phi_j(n)) n^alpha_j series_j", "multi_scale_residual", "borel_resurgent_bridge", ("sectors", "stokes_data"), ("state_summability",), ("sector_overfit",), False),
    FamilySeed("stochastic_process", "Stochastic sequence model", FamilyClass.STOCHASTIC, "a_n=f(n)+epsilon_n", "distributional_model_selection", "process_to_moments", ("mean", "covariance", "regime"), ("calibrate_uncertainty",), ("noise_as_structure",), False, True),
    FamilySeed("matrix_tensor", "Matrix/tensor recurrence", FamilyClass.MULTIVARIATE, "X_{n+1}=F(X_n)", "tensor_rank_operator_fit", "tensor_to_scalar_invariants", ("rank", "spectrum", "symmetry"), ("prove_shape_and_domain",), ("flattening_artifact",), False, True),
    FamilySeed("multivariate_gf", "Multivariate generating function", FamilyClass.MULTIVARIATE, "A(z_1,...,z_d)=sum a_n z^n", "multivariate_operator_guess", "diagonal_extraction", ("dimension", "singular_variety"), ("prove_domain_and_diagonal",), ("diagonal_alias",), False, True),
    FamilySeed("algorithmic_program", "Algorithmic description", FamilyClass.ALGORITHMIC, "a_n=Program(n)", "program_synthesis_guarded", "program_to_invariants", ("description_length", "time_complexity"), ("prove_program_equivalence",), ("memorizing_program",), True),
)


TRANSFORMATION_SEEDS: tuple[TransformationSeed, ...] = (
    TransformationSeed("shift", "Index shift", TransformationClass.INDEX, tuple(FamilyClass), tuple(FamilyClass), ("integer_shift",), ("track_initial_conditions",), ("index_origin",), True),
    TransformationSeed("decimate", "Arithmetic subsequence", TransformationClass.INDEX, tuple(FamilyClass), tuple(FamilyClass), ("positive_stride",), ("prove_subsequence_mapping",), ("aliasing",), False),
    TransformationSeed("affine_index", "Affine index map", TransformationClass.INDEX, tuple(FamilyClass), tuple(FamilyClass), ("integral_indices",), ("track_domain",), ("missing_indices",), False),
    TransformationSeed("finite_difference", "Forward difference", TransformationClass.DIFFERENCE, tuple(FamilyClass), tuple(FamilyClass), ("sequence_defined",), ("track_boundary",), ("noise_amplification",), False),
    TransformationSeed("partial_sum", "Partial summation", TransformationClass.DIFFERENCE, tuple(FamilyClass), tuple(FamilyClass), ("summable_prefix",), ("fix_constant",), ("constant_ambiguity",), False),
    TransformationSeed("binomial", "Binomial transform", TransformationClass.DIFFERENCE, tuple(FamilyClass), tuple(FamilyClass), ("finite_coefficients",), ("prove_inversion",), ("sign_convention",), True),
    TransformationSeed("mobius", "Möbius inversion", TransformationClass.ARITHMETIC, (FamilyClass.ARITHMETIC,), (FamilyClass.ARITHMETIC,), ("divisor_finite",), ("prove_convolution_domain",), ("index_zero",), True),
    TransformationSeed("dirichlet_convolution", "Dirichlet convolution", TransformationClass.CONVOLUTION, (FamilyClass.ARITHMETIC,), (FamilyClass.ARITHMETIC,), ("finite_divisors",), ("prove_factorization",), ("factor_nonuniqueness",), False),
    TransformationSeed("cauchy_convolution", "Cauchy convolution", TransformationClass.CONVOLUTION, tuple(FamilyClass), tuple(FamilyClass), ("finite_coefficient_sum",), ("prove_coefficient_product",), ("radius_of_convergence",), False),
    TransformationSeed("hadamard_product", "Hadamard product", TransformationClass.CONVOLUTION, tuple(FamilyClass), tuple(FamilyClass), ("pointwise_defined",), ("prove_closure",), ("closure_failure",), False),
    TransformationSeed("recurrence_to_ogf", "Recurrence to OGF", TransformationClass.COMPILATION, (FamilyClass.RECURRENT,), (FamilyClass.GENERATING,), ("linear_recurrence",), ("derive_numerator",), ("initial_condition_loss",), False),
    TransformationSeed("ogf_to_recurrence", "OGF to recurrence", TransformationClass.COMPILATION, (FamilyClass.GENERATING,), (FamilyClass.RECURRENT,), ("formal_series",), ("coefficient_extract",), ("analytic_formal_confusion",), False),
    TransformationSeed("p_recursive_to_dfinite", "P-recursive to D-finite", TransformationClass.COMPILATION, (FamilyClass.RECURRENT,), (FamilyClass.GENERATING,), ("characteristic_zero",), ("translate_boundary_terms",), ("operator_convention",), True),
    TransformationSeed("hypergeom_to_gamma", "Ratio to Gamma/Pochhammer", TransformationClass.COMPILATION, (FamilyClass.EXPLICIT,), (FamilyClass.EXPLICIT,), ("factorable_ratio",), ("track_exceptional_indices",), ("gamma_poles",), False),
    TransformationSeed("prony", "Prony spectral reconstruction", TransformationClass.SPECTRAL, tuple(FamilyClass), (FamilyClass.SPECTRAL,), ("finite_exponential_rank",), ("certify_hankel_rank",), ("root_collision",), False),
    TransformationSeed("z_transform", "Z transform", TransformationClass.GENERATING, tuple(FamilyClass), (FamilyClass.GENERATING,), ("formal_or_convergent",), ("state_interpretation",), ("roc_omission",), False),
    TransformationSeed("borel", "Borel transform", TransformationClass.GENERATING, (FamilyClass.ASYMPTOTIC,), (FamilyClass.GENERATING,), ("coefficient_growth_known",), ("prove_summability",), ("summation_ambiguity",), False),
    TransformationSeed("mellin", "Mellin transform", TransformationClass.INTEGRAL, tuple(FamilyClass), (FamilyClass.INTEGRAL,), ("integrability_strip",), ("prove_strip_and_inversion",), ("pole_crossing",), False),
    TransformationSeed("laplace", "Laplace transform", TransformationClass.INTEGRAL, tuple(FamilyClass), (FamilyClass.INTEGRAL,), ("exponential_order",), ("prove_inversion",), ("distribution_terms",), False),
    TransformationSeed("coefficient_extract", "Coefficient extraction", TransformationClass.SYMBOLIC, (FamilyClass.GENERATING,), tuple(FamilyClass), ("formal_series",), ("prove_indexing",), ("off_by_one",), False),
    TransformationSeed("series_reversion", "Series reversion", TransformationClass.SYMBOLIC, (FamilyClass.GENERATING,), (FamilyClass.GENERATING,), ("nonzero_linear_term",), ("prove_composition_identity",), ("branch_selection",), True),
    TransformationSeed("lagrange_inversion", "Lagrange inversion", TransformationClass.SYMBOLIC, (FamilyClass.GENERATING,), tuple(FamilyClass), ("implicit_function_conditions",), ("prove_local_branch",), ("singular_derivative",), False),
    TransformationSeed("diagonal", "Diagonal extraction", TransformationClass.GENERATING, (FamilyClass.MULTIVARIATE,), (FamilyClass.GENERATING,), ("formal_multiseries",), ("prove_diagonal_map",), ("dimension_alias",), False),
    TransformationSeed("tensor_lift", "Tensor/Carleman lift", TransformationClass.SYMBOLIC, tuple(FamilyClass), (FamilyClass.OPERATOR,), ("finite_truncation",), ("bound_residual",), ("truncation_as_exact",), False, True),
    TransformationSeed("koopman_fit", "Koopman operator fit", TransformationClass.SPECTRAL, tuple(FamilyClass), (FamilyClass.OPERATOR,), ("observable_basis_declared",), ("validate_out_of_sample",), ("basis_leakage",), False, True),
    TransformationSeed("residualize", "Residual extraction", TransformationClass.RESIDUAL, tuple(FamilyClass), tuple(FamilyClass), ("candidate_evaluable",), ("preserve_provenance",), ("error_structure_loss",), False),
    TransformationSeed("residual_recurse", "Residual form recursion", TransformationClass.RESIDUAL, tuple(FamilyClass), tuple(FamilyClass), ("positive_compression_gain",), ("track_total_model",), ("double_counting",), False),
    TransformationSeed("symbolic_normalize", "Symbolic normal form", TransformationClass.SYMBOLIC, tuple(FamilyClass), tuple(FamilyClass), ("rewrite_rules_sound",), ("prove_rule_set",), ("branch_unsafe_rewrite",), False),
    TransformationSeed("operator_factor", "Operator factorization", TransformationClass.SYMBOLIC, (FamilyClass.OPERATOR, FamilyClass.RECURRENT), (FamilyClass.OPERATOR,), ("ore_domain_declared",), ("check_noncommutative_order",), ("left_right_factor_confusion",), False),
    TransformationSeed("singularity_analysis", "Singularity to asymptotic", TransformationClass.COMPILATION, (FamilyClass.GENERATING,), (FamilyClass.ASYMPTOTIC,), ("dominant_singularities_known",), ("justify_transfer_theorem",), ("competing_singularities",), False),
    TransformationSeed("richardson", "Richardson extrapolation", TransformationClass.VALUE, tuple(FamilyClass), (FamilyClass.ASYMPTOTIC,), ("expansion_scale_known",), ("validate_order",), ("wrong_correction_power",), False),
    TransformationSeed("ratio_log", "Log-ratio transform", TransformationClass.VALUE, tuple(FamilyClass), tuple(FamilyClass), ("nonzero_terms",), ("track_sign_phase",), ("zero_and_branch",), False),
    TransformationSeed("normalize_scale", "Scale normalization", TransformationClass.VALUE, tuple(FamilyClass), tuple(FamilyClass), ("scale_nonzero",), ("record_scale",), ("lost_units",), True),
    TransformationSeed("modular_projection", "Modular projection", TransformationClass.ARITHMETIC, tuple(FamilyClass), tuple(FamilyClass), ("integer_coefficients",), ("reconstruct_or_bound",), ("modular_false_positive",), False, True),
    TransformationSeed("crt_reconstruct", "CRT reconstruction", TransformationClass.ARITHMETIC, tuple(FamilyClass), tuple(FamilyClass), ("coprime_moduli",), ("prove_size_bound",), ("insufficient_modulus",), True),
    TransformationSeed("rational_reconstruct", "Rational reconstruction", TransformationClass.ARITHMETIC, tuple(FamilyClass), tuple(FamilyClass), ("height_bound",), ("verify_exactly",), ("ambiguous_fraction",), False),
    TransformationSeed("pslq_relation", "Integer-relation search", TransformationClass.SYMBOLIC, tuple(FamilyClass), tuple(FamilyClass), ("precision_budget_declared",), ("recheck_high_precision",), ("precision_hallucination",), False),
    TransformationSeed("hankel_rank", "Hankel rank transform", TransformationClass.SPECTRAL, tuple(FamilyClass), (FamilyClass.SPECTRAL,), ("exact_or_interval_arithmetic",), ("certify_rank",), ("numerical_rank_threshold",), False),
    TransformationSeed("fft", "Discrete Fourier analysis", TransformationClass.SPECTRAL, tuple(FamilyClass), (FamilyClass.SPECTRAL,), ("uniform_grid",), ("state_window",), ("spectral_leakage",), False),
    TransformationSeed("wavelet", "Wavelet multi-scale analysis", TransformationClass.SPECTRAL, tuple(FamilyClass), tuple(FamilyClass), ("basis_declared",), ("validate_reconstruction",), ("basis_selection_bias",), True),
    TransformationSeed("ffwt", "Fractal wavelet analysis", TransformationClass.SPECTRAL, tuple(FamilyClass), tuple(FamilyClass), ("prototype_basis_declared",), ("benchmark_against_wavelets",), ("fractal_overinterpretation",), False),
    TransformationSeed("moment_hankel", "Moment Hankel map", TransformationClass.INTEGRAL, tuple(FamilyClass), (FamilyClass.INTEGRAL,), ("moments_finite",), ("test_positivity",), ("finite_minor_insufficiency",), False),
    TransformationSeed("j_fraction", "J-fraction compilation", TransformationClass.COMPILATION, (FamilyClass.INTEGRAL, FamilyClass.GENERATING), (FamilyClass.GENERATING,), ("nonzero_hankel_determinants",), ("prove_convergents",), ("degenerate_minor",), False),
    TransformationSeed("active_index", "Active discriminating index", TransformationClass.PROOF, tuple(FamilyClass), tuple(FamilyClass), ("multiple_candidates",), ("record_selection_criterion",), ("selection_bias",), False),
    TransformationSeed("counterexample_search", "Counterexample search", TransformationClass.PROOF, tuple(FamilyClass), tuple(FamilyClass), ("candidate_executable",), ("state_search_domain",), ("finite_search_as_proof",), False),
    TransformationSeed("induction_bridge", "Induction proof skeleton", TransformationClass.PROOF, tuple(FamilyClass), tuple(FamilyClass), ("recurrence_or_explicit_form",), ("prove_base_and_step",), ("missing_domain",), False),
    TransformationSeed("formal_export", "Formal proof export", TransformationClass.PROOF, tuple(FamilyClass), tuple(FamilyClass), ("typed_statement",), ("leave_no_placeholders_for_completion",), ("placeholder_as_proof",), False),
    TransformationSeed("bayes_update", "Bayesian family update", TransformationClass.PROOF, tuple(FamilyClass), tuple(FamilyClass), ("priors_declared",), ("calibrate_probabilities",), ("posterior_as_truth",), False),
    TransformationSeed("mdl_rank", "Minimum-description ranking", TransformationClass.PROOF, tuple(FamilyClass), tuple(FamilyClass), ("coding_scheme_declared",), ("compare_same_data",), ("coding_bias",), False),
    TransformationSeed("pareto_front", "Pareto frontier extraction", TransformationClass.PROOF, tuple(FamilyClass), tuple(FamilyClass), ("objectives_declared",), ("retain_nondominated",), ("hidden_weighting",), False),
    TransformationSeed("unit_check", "Dimensional/unit audit", TransformationClass.PROOF, tuple(FamilyClass), tuple(FamilyClass), ("units_available",), ("propagate_units",), ("dimensionless_assumption",), True),
    TransformationSeed("domain_partition", "Domain partition", TransformationClass.INDEX, tuple(FamilyClass), tuple(FamilyClass), ("partition_covers_domain",), ("prove_disjoint_or_manage_overlap",), ("boundary_gap",), False),
    TransformationSeed("change_point", "Change-point segmentation", TransformationClass.RESIDUAL, tuple(FamilyClass), tuple(FamilyClass), ("segment_cost_declared",), ("validate_heldout_segments",), ("oversegmentation",), False),
    TransformationSeed("mixture", "Mixture decomposition", TransformationClass.RESIDUAL, tuple(FamilyClass), tuple(FamilyClass), ("component_grammar_declared",), ("prevent_double_counting",), ("nonidentifiable_mixture",), False),
    TransformationSeed("symmetry_quotient", "Symmetry quotient", TransformationClass.SYMBOLIC, tuple(FamilyClass), tuple(FamilyClass), ("group_action_declared",), ("prove_invariance",), ("false_symmetry",), False),
    TransformationSeed("noether_residue", "Noether-style residual", TransformationClass.PROOF, tuple(FamilyClass), tuple(FamilyClass), ("action_or_invariant_declared",), ("separate_analogy_from_theorem",), ("physical_overclaim",), False),
    TransformationSeed("round_trip", "Representation round trip", TransformationClass.PROOF, tuple(FamilyClass), tuple(FamilyClass), ("both_compilers_available",), ("compare_canonical_forms",), ("lossy_roundtrip",), True),
    TransformationSeed("cross_language", "Cross-language oracle", TransformationClass.PROOF, tuple(FamilyClass), tuple(FamilyClass), ("implementations_independent",), ("compare_exact_receipts",), ("shared_bug",), False),
    TransformationSeed("interval_certify", "Interval certification", TransformationClass.PROOF, tuple(FamilyClass), tuple(FamilyClass), ("directed_rounding",), ("enclose_all_results",), ("unsound_interval_backend",), False),
    TransformationSeed("property_test", "Property-based validation", TransformationClass.PROOF, tuple(FamilyClass), tuple(FamilyClass), ("generator_domain_declared",), ("retain_counterexamples",), ("biased_generator",), False),
    TransformationSeed("mutation_test", "Mutation falsification", TransformationClass.PROOF, tuple(FamilyClass), tuple(FamilyClass), ("mutants_semantically_distinct",), ("measure_kill_rate",), ("equivalent_mutant",), False),
    TransformationSeed("provenance_bind", "Provenance binding", TransformationClass.PROOF, tuple(FamilyClass), tuple(FamilyClass), ("source_hash_available",), ("bind_claim_to_input",), ("stale_source",), True),
    TransformationSeed("receipt_chain", "Evidence receipt chain", TransformationClass.PROOF, tuple(FamilyClass), tuple(FamilyClass), ("canonical_serialization",), ("verify_hash_chain",), ("nondeterministic_payload",), True),
    TransformationSeed("compression_loop", "LOG/EXP compression loop", TransformationClass.RESIDUAL, tuple(FamilyClass), tuple(FamilyClass), ("reconstruction_metric",), ("separate_generation_from_proof",), ("hallucinated_reconstruction",), False),
    TransformationSeed("cvcd_extract", "CVCD invariant extraction", TransformationClass.RESIDUAL, tuple(FamilyClass), tuple(FamilyClass), ("invariants_operationalized",), ("benchmark_predictive_value",), ("vague_invariant",), False),
    TransformationSeed("oak_gate", "OAK promotion gate", TransformationClass.PROOF, tuple(FamilyClass), tuple(FamilyClass), ("evidence_graph_complete",), ("enforce_level_requirements",), ("manual_override_without_receipt",), False),
    TransformationSeed("mminus_update", "Negative-memory update", TransformationClass.PROOF, tuple(FamilyClass), tuple(FamilyClass), ("failure_reproducible",), ("store_minimal_counterexample",), ("poisoned_memory",), False),
)


ANTI_PATTERN_SEEDS: tuple[AntiPatternSeed, ...] = (
    AntiPatternSeed("vacuous_interpolation", "Vacuous interpolation", "degree_near_sample_count", "withhold_points_and_penalize_degree", 5, EvidenceLevel.OBSERVED_FIT, "Any finite prefix has a polynomial interpolant; this does not identify the continuation."),
    AntiPatternSeed("high_order_memorization", "High-order recurrence memorization", "order_near_half_sample_count", "require_overdetermination_and_holdout", 5, EvidenceLevel.OBSERVED_FIT, "A recurrence can merely encode the observed prefix."),
    AntiPatternSeed("numerical_to_exact", "Numerical relation promoted to exact", "floating_relation_without_certificate", "reconstruct_rationally_and_substitute_exactly", 5, EvidenceLevel.HELD_OUT_PREDICTION, "Floating agreement is not an exact identity."),
    AntiPatternSeed("asymptotic_as_equality", "Asymptotic used as equality", "asymptotic_marker_missing", "require_remainder_or_ratio_limit", 5, EvidenceLevel.OBSERVED_FIT, "An asymptotic expansion requires a stated limiting meaning."),
    AntiPatternSeed("finite_search_as_proof", "Finite search used as proof", "global_claim_with_finite_range", "require_symbolic_or_formal_argument", 5, EvidenceLevel.ADVERSARIAL_VALIDATION, "Checking many indices cannot prove a universal identity by itself."),
    AntiPatternSeed("branch_cut", "Untracked analytic branch", "multivalued_function_without_branch", "declare_branch_and_domain", 4, EvidenceLevel.HELD_OUT_PREDICTION, "Roots and logarithms require explicit branch choices."),
    AntiPatternSeed("domain_error", "Domain mismatch", "candidate_undefined_on_required_index", "audit_all_singular_indices", 5, EvidenceLevel.OBSERVED_FIT, "A candidate must be defined on the claimed domain."),
    AntiPatternSeed("index_origin", "Index-origin drift", "shifted_fit_equally_plausible", "test_n0_n1_and_render_origin", 4, EvidenceLevel.HELD_OUT_PREDICTION, "Off-by-one conventions can change every formula."),
    AntiPatternSeed("short_period_alias", "Short-window periodic alias", "period_supported_by_few_cycles", "require_many_cycles_and_remote_indices", 4, EvidenceLevel.OBSERVED_FIT, "A short prefix may imitate a period it does not continue."),
    AntiPatternSeed("modular_false_positive", "Modular false positive", "identity_only_mod_primes", "crt_reconstruct_with_height_bound_and_exact_check", 5, EvidenceLevel.HELD_OUT_PREDICTION, "Agreement modulo several primes may still fail over the integers."),
    AntiPatternSeed("precision_hallucination", "Precision-dependent constant recognition", "pslq_relation_changes_with_precision", "repeat_at_higher_precision_and_complexity_bounds", 5, EvidenceLevel.OBSERVED_FIT, "Integer-relation searches require precision and coefficient-height controls."),
    AntiPatternSeed("operator_nonminimality", "Nonminimal annihilator", "operator_has_removable_factor", "factor_and_compare_solution_spaces", 3, EvidenceLevel.SYMBOLIC_IDENTITY, "A valid but nonminimal operator can obscure the actual mechanism."),
    AntiPatternSeed("apparent_singularity", "Apparent singularity misread", "leading_coefficient_zero", "analyze_local_solution_and_desingularize", 4, EvidenceLevel.SYMBOLIC_IDENTITY, "Operator singularities may be removable or may restrict the recurrence domain."),
    AntiPatternSeed("illegal_exchange", "Illegal limit/sum/integral exchange", "exchange_without_dominance", "supply_dominated_or_uniform_convergence_argument", 5, EvidenceLevel.SYMBOLIC_IDENTITY, "Formal manipulation is not automatically analytically justified."),
    AntiPatternSeed("formal_placeholder", "Formal placeholder presented as proof", "sorry_admit_or_axiom_placeholder", "reject_completion_claim", 5, EvidenceLevel.MATHEMATICAL_PROOF, "A proof skeleton with placeholders is not a completed formal proof."),
    AntiPatternSeed("nonidentifiable_mixture", "Non-identifiable mixture", "multiple_component_decompositions", "report_equivalence_class_and_active_index", 4, EvidenceLevel.HELD_OUT_PREDICTION, "Different component mixtures may explain the same observations."),
)


@lru_cache(maxsize=1)
def build_family_catalog() -> tuple[AnalyticFamily, ...]:
    if len(FAMILY_SEEDS) != 32:
        raise RuntimeError("R∞ family seed count drifted from 32")
    catalog: list[AnalyticFamily] = []
    for seed_index, seed in enumerate(FAMILY_SEEDS):
        for variant_index, variant in enumerate(FAMILY_VARIANTS):
            index = seed_index * len(FAMILY_VARIANTS) + variant_index
            exact = seed.exact_capable and variant not in {"scalar_noisy", "asymptotic_residual"}
            multi = seed.multivariate_capable or variant in {"vector_exact", "multivariate_exact"}
            catalog.append(
                AnalyticFamily(
                    family_id=f"family.{index:03d}.{seed.slug}.{variant}",
                    index=index,
                    label=f"{seed.label} [{variant}]",
                    family_class=seed.family_class,
                    representation=seed.representation,
                    detector_ids=(seed.detector, f"variant.{variant}"),
                    compiler_ids=(seed.compiler,),
                    invariants=seed.invariants + (f"variant:{variant}",),
                    proof_obligations=seed.obligations + ("finite_prefix_nonuniqueness",),
                    risk_tags=seed.risks + (("noise_model",) if variant == "scalar_noisy" else ()),
                    maturity=Maturity.PROTOTYPE if variant == "scalar_exact" else Maturity.SPECIFICATION,
                    exact_capable=exact,
                    multivariate_capable=multi,
                    notes="Generated deterministically from a canonical R∞ seed and orthogonal data regime.",
                )
            )
    if len(catalog) != 256 or len({item.family_id for item in catalog}) != 256:
        raise RuntimeError("family catalog must contain 256 unique entries")
    return tuple(catalog)


@lru_cache(maxsize=1)
def build_transformation_catalog() -> tuple[TransformationSpec, ...]:
    if len(TRANSFORMATION_SEEDS) != 64:
        raise RuntimeError(f"R∞ transformation seed count drifted from 64: {len(TRANSFORMATION_SEEDS)}")
    catalog: list[TransformationSpec] = []
    for seed_index, seed in enumerate(TRANSFORMATION_SEEDS):
        for mode_index, mode in enumerate(TRANSFORMATION_MODES):
            index = seed_index * len(TRANSFORMATION_MODES) + mode_index
            inverse_mode = mode == "inverse"
            catalog.append(
                TransformationSpec(
                    transformation_id=f"transform.{index:03d}.{seed.slug}.{mode}",
                    index=index,
                    label=f"{seed.label} [{mode}]",
                    transformation_class=seed.transformation_class,
                    source_classes=seed.source,
                    target_classes=seed.target,
                    exact_when=seed.exact_when + (f"mode:{mode}",),
                    proof_obligations=seed.obligations + ("preserve_provenance",),
                    risk_tags=seed.risks + (("inverse_not_guaranteed",) if inverse_mode and not seed.invertible else ()),
                    invertible=seed.invertible and inverse_mode,
                    lossy=seed.lossy or mode in {"numerical_guarded", "residual_aware"},
                    maturity=Maturity.PROTOTYPE if mode == "forward" else Maturity.SPECIFICATION,
                )
            )
    if len(catalog) != 512 or len({item.transformation_id for item in catalog}) != 512:
        raise RuntimeError("transformation catalog must contain 512 unique entries")
    return tuple(catalog)


@lru_cache(maxsize=1)
def build_antipattern_catalog() -> tuple[AntiPatternSpec, ...]:
    if len(ANTI_PATTERN_SEEDS) != 16:
        raise RuntimeError("R∞ anti-pattern seed count drifted from 16")
    # 16 seeds × 8 contexts × 8 deterministic mutations = 1,024 entries.
    mutations = (
        "base",
        "boundary",
        "remote_index",
        "precision",
        "subsequence",
        "parameter",
        "multimodel",
        "roundtrip",
    )
    catalog: list[AntiPatternSpec] = []
    index = 0
    for seed in ANTI_PATTERN_SEEDS:
        for context in ANTIPATTERN_CONTEXTS:
            for mutation in mutations:
                severity = min(5, max(1, seed.severity + (1 if mutation == "boundary" else 0)))
                catalog.append(
                    AntiPatternSpec(
                        antipattern_id=f"mminus.{index:04d}.{seed.slug}.{context}.{mutation}",
                        index=index,
                        name=f"{seed.name} [{context}/{mutation}]",
                        context=context,
                        detector=f"{seed.detector}:{mutation}",
                        countercheck=f"{seed.countercheck}:{context}",
                        severity=severity,
                        blocks_promotion_above=seed.block,
                        explanation=seed.explanation,
                    )
                )
                index += 1
    if len(catalog) != 1024 or len({item.antipattern_id for item in catalog}) != 1024:
        raise RuntimeError("anti-pattern catalog must contain 1,024 unique entries")
    return tuple(catalog)


def catalog_payload() -> dict[str, object]:
    families = build_family_catalog()
    transforms = build_transformation_catalog()
    anti = build_antipattern_catalog()
    sections = {
        "families": canonical_digest(item.to_dict() for item in families),
        "transformations": canonical_digest(item.to_dict() for item in transforms),
        "antipatterns": canonical_digest(item.to_dict() for item in anti),
    }
    combined = sha256(json.dumps(sections, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return {
        "schema": "omega-sequence-forms-rinf-catalog/1",
        "counts": {
            "families": len(families),
            "transformations": len(transforms),
            "antipatterns": len(anti),
        },
        "digests": sections,
        "catalog_digest": combined,
        "permanent_total_cap": None,
        "global_identity_proved": False,
    }


def iter_catalog_records() -> Iterator[dict[str, object]]:
    for item in build_family_catalog():
        yield {"record_type": "family", **item.to_dict()}
    for item in build_transformation_catalog():
        yield {"record_type": "transformation", **item.to_dict()}
    for item in build_antipattern_catalog():
        yield {"record_type": "antipattern", **item.to_dict()}


def assert_catalog_invariants() -> None:
    payload = catalog_payload()
    expected = {"families": 256, "transformations": 512, "antipatterns": 1024}
    if payload["counts"] != expected:
        raise AssertionError(f"catalog count mismatch: {payload['counts']!r}")
    ids = []
    ids.extend(item.family_id for item in build_family_catalog())
    ids.extend(item.transformation_id for item in build_transformation_catalog())
    ids.extend(item.antipattern_id for item in build_antipattern_catalog())
    if len(ids) != len(set(ids)):
        raise AssertionError("catalog IDs are not globally unique")
