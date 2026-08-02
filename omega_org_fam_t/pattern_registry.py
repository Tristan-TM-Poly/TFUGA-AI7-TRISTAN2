"""Versioned SMARTS/SMIRKS pattern registry with optional RDKit execution.

Syntax validation here is intentionally conservative and does not certify
chemical correctness. Matching requires RDKit and remains an optional adapter.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Iterable, Mapping

_ALLOWED = re.compile(r"^[A-Za-z0-9@+\-#:=~.(),;!$%*\\/\[\]{}?&>]+$")


def validate_pattern_syntax(pattern: str, *, transformation: bool = False) -> tuple[bool, tuple[str, ...]]:
    errors: list[str] = []
    if not pattern:
        errors.append("empty_pattern")
    if pattern and not _ALLOWED.match(pattern):
        errors.append("unsupported_character")
    for left, right, label in (("[", "]", "bracket"), ("(", ")", "parenthesis"), ("{", "}", "brace")):
        if pattern.count(left) != pattern.count(right):
            errors.append(f"unbalanced_{label}")
    if transformation and pattern.count(">>") != 1:
        errors.append("smirks_requires_single_reaction_arrow")
    if not transformation and ">>" in pattern:
        errors.append("smarts_must_not_contain_reaction_arrow")
    return not errors, tuple(errors)


@dataclass(frozen=True, slots=True)
class PatternRule:
    rule_id: str
    family: str
    smarts: str
    provenance: str
    license: str
    status: str = "candidate_substructure_rule"
    required_elements: tuple[str, ...] = ()
    forbidden_elements: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        valid, errors = validate_pattern_syntax(self.smarts)
        if not valid:
            raise ValueError(f"invalid SMARTS for {self.rule_id}: {errors}")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class TransformationRule:
    rule_id: str
    name: str
    smirks: str
    provenance: str
    license: str
    status: str = "candidate_transformation_template"

    def __post_init__(self) -> None:
        valid, errors = validate_pattern_syntax(self.smirks, transformation=True)
        if not valid:
            raise ValueError(f"invalid SMIRKS for {self.rule_id}: {errors}")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class PatternRegistry:
    def __init__(self, version: str, patterns: Iterable[PatternRule], transformations: Iterable[TransformationRule] = ()):
        self.version = version
        self.patterns = tuple(patterns)
        self.transformations = tuple(transformations)
        ids = [item.rule_id for item in self.patterns + self.transformations]
        if len(ids) != len(set(ids)):
            raise ValueError("pattern rule IDs must be unique")

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "patterns": [item.to_dict() for item in self.patterns],
            "transformations": [item.to_dict() for item in self.transformations],
        }

    def dump(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({**self.to_dict(), "fingerprint": self.fingerprint}, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> "PatternRegistry":
        patterns = tuple(PatternRule(**dict(item)) for item in raw.get("patterns", []) if isinstance(item, dict))
        transformations = tuple(TransformationRule(**dict(item)) for item in raw.get("transformations", []) if isinstance(item, dict))
        return cls(str(raw.get("version", "external")), patterns, transformations)

    @classmethod
    def load(cls, path: Path) -> "PatternRegistry":
        return cls.from_mapping(json.loads(path.read_text(encoding="utf-8")))


def optional_rdkit_match(smiles: str, rule: PatternRule) -> dict[str, object]:
    try:
        from rdkit import Chem  # type: ignore
    except ImportError:
        return {"available": False, "matched": None, "status": "rdkit_not_installed"}
    molecule = Chem.MolFromSmiles(smiles)
    pattern = Chem.MolFromSmarts(rule.smarts)
    if molecule is None or pattern is None:
        return {"available": True, "matched": None, "status": "parse_failure"}
    return {"available": True, "matched": bool(molecule.HasSubstructMatch(pattern)), "status": "computed_match"}


SEED_PATTERN_REGISTRY = PatternRegistry(
    "R0.3-seed",
    (
        PatternRule("smarts-alcohol", "alcohol_phenol", "[OX2H][CX4]", "curated_seed_r03", "CC0", required_elements=("O", "C")),
        PatternRule("smarts-phenol", "alcohol_phenol", "[OX2H]c", "curated_seed_r03", "CC0", required_elements=("O", "C")),
        PatternRule("smarts-carbonyl", "aldehyde_ketone", "[CX3]=[OX1]", "curated_seed_r03", "CC0", required_elements=("C", "O")),
        PatternRule("smarts-carboxylic-acid", "carboxylic_acid", "[CX3](=O)[OX2H1]", "curated_seed_r03", "CC0", required_elements=("C", "O")),
        PatternRule("smarts-ester", "ester_anhydride", "[CX3](=O)[OX2][#6]", "curated_seed_r03", "CC0", required_elements=("C", "O")),
        PatternRule("smarts-amide", "amide_imide", "[NX3][CX3](=[OX1])", "curated_seed_r03", "CC0", required_elements=("N", "C", "O")),
        PatternRule("smarts-amine", "amine_imine", "[NX3;H2,H1,H0;!$(NC=O)]", "curated_seed_r03", "CC0", required_elements=("N",)),
        PatternRule("smarts-nitrile", "nitrile_isocyanate", "[CX2]#N", "curated_seed_r03", "CC0", required_elements=("C", "N")),
        PatternRule("smarts-thiol", "thiol_sulfide", "[SX2H]", "curated_seed_r03", "CC0", required_elements=("S",)),
        PatternRule("smarts-sulfone", "sulfoxide_sulfone", "S(=O)(=O)", "curated_seed_r03", "CC0", required_elements=("S", "O")),
        PatternRule("smarts-halogen", "organohalogen", "[#6][F,Cl,Br,I]", "curated_seed_r03", "CC0", required_elements=("C",)),
        PatternRule("smarts-silicon", "organosilicon", "[#6][Si]", "curated_seed_r03", "CC0", required_elements=("C", "Si")),
    ),
    (
        TransformationRule("smirks-alcohol-carbonyl", "alcohol_to_carbonyl_template", "[C:1][OH:2]>>[C:1]=[O:2]", "curated_seed_r03", "CC0"),
        TransformationRule("smirks-ester-hydrolysis", "ester_hydrolysis_template", "[C:1](=[O:2])[O:3][C:4]>>[C:1](=[O:2])[OH:3].[C:4][OH]", "curated_seed_r03", "CC0"),
    ),
)
