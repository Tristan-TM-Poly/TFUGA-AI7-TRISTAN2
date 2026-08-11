"""Ω-SKILLGEN-T∞ — recursive OAK-safe Agent Skill foundry."""

__version__ = "0.6.0"

from .adversary import enrich_with_adversarial_evals, generate_adversarial_evals
from .arena import ArenaCandidate, arena_report, pareto_front, select_diverse
from .budget import AdaptiveBudget
from .catalog import build_skill_hypergraph, catalog_skills
from .core import SkillSpecError, eval_coverage, evolve_failures, generate_skill, lint_skill, load_json, validate_spec
from .ecology import capability_gap_report, ecology_audit
from .evolution import infer_repair_actions, mminus_to_regression_case, preservation_contracts_from_mplus, repair_from_mminus
from .lineage import lineage_audit, lineage_edges
from .meta import compare_specs, compose_specs, generate_domain_generator, mutate_spec
from .mining import mine_workflows, proposals_from_workflows
from .planner import plan_expansion
from .synthesis import crossover_specs, fission_spec, novelty_against, synthesize_crossovers
from .trust import scan_skill_trust
