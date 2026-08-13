from __future__ import annotations
from .core import Rule

CANONICAL_KERNELS = frozenset({"SENSE", "MODEL", "TRANSFORM", "VERIFY", "REMEMBER", "MATERIALIZE"})
CANONICAL_RULES = (
    Rule.make("observe-to-model", {"SENSE"}, {"OBSERVATION"}),
    Rule.make("model-state", {"MODEL", "OBSERVATION"}, {"STATE_MODEL"}),
    Rule.make("candidate-transform", {"TRANSFORM", "STATE_MODEL"}, {"CANDIDATE"}),
    Rule.make("verification", {"VERIFY", "CANDIDATE"}, {"EVIDENCE"}),
    Rule.make("memory", {"REMEMBER", "EVIDENCE"}, {"MEMORY_UPDATE"}),
    Rule.make("materialization", {"MATERIALIZE", "EVIDENCE"}, {"VERIFIED_ARTIFACT"}),
    Rule.make("learning-loop", {"MEMORY_UPDATE", "STATE_MODEL"}, {"COMPILER_FEEDBACK"}),
)
TARGET_DERIVED = frozenset({"OBSERVATION", "STATE_MODEL", "CANDIDATE", "EVIDENCE", "MEMORY_UPDATE", "VERIFIED_ARTIFACT", "COMPILER_FEEDBACK"})
