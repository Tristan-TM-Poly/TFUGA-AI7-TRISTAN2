from .kernel import MactCompiler
from .models import EpistemicType, EvidenceRef, ResourceVector, TransformationCandidate, VerificationContract


def build_demo():
    evidence = [EvidenceRef("ev-1", EpistemicType.MEASURED, "demo", independent=True)]
    return [
        TransformationCandidate("none", "NO_ACTION", "unchanged", ResourceVector(), evidence=evidence),
        TransformationCandidate("wait", "WAIT", "defer", ResourceVector(time=0.2), evidence=evidence),
        TransformationCandidate("reuse", "REUSE", "same-output", ResourceVector(compute=0.1, memory_persistent=0.1), evidence=evidence, rollback="discard cache"),
        TransformationCandidate("compute", "COMPUTE", "same-output", ResourceVector(compute=4.0, time=1.0), evidence=evidence, rollback="discard result"),
    ]


def main() -> int:
    candidates = build_demo()
    compiler = MactCompiler()
    selected = compiler.select(candidates, VerificationContract(required_scope="demo"))
    print(selected.id if selected else "HOLD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
