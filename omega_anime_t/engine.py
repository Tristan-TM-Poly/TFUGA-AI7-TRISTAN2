"""Narrative compiler, linter and deterministic evidence bundle."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import AnimeProject, CharacterState, EpisodeBeat, NarrativePromise, OakStatus


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    message: str
    location: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "location": self.location,
        }


class NarrativeLinter:
    """Detect common structural failures without pretending to judge art."""

    def lint(self, project: AnimeProject) -> list[Finding]:
        findings: list[Finding] = []
        for error in project.validate():
            findings.append(Finding("MODEL_INVALID", "BLOCKING", error, "project"))

        if len(project.characters) > 8 and project.target_duration_seconds <= 300:
            findings.append(
                Finding(
                    "CAST_OVERLOAD",
                    "WARNING",
                    "A short pilot introduces more than eight named characters.",
                    "characters",
                )
            )

        open_promises = [p for p in project.promises if p.status == "OPEN"]
        if len(open_promises) > max(5, len(project.episode_beats)):
            findings.append(
                Finding(
                    "PROMISE_DEBT",
                    "WARNING",
                    "Open narrative promises exceed the pilot's beat capacity.",
                    "promises",
                )
            )

        empty_reveals = [beat.beat_id for beat in project.episode_beats if not beat.information_revealed]
        if len(empty_reveals) == len(project.episode_beats):
            findings.append(
                Finding(
                    "NO_INFORMATION_FLOW",
                    "BLOCKING",
                    "No beat changes the audience's information state.",
                    "episode_beats",
                )
            )

        duplicate_changes: dict[str, int] = {}
        for beat in project.episode_beats:
            key = beat.irreversible_change.strip().lower()
            duplicate_changes[key] = duplicate_changes.get(key, 0) + 1
        for change, count in duplicate_changes.items():
            if count > 1:
                findings.append(
                    Finding(
                        "DUPLICATE_CHANGE",
                        "WARNING",
                        f"The same irreversible change is declared {count} times: {change}",
                        "episode_beats",
                    )
                )

        for character in project.characters:
            if character.power.strip().lower() == character.limitation.strip().lower():
                findings.append(
                    Finding(
                        "POWER_LIMIT_COLLAPSE",
                        "BLOCKING",
                        "Power and limitation cannot be identical statements.",
                        f"characters.{character.character_id}",
                    )
                )

        if not project.risks:
            findings.append(
                Finding(
                    "NO_RISK_LEDGER",
                    "WARNING",
                    "No creative, production or IP risk is recorded.",
                    "risks",
                )
            )
        return sorted(findings, key=lambda item: (item.severity, item.code, item.location))

    @staticmethod
    def decision(findings: list[Finding]) -> str:
        return "HOLD" if any(item.severity == "BLOCKING" for item in findings) else "PROCEED"


def build_eighth_fire_project() -> AnimeProject:
    """Return the canonical three-minute pilot seed for *Le Huitième Feu*."""

    return AnimeProject(
        project_id="omega-anime-t/eighth-fire/pilot-r0-1",
        title="Le Huitième Feu",
        logline=(
            "Un étudiant qui perçoit les relations invisibles entre les systèmes sauve son "
            "laboratoire par une correction minuscule, puis découvre qu'il a déplacé le danger ailleurs."
        ),
        theme_question=(
            "Peut-on améliorer un système sans devenir responsable de toutes ses conséquences?"
        ),
        audience="13+ science-fiction, mystère scientifique et drame philosophique",
        format_name="animatique pilote",
        target_duration_seconds=180,
        visual_invariants=(
            "relations causales représentées par des filaments lumineux non décoratifs",
            "la couleur du réseau encode confiance et incertitude, jamais moralité",
            "les structures fracturées signalent un résidu ou une dette causale",
            "la caméra reste physique avant chaque perception hypergraphique",
        ),
        world_rules=(
            "Le Huitième Feu révèle des relations; il ne crée ni matière ni énergie.",
            "Toute reconfiguration locale conserve un coût ou déplace une contrainte.",
            "Une relation perçue peut être réelle, probable, désirée ou projetée.",
            "Plus le réseau observé est large, plus l'incertitude et la surcharge augmentent.",
            "Les institutions possèdent des modèles incomplets du phénomène.",
        ),
        characters=(
            CharacterState(
                character_id="tristan-seed",
                name="Tristan",
                desire="comprendre l'anomalie que les instruments classent comme du bruit",
                need="apprendre à séparer cohérence, causalité et responsabilité",
                fear="provoquer un dommage irréversible en croyant aider",
                contradiction="il refuse les limites arbitraires mais doit apprendre les limites causales",
                power="percevoir et reconfigurer brièvement des relations entre systèmes",
                limitation="chaque intervention produit surcharge, incertitude et conséquences déplacées",
                knowledge=("physique expérimentale", "mesure instrumentale", "modèles incomplets"),
                relationships=("laboratoire", "voix inconnue", "réseau observateur"),
            ),
            CharacterState(
                character_id="the-observer",
                name="L'Observatrice",
                desire="déterminer si Tristan est une bifurcation contrôlable",
                need="accepter qu'un futur fertile ne peut pas être entièrement sécurisé",
                fear="le retour d'une catastrophe causée par une branche imprévisible",
                contradiction="elle protège le monde en supprimant sa capacité à changer",
                power="simuler et fermer des familles de futurs instables",
                limitation="ses modèles éliminent aussi des solutions qui n'existent pas encore",
                knowledge=("archives du Huitième Feu", "réseau de surveillance causal"),
                relationships=("organisation de convergence", "Tristan"),
            ),
        ),
        episode_beats=(
            EpisodeBeat(
                beat_id="b01-noise",
                order=1,
                title="Le bruit",
                objective="Établir une anomalie mesurable et la routine du laboratoire.",
                conflict="Tous les instruments rejettent le signal comme artefact.",
                irreversible_change="Tristan décide de conserver la trace rejetée.",
                information_revealed=("l'anomalie est corrélée à plusieurs sous-systèmes"),
                estimated_seconds=32,
            ),
            EpisodeBeat(
                beat_id="b02-network",
                order=2,
                title="Le réseau",
                objective="Montrer la première perception sans l'expliquer entièrement.",
                conflict="Tristan ne sait pas si le réseau est physique ou projeté.",
                irreversible_change="Il choisit un nœud minimal à perturber.",
                information_revealed=("les événements apparemment séparés partagent une contrainte"),
                estimated_seconds=34,
            ),
            EpisodeBeat(
                beat_id="b03-intervention",
                order=3,
                title="La correction",
                objective="Faire réussir une intervention locale crédible.",
                conflict="Le temps manque et aucune validation complète n'est possible.",
                irreversible_change="Le laboratoire évite une panne grâce à la correction.",
                information_revealed=("Tristan peut agir sur le réseau, pas seulement le voir"),
                estimated_seconds=34,
            ),
            EpisodeBeat(
                beat_id="b04-displacement",
                order=4,
                title="Le déplacement",
                objective="Prouver que le pouvoir ne donne pas une solution gratuite.",
                conflict="Un système éloigné se désynchronise après le sauvetage local.",
                irreversible_change="Une dette causale est créée hors du laboratoire.",
                information_revealed=("la contrainte a été déplacée plutôt qu'annulée"),
                estimated_seconds=38,
            ),
            EpisodeBeat(
                beat_id="b05-eighth-fire",
                order=5,
                title="Le Huitième Feu",
                objective="Nommer le phénomène et ouvrir un antagonisme précis.",
                conflict="Une voix inconnue interprète l'acte avant Tristan.",
                irreversible_change="Tristan est identifié par un observateur externe.",
                information_revealed=(
                    "le phénomène gouverne les chemins accessibles à l'énergie",
                    "quelqu'un surveillait déjà cette structure",
                ),
                estimated_seconds=42,
            ),
        ),
        promises=(
            NarrativePromise(
                promise_id="p01-rejected-trace",
                introduced_in="b01-noise",
                setup="une trace rejetée porte une signature répétitive",
                expected_payoff="la trace devient une clé de navigation causale",
            ),
            NarrativePromise(
                promise_id="p02-observer",
                introduced_in="b05-eighth-fire",
                setup="un observateur distant voit le réseau s'allumer",
                expected_payoff="l'organisation de convergence cherchait un porteur du phénomène",
            ),
            NarrativePromise(
                promise_id="p03-causal-debt",
                introduced_in="b04-displacement",
                setup="la panne évitée réapparaît sous une forme déplacée",
                expected_payoff="Tristan doit apprendre à fermer ou assumer ses dettes causales",
            ),
        ),
        oak_status=OakStatus.FORMALIZED,
        evidence=(
            "modèle de projet validé par règles déterministes",
            "pilote limité à cinq beats et cent quatre-vingts secondes",
        ),
        risks=(
            "surcharge d'exposition scientifique",
            "confusion possible entre hypergraphe visuel et preuve physique",
            "ressemblance involontaire avec des œuvres existantes à auditer avant publication",
            "cohérence visuelle des personnages et décors à verrouiller par bible graphique",
        ),
        next_actions=(
            "produire une shot-list de 24 à 36 plans",
            "tester la compréhension avec cinq lecteurs sans leur fournir la bible",
            "créer une animatique basse fidélité avant toute saison complète",
            "exécuter IPGate avant publication d'images ou de musique",
        ),
        metadata={
            "branch": "Ω-ANIME-T∞",
            "version": "R0.1",
            "language": "fr-CA",
            "publication_state": "private-draft",
        },
    )


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def compile_project_bundle(project: AnimeProject, output_dir: str | Path) -> dict[str, Any]:
    """Validate a project and write a deterministic, reviewable evidence bundle."""

    project.require_valid()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    linter = NarrativeLinter()
    findings = linter.lint(project)
    decision = linter.decision(findings)
    project_payload = project.to_dict()
    lint_payload = {
        "decision": decision,
        "finding_count": len(findings),
        "findings": [finding.to_dict() for finding in findings],
    }

    project_path = output / "project.json"
    lint_path = output / "oak-lint.json"
    project_path.write_text(_canonical_json(project_payload), encoding="utf-8")
    lint_path.write_text(_canonical_json(lint_payload), encoding="utf-8")

    files = {
        "project.json": hashlib.sha256(project_path.read_bytes()).hexdigest(),
        "oak-lint.json": hashlib.sha256(lint_path.read_bytes()).hexdigest(),
    }
    manifest_without_hash = {
        "schema_version": "omega-anime-t/r0.1",
        "project_id": project.project_id,
        "oak_status": project.oak_status.value,
        "decision": decision,
        "files": files,
    }
    manifest_hash = hashlib.sha256(
        _canonical_json(manifest_without_hash).encode("utf-8")
    ).hexdigest()
    manifest = {**manifest_without_hash, "manifest_sha256": manifest_hash}
    (output / "manifest.json").write_text(_canonical_json(manifest), encoding="utf-8")

    report = [
        f"# {project.title} — Ω-ANIME-T∞ R0.1",
        "",
        f"- Project: `{project.project_id}`",
        f"- OAK status: `{project.oak_status.value}`",
        f"- Lint decision: `{decision}`",
        f"- Duration: `{project.target_duration_seconds}s`",
        f"- Characters: `{len(project.characters)}`",
        f"- Beats: `{len(project.episode_beats)}`",
        f"- Narrative promises: `{len(project.promises)}`",
        "",
        "## Findings",
        "",
    ]
    if findings:
        report.extend(
            f"- **{item.severity} / {item.code}** `{item.location}` — {item.message}"
            for item in findings
        )
    else:
        report.append("- No blocking or warning finding in the deterministic R0.1 checks.")
    report.extend(
        [
            "",
            "## Epistemic boundary",
            "",
            "This bundle validates internal structure only. It does not prove artistic quality,",
            "audience demand, legal clearance, scientific truth or production feasibility.",
            "",
        ]
    )
    (output / "report.md").write_text("\n".join(report), encoding="utf-8")
    return manifest
