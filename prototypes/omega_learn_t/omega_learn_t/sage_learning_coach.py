from __future__ import annotations

from typing import Any, Dict

from .bayes_mastery import mastery_vector, update_mastery
from .core import LearningProfile, SkillSpec
from .curriculum_cvcd import generate_curriculum
from .cvcd import extract_invariants
from .m_minus_registry import MMinusRegistry
from .memory_codec import cards_from_errors, cards_from_invariants, oak_cards, schedule_cards
from .oakbench_learn import oak_questions, oakbench
from .scheduler import build_review_queue


class SageLearningCoach:
    """Zero-touch orchestrator for Ω-LEARN-T.

    It converts one skill specification into: CVCD invariants, Bayes mastery,
    M⁻ registry, curriculum, memory cards, scheduler queue, and OAKBench status.
    """

    def inspect(self, spec: SkillSpec) -> Dict[str, Any]:
        signature = extract_invariants(" ".join([spec.skill, spec.goal, spec.notes]))
        mastery = mastery_vector(spec.evidence)
        registry = MMinusRegistry(spec.errors)
        oak = oakbench(mastery, spec.evidence, registry)
        plan = generate_curriculum(mastery, signature.invariants, spec.goal)
        profile = LearningProfile(
            spec=spec,
            mastery=mastery,
            invariants=signature.invariants,
            residues=signature.residues,
            next_actions=plan,
            oak_status=oak.status,
            negentropy_index=oak.negentropy_index,
        )
        return {
            "skill": spec.skill,
            "goal": spec.goal,
            "tags": spec.tags,
            "mastery": {axis.value: round(score, 3) for axis, score in mastery.items()},
            "bayes_posteriors": {
                axis.value: {"alpha": post.alpha, "beta": post.beta, "mean": round(post.mean, 3), "uncertainty": round(post.uncertainty, 3)}
                for axis, post in update_mastery(spec.evidence).items()
            },
            "cvcd": {
                "invariants": signature.invariants,
                "residues": signature.residues,
                "compression_ratio": round(signature.compression_ratio, 3),
                "token_entropy": round(signature.token_entropy, 3),
            },
            "m_minus": registry.to_dicts(),
            "oakbench": oak.to_dict(),
            "next_actions": profile.next_actions,
        }

    def coach(self, spec: SkillSpec) -> Dict[str, Any]:
        report = self.inspect(spec)
        cards = cards_from_invariants(spec.skill, report["cvcd"]["invariants"][:6], spec.tags)
        cards.extend(cards_from_errors(spec.errors, spec.tags))
        cards.extend(oak_cards(spec.skill, oak_questions()[:3], spec.tags))
        queue = build_review_queue(
            skill=spec.skill,
            mastery=mastery_vector(spec.evidence),
            invariants=report["cvcd"]["invariants"],
            errors=spec.errors,
            tags=spec.tags,
        )
        return {
            **report,
            "oak_questions": oak_questions(),
            "memory_cards_due": schedule_cards(cards, days_from_now=1),
            "review_queue": [task.to_dict() for task in queue],
        }

    def summarize_markdown(self, spec: SkillSpec) -> str:
        report = self.coach(spec)
        lines = [f"# Ω-LEARN-T Report — {report['skill']}", ""]
        lines.append(f"**Goal:** {report['goal']}")
        lines.append(f"**OAK status:** {report['oakbench']['status']}")
        lines.append(f"**Negentropy index:** {report['oakbench']['negentropy_index']:.3f}")
        lines.append("\n## Weak/strong mastery vector")
        for axis, score in report["mastery"].items():
            lines.append(f"- {axis}: {score}")
        lines.append("\n## CVCD invariants")
        for inv in report["cvcd"]["invariants"]:
            lines.append(f"- {inv}")
        lines.append("\n## Next actions")
        for action in report["next_actions"]:
            lines.append(f"- {action}")
        lines.append("\n## Review queue")
        for task in report["review_queue"][:10]:
            lines.append(f"- {task['due']} | p={task['priority']:.2f} | {task['prompt']}")
        lines.append("\n## OAK questions")
        for q in report["oak_questions"]:
            lines.append(f"- {q}")
        return "\n".join(lines)
