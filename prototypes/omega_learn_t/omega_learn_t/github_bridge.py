from __future__ import annotations

from typing import Literal

from .core import ErrorRecord, SkillSpec
from .sage_learning_coach import SageLearningCoach

IssueKind = Literal["learning_goal", "m_minus_error", "oak_test"]


def issue_markdown(spec: SkillSpec, kind: IssueKind = "learning_goal") -> str:
    """Generate GitHub Issue markdown without requiring network credentials."""

    coach = SageLearningCoach()
    report = coach.inspect(spec)
    if kind == "learning_goal":
        return _learning_goal(spec, report)
    if kind == "m_minus_error":
        return _m_minus(spec)
    if kind == "oak_test":
        return _oak_test(spec, report)
    raise ValueError(f"Unsupported issue kind: {kind}")


def _learning_goal(spec: SkillSpec, report: dict) -> str:
    actions = "\n".join(f"- [ ] {x}" for x in report["next_actions"])
    invariants = "\n".join(f"- {x}" for x in report["cvcd"]["invariants"])
    return f"""## Ω-LEARN-T Learning Goal

**Skill:** {spec.skill}
**Goal:** {spec.goal}
**OAK status:** {report['oakbench']['status']}
**Negentropy index:** {report['oakbench']['negentropy_index']:.3f}

### CVCD invariants

{invariants}

### Action plan

{actions}

### OAK gate

- [ ] Solve without notes
- [ ] Solve a new variant
- [ ] Explain simply + formally
- [ ] Capture M⁻ residues
"""


def _m_minus(spec: SkillSpec) -> str:
    if not spec.errors:
        return f"## M⁻ registry for {spec.skill}\n\nNo errors logged yet. Add the first falsifying residue.\n"
    blocks = []
    for err in spec.errors:
        blocks.append(_error_block(err))
    return f"## Ω-LEARN-T M⁻ Registry — {spec.skill}\n\n" + "\n\n".join(blocks)


def _error_block(err: ErrorRecord) -> str:
    return f"""### {err.name}

- **Cause:** {err.cause}
- **Correction:** {err.correction}
- **Future test:** {err.future_test}
- **Severity:** {err.severity}
- **OAK status:** {err.status_oak}
"""


def _oak_test(spec: SkillSpec, report: dict) -> str:
    questions = "\n".join(f"- [ ] {q}" for q in [
        "Résoudre sans notes",
        "Résoudre une variante nouvelle",
        "Expliquer en langage simple et en équations",
        "Identifier une mauvaise solution",
        "Transférer à un autre domaine",
        "Capturer M⁻ et prochaine action",
    ])
    return f"""## Ω-LEARN-T OAK Test — {spec.skill}

**Goal:** {spec.goal}
**Current status:** {report['oakbench']['status']}

### Checklist

{questions}

### Evidence to append

```json
{{"axis": "transfer", "successes": 0, "failures": 0, "source": "oak_test"}}
```
"""
