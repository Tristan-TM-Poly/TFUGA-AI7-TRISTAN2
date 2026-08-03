"""Formal-target compiler with explicit incomplete-proof boundaries."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Iterable

from .models import EpistemicStatus, ProblemCell
from .store import atomic_write_json, atomic_write_text


@dataclass(frozen=True)
class FormalTarget:
    target_id: str
    source_cell_id: str
    language: str
    module_name: str
    theorem_name: str
    statement_status: str
    proof_status: str
    source_address: str
    code: str
    dependencies: tuple[str, ...]
    assumptions: tuple[str, ...]
    sorry_count: int
    theorem_claimed: bool = False
    formally_verified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FormalBundleManifest:
    format: str
    language: str
    targets: int
    files: tuple[str, ...]
    aggregate_sha256: str
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def lean_identifier(value: str, *, prefix: str = "vla") -> str:
    normalized = re.sub(r"[^A-Za-z0-9_]", "_", value)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        normalized = prefix
    if normalized[0].isdigit():
        normalized = f"{prefix}_{normalized}"
    return normalized[:120]


def _escape_comment(value: str) -> str:
    return value.replace("/-", "/ -").replace("-/", "- /")


class LeanTargetCompiler:
    """Compile ProblemCells to reviewable Lean skeletons containing `sorry`.

    The translation deliberately does not pretend that natural-language
    hypotheses have been formalized. It creates a traceable target file whose
    incompleteness is machine-readable and visible in the code.
    """

    language = "Lean4"

    def compile(self, cell: ProblemCell) -> FormalTarget:
        module_suffix = lean_identifier(cell.cell_id.replace("vla-cell-", ""))
        module_name = f"OmegaVLA.Generated.Cell_{module_suffix}"
        theorem_name = f"candidate_{module_suffix}"
        target_id = f"lean-target-{sha256(cell.cell_id.encode()).hexdigest()[:20]}"
        hypothesis_comments = "\n".join(
            f"-- hypothesis: {_escape_comment(value)}" for value in cell.hypotheses
        )
        invariant_comments = "\n".join(
            f"-- invariant: {_escape_comment(value)}" for value in cell.invariants
        )
        falsifier_comments = "\n".join(
            f"-- falsifier: {_escape_comment(value)}" for value in cell.falsifiers
        )
        conclusion = _escape_comment(cell.candidate_conclusion)
        address = _escape_comment(cell.address)
        code = f'''/--
Generated Ω-VLA formal target.

Source cell: {cell.cell_id}
Address: {address}

This file is an explicit incomplete skeleton. Natural-language assumptions and
conclusions have NOT been semantically translated into Lean definitions.
-/

set_option autoImplicit false

namespace {module_name}

{hypothesis_comments}
{invariant_comments}
{falsifier_comments}

/-- Natural-language target: {conclusion} -/
def CandidateStatement : Prop := True

/--
Placeholder target only. `sorry` is intentional and prevents any claim of a
completed formal proof. Replace CandidateStatement with a faithful definition,
then discharge every assumption and remove `sorry` before promotion.
-/
theorem {theorem_name} : CandidateStatement := by
  sorry

end {module_name}
'''
        return FormalTarget(
            target_id=target_id,
            source_cell_id=cell.cell_id,
            language=self.language,
            module_name=module_name,
            theorem_name=theorem_name,
            statement_status="NATURAL_LANGUAGE_NOT_FORMALIZED",
            proof_status=EpistemicStatus.FORMALIZED_INCOMPLETE.value,
            source_address=cell.address,
            code=code,
            dependencies=(),
            assumptions=cell.hypotheses,
            sorry_count=1,
            theorem_claimed=False,
            formally_verified=False,
        )

    def compile_many(self, cells: Iterable[ProblemCell]) -> list[FormalTarget]:
        return [self.compile(cell) for cell in cells]

    def write_bundle(
        self,
        targets: Iterable[FormalTarget],
        output_dir: str | Path,
    ) -> FormalBundleManifest:
        root = Path(output_dir)
        root.mkdir(parents=True, exist_ok=True)
        files: list[str] = []
        digests: list[str] = []
        count = 0
        for target in targets:
            file_name = f"{lean_identifier(target.source_cell_id)}.lean"
            path = root / file_name
            atomic_write_text(path, target.code)
            metadata_path = root / f"{file_name}.json"
            atomic_write_json(metadata_path, target.to_dict())
            files.extend((file_name, metadata_path.name))
            digests.extend(
                (
                    sha256(target.code.encode("utf-8")).hexdigest(),
                    sha256(
                        json.dumps(
                            target.to_dict(),
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode("utf-8")
                    ).hexdigest(),
                )
            )
            count += 1
        manifest = FormalBundleManifest(
            format="omega-vla-lean-incomplete-bundle-v1",
            language=self.language,
            targets=count,
            files=tuple(files),
            aggregate_sha256=sha256("".join(digests).encode("ascii")).hexdigest(),
        )
        atomic_write_json(root / "manifest.json", manifest.to_dict())
        return manifest
