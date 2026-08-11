"""Ω-SKILLGEN-T∞ — recursive OAK-safe Agent Skill foundry."""
__version__ = "0.2.0"
from .core import SkillSpecError, load_json, validate_spec, generate_skill, lint_skill, eval_coverage, evolve_failures
from .meta import compose_specs, generate_domain_generator, mutate_spec, compare_specs
from .mining import mine_workflows, proposals_from_workflows
from .catalog import catalog_skills, build_skill_hypergraph
from .trust import scan_skill_trust
