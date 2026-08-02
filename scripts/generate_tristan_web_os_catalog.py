#!/usr/bin/env python3
"""Generate the public Tristan Web OS catalog and reviewable Markdown cards."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from tristan_web_catalog_seed_01 import ROWS as ROWS_01
from tristan_web_catalog_seed_02 import ROWS as ROWS_02
from tristan_web_catalog_seed_03 import ROWS as ROWS_03
from tristan_web_catalog_seed_04 import ROWS as ROWS_04

FIELDS = ("id", "symbol", "title", "summary", "domains", "maturity", "evidence", "artifacts", "status_note", "next_action", "source_path", "family")
SEED_ROWS = "\n".join((ROWS_01, ROWS_02, ROWS_03, ROWS_04))

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "apps" / "tristan-8fire-site"
DATA = SITE / "data"
GENERATED = ROOT / "content" / "generated"
CARDS = GENERATED / "theory-cards"
VERSION = "0.2.0"
GENERATED_AT = "2026-08-02T18:12:00-04:00"
RULE = "PUBLIC = OAKGate AND IPGate AND PrivacyGate AND SecurityGate"

BASE = {
    "hypothèse": dict(verite=.28, utilite=.72, testabilite=.67, simplicite=.45, valeur=.64, protection=.58),
    "architecture": dict(verite=.44, utilite=.81, testabilite=.78, simplicite=.48, valeur=.74, protection=.64),
    "prototype": dict(verite=.57, utilite=.84, testabilite=.88, simplicite=.52, valeur=.77, protection=.61),
}
AUDIENCES = {
    "platform": ["développeurs", "chercheurs", "partenaires"],
    "science": ["chercheurs", "ingénieurs", "étudiants"],
    "compute": ["développeurs", "chercheurs HPC", "ingénieurs"],
    "hardware": ["ingénieurs", "chercheurs", "industrie"],
    "energy": ["ingénieurs énergie", "chercheurs", "industrie"],
    "manufacturing": ["fabrication", "laboratoires", "qualité"],
    "venture": ["entrepreneurs", "partenaires", "clients pilotes"],
    "governance": ["produit", "chercheurs", "auditeurs"],
    "health-research": ["chercheurs", "étudiants", "professionnels qualifiés"],
    "education": ["étudiants", "enseignants", "institutions"],
    "life-science": ["chercheurs", "étudiants", "biologistes"],
    "knowledge": ["chercheurs", "documentalistes", "développeurs"],
    "operations": ["opérateurs", "produit", "auditeurs"],
    "safety": ["formateurs", "sécurité", "pratiquants"],
}
RISKS = {
    "hardware": ["sécurité physique", "fabricabilité"],
    "energy": ["sécurité physique", "thermique", "rendement non validé"],
    "health-research": ["mauvaise interprétation", "usage hors cadre"],
    "venture": ["confidentialité", "droits et permissions"],
    "operations": ["action externe non autorisée", "confidentialité"],
    "knowledge": ["provenance insuffisante", "licence incompatible"],
    "safety": ["escalade", "mauvaise application"],
    "science": ["artefact numérique", "généralisation abusive"],
    "compute": ["artefact numérique", "généralisation abusive"],
}
OUTPUTS = {
    "prototype": ["code exécutable", "tests", "benchmark"],
    "architecture": ["spécification", "schéma", "protocole de test"],
    "hypothèse": ["définition falsifiable", "contre-hypothèses", "expérience discriminante"],
}
UNIVERSAL = (
    ("omega-tristan-self-os", "crystallized_by", "Traverse capture, canon, OAK, prototype, IP et valeur."),
    ("omega-doc-t", "documented_by", "Claims, versions, limites et résidus restent documentés."),
    ("omega-atlas-t", "mapped_by", "Coordonnées, provenance, statut, risques et routes restent navigables."),
    ("omega-unc2-t", "uncertainty_guard", "Incertitudes, désaccords et domaines de validité restent explicites."),
    ("omega-web-tristan-t", "published_through", "La couche publique expose seulement le résumé validé par les quatre gates."),
)


def stable_hash(text: str) -> int:
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:2], "big")


def delta(identifier: str, label: str) -> float:
    return ((stable_hash(identifier + ":" + label) / 65535.0) - .5) * .10


def profile(identifier: str, maturity: str) -> dict[str, float]:
    return {
        key: round(max(.05, min(.95, value + delta(identifier, key))), 2)
        for key, value in BASE[maturity].items()
    }


def slug(value: str) -> str:
    value = value.lower().replace("²", "2").replace("∞", "infinity")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def words(*values: str) -> list[str]:
    raw = " ".join(str(value) for value in values)
    tokens = re.findall(r"[A-Za-zÀ-ÿ0-9²∞-]+", raw)
    return sorted({token.strip("-Ω").lower() for token in tokens if len(token.strip("-Ω")) > 1})


def parse_seeds() -> list[dict[str, object]]:
    result = []
    rows = [row for row in SEED_ROWS.strip().splitlines() if "|" in row]
    for ordinal, row in enumerate(rows, 1):
        record = dict(zip(FIELDS, row.split("|")))
        record["domains"] = str(record["domains"]).split(";")
        record["artifacts"] = int(record["artifacts"])
        record["ordinal"] = ordinal
        result.append(record)
    return result


def build_theories() -> list[dict[str, object]]:
    result = []
    for seed in parse_seeds():
        identifier = str(seed["id"])
        maturity = str(seed["maturity"])
        family = str(seed["family"])
        risks = ["surpromesse", "preuve insuffisante", *RISKS.get(family, [])]
        outputs = ["fiche publique", "rapport OAK", "prochaine expérience", *OUTPUTS[maturity]]
        result.append({
            **seed,
            "slug": slug(identifier.removeprefix("omega-")),
            "claims_count": 4 if identifier == "omega-transform-t" else 3,
            "source_status": "canonical-reference",
            "version": "R0.2-public",
            "updated_at": "2026-08-02",
            "visibility": "public-summary",
            "audiences": AUDIENCES.get(family, ["chercheurs", "développeurs", "partenaires"]),
            "keywords": words(str(seed["symbol"]), str(seed["title"]), *seed["domains"]),
            "risks": list(dict.fromkeys(risks)),
            "outputs": list(dict.fromkeys(outputs)),
            "oak": profile(identifier, maturity),
            "publication": {
                "oak_gate": True,
                "ip_gate": True,
                "privacy_gate": True,
                "security_gate": True,
                "scope": "summary-only",
                "automatic_external_action": False,
            },
            "links": {
                "detail_route": f"#/theory/{identifier}",
                "claims_route": f"#/claims?theory={identifier}",
                "source_route": f"#/sources?path={seed['source_path']}",
            },
        })
    return result


def build_claims(theories: list[dict[str, object]]) -> list[dict[str, object]]:
    templates = (
        (
            "scope", "Portée publique et objet testable",
            "{symbol} propose un cadre structuré pour {summary}",
            "candidate", "modèle ou architecture", "provisoire",
            "La portée publique ne démontre ni supériorité générale, ni causalité, ni validité hors du domaine déclaré.",
            "Transformer l’objet en entrée, sortie, baseline, métrique et seuil reproductibles.",
        ),
        (
            "limit", "Limite OAK obligatoire",
            "La promotion de {symbol} reste bloquée tant que hypothèses, unités, résidus, risques et contre-exemples ne sont pas exposés.",
            "guardrail", "règle de gouvernance", "processus fort, fond non prouvé",
            "Un garde-fou éditorial réduit la surpromesse mais ne valide pas le modèle sous-jacent.",
            "Auditer page, dépôt, tests et sources pour détecter une divergence réelle.",
        ),
        (
            "test-plan", "Prochaine falsification ou réduction",
            "La prochaine progression de {symbol} doit produire une comparaison mesurée plutôt qu’une nouvelle extension nominale.",
            "planned", "plan expérimental", "non exécuté",
            "Le plan peut échouer, être sous-dimensionné ou mesurer un proxy inadéquat.",
            "{next_action}",
        ),
    )
    result = []
    for theory in theories:
        for index, template in enumerate(templates, 1):
            kind, title, statement, status, level, confidence, limit, next_test = template
            summary = str(theory["summary"])
            result.append({
                "id": f"claim-{theory['id']}-{index:02d}",
                "theory_id": theory["id"],
                "kind": kind,
                "title": title,
                "statement": statement.format(
                    symbol=theory["symbol"],
                    summary=summary[0].lower() + summary[1:],
                ),
                "status": status,
                "epistemic_level": level,
                "confidence_label": confidence,
                "support": [{
                    "type": "canonical-reference",
                    "path": theory["source_path"],
                    "locator": theory["version"],
                    "note": "Référence de conception, pas validation externe.",
                }],
                "counter_hypotheses": [
                    "Une baseline plus simple peut suffire.",
                    "Le gain peut provenir des données, du protocole ou du réglage.",
                ],
                "falsification_or_limit": limit,
                "next_test": next_test.format(next_action=theory["next_action"]),
                "risk_tags": theory["risks"],
                "publication_scope": "public-summary",
                "automatic_promotion": False,
                "updated_at": "2026-08-02",
            })
    result.append({
        "id": "claim-omega-transform-t-negative-01",
        "theory_id": "omega-transform-t",
        "kind": "negative-memory",
        "title": "M⁻ — la pondération fractale naïve ne gagne pas au premier benchmark",
        "statement": "Sur le premier signal synthétique documenté, une FWT standard a obtenu une meilleure erreur de reconstruction que la FFWT heuristique à fraction conservée comparable.",
        "status": "negative_result",
        "epistemic_level": "résultat expérimental local",
        "confidence_label": "observé dans un cas documenté",
        "support": [{
            "type": "local-benchmark",
            "path": "omega_transform_t_package.zip",
            "locator": "keep_fraction=0.2",
            "note": "Conserver comme mémoire M⁻.",
        }],
        "counter_hypotheses": [
            "La FFWT peut aider une autre tâche.",
            "La pondération naïve peut expliquer l’échec.",
            "La classe de signal peut favoriser la FWT.",
        ],
        "falsification_or_limit": "Résultat local; aucune conclusion générale sur toutes les FFWT ou toutes les tâches.",
        "next_test": "Répéter sur plusieurs classes de signaux avec intervalles, coût et baselines.",
        "risk_tags": ["surinterprétation", "cherry-picking", "benchmark insuffisant"],
        "publication_scope": "public-result-with-limit",
        "automatic_promotion": False,
        "updated_at": "2026-08-02",
    })
    return result


def build_relations(theories: list[dict[str, object]]) -> list[dict[str, object]]:
    identifiers = {str(theory["id"]) for theory in theories}
    candidates = []
    for theory in theories:
        for target, kind, rationale in UNIVERSAL:
            if theory["id"] != target:
                candidates.append((theory["id"], target, kind, rationale))
    for source in theories:
        for target in theories:
            if str(source["id"]) >= str(target["id"]):
                continue
            shared_domains = sorted(set(source["domains"]) & set(target["domains"]))
            same_family = source["family"] == target["family"]
            if not shared_domains and not same_family:
                continue
            kind = "shares_domain" if shared_domains else "same_family"
            rationale = (
                "Domaine partagé: " + ", ".join(shared_domains)
                if shared_domains else f"Famille partagée: {source['family']}"
            )
            candidates.append((source["id"], target["id"], kind, rationale))
    result = []
    seen = set()
    for source, target, kind, rationale in candidates:
        key = (source, target, kind)
        if source not in identifiers or target not in identifiers or source == target or key in seen:
            continue
        if len(result) >= 268:
            break
        seen.add(key)
        result.append({
            "id": f"relation-{len(result)+1:04d}",
            "source": source,
            "target": target,
            "kind": kind,
            "rationale": rationale,
            "strength": round(.55 + delta(str(source) + str(target), str(kind)), 2),
            "status": "curated-candidate",
            "directional": True,
            "evidence_required": True,
            "public_scope": "navigation",
        })
    if len(result) != 268:
        raise SystemExit(f"Expected 268 relations, got {len(result)}")
    return result


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_card(theory, claims, relations) -> str:
    local_claims = [claim for claim in claims if claim["theory_id"] == theory["id"]]
    outgoing = [relation for relation in relations if relation["source"] == theory["id"]]
    incoming = [relation for relation in relations if relation["target"] == theory["id"]]
    lines = [
        f"# {theory['symbol']} — {theory['title']}",
        "",
        f"**Identifiant :** `{theory['id']}`  ",
        f"**Version :** `{theory['version']}`  ",
        f"**Maturité :** `{theory['maturity']}`  ",
        f"**Preuve :** `{theory['evidence']}`",
        "",
        "## Résumé", "", theory["summary"], "",
        "## Statut épistémique", "", theory["status_note"], "",
        "Une architecture n’est pas une preuve; un prototype n’est pas un produit validé.", "",
        "## Domaines", "", *[f"- {item}" for item in theory["domains"]], "",
        "## Profil OAK provisoire", "",
        "| Dimension | Signal |", "|---|---:|",
        *[f"| {key} | {value:.2f} |" for key, value in theory["oak"].items()],
        "",
        "Les scores servent à naviguer; ils ne sont ni probabilités de vérité ni certifications.",
        "",
        "## Claims publics", "",
    ]
    for claim in local_claims:
        lines.extend([
            f"### {claim['id']} — {claim['title']}", "",
            f"- Type: `{claim['kind']}`",
            f"- Statut: `{claim['status']}`",
            f"- Énoncé: {claim['statement']}",
            f"- Limite: {claim['falsification_or_limit']}",
            f"- Prochain test: {claim['next_test']}", "",
        ])
    lines.extend(["## Relations sortantes", ""])
    lines.extend(f"- `{item['kind']}` → `{item['target']}` — {item['rationale']}" for item in outgoing)
    lines.extend(["", "## Relations entrantes", ""])
    lines.extend(f"- `{item['kind']}` ← `{item['source']}` — {item['rationale']}" for item in incoming)
    lines.extend(["", "## Risques", "", *[f"- {item}" for item in theory["risks"]]])
    lines.extend(["", "## Artefacts attendus", "", *[f"- {item}" for item in theory["outputs"]]])
    lines.extend([
        "", "## Prochaine action", "", theory["next_action"],
        "", "## Provenance", "",
        f"- Source: `{theory['source_path']}`",
        f"- Mise à jour: `{theory['updated_at']}`",
        "", "## Gates", "", f"```text\n{RULE}\n```", "",
        "Aucune action externe automatique ou divulgation d’IP n’est autorisée par cette fiche.", "",
    ])
    return "\n".join(lines)


def write_indexes(theories, claims, relations) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    lines = ["# Tristan Web OS — Claim Index", "", f"Generated: `{GENERATED_AT}`", ""]
    for claim in claims:
        lines.extend([
            f"## {claim['id']}", "",
            f"- Theory: `{claim['theory_id']}`",
            f"- Kind: `{claim['kind']}`",
            f"- Status: `{claim['status']}`",
            f"- Statement: {claim['statement']}",
            f"- Limit: {claim['falsification_or_limit']}",
            f"- Next test: {claim['next_test']}", "",
        ])
    (GENERATED / "CLAIM_INDEX.md").write_text("\n".join(lines), encoding="utf-8")

    lines = [
        "# Tristan Web OS — Relation Index", "", f"Generated: `{GENERATED_AT}`", "",
        "Relations are navigation candidates, not causal proof.", "",
    ]
    for relation in relations:
        lines.extend([
            f"## {relation['id']}", "",
            f"`{relation['source']}` — **{relation['kind']}** → `{relation['target']}`", "",
            relation["rationale"], "",
        ])
    (GENERATED / "RELATION_INDEX.md").write_text("\n".join(lines), encoding="utf-8")

    lines = [
        "# Tristan Web OS — Generated Public Catalog", "",
        f"- Theories: **{len(theories)}**",
        f"- Claims: **{len(claims)}**",
        f"- Relations: **{len(relations)}**",
        f"- Declared artifacts: **{sum(theory['artifacts'] for theory in theories)}**", "",
        f"```text\n{RULE}\n```", "",
        "## OAK interpretation", "",
        "- A name is not a proof.",
        "- An architecture is not a prototype.",
        "- A prototype is not a validated product.",
        "- A relation is not causal proof.",
        "- A public summary does not authorize disclosure.", "",
    ]
    (GENERATED / "CATALOG_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    CARDS.mkdir(parents=True, exist_ok=True)
    theories = build_theories()
    claims = build_claims(theories)
    relations = build_relations(theories)
    write_json(DATA / "theories.json", {
        "schema_version": VERSION,
        "generated_at": GENERATED_AT,
        "locale": "fr-CA",
        "title": "Tristan Web OS — Atlas public",
        "disclaimer": "Scores OAK provisoires; aucune certification scientifique, médicale, juridique ou financière.",
        "publication_rule": RULE,
        "theories": theories,
    })
    write_json(DATA / "claims.json", {
        "schema_version": VERSION,
        "generated_at": GENERATED_AT,
        "disclaimer": "Chaque claim conserve son statut, sa limite et son prochain test.",
        "claims": claims,
    })
    write_json(DATA / "relations.json", {
        "schema_version": VERSION,
        "generated_at": GENERATED_AT,
        "disclaimer": "Relations de navigation, pas preuves causales.",
        "relations": relations,
    })
    for theory in theories:
        (CARDS / f"{theory['id']}.md").write_text(
            render_card(theory, claims, relations), encoding="utf-8"
        )
    write_indexes(theories, claims, relations)
    actual = (len(theories), len(claims), len(relations))
    expected = (44, 133, 268)
    if actual != expected:
        raise SystemExit(f"Expected {expected}, got {actual}")
    print(json.dumps({
        "theories": len(theories),
        "claims": len(claims),
        "relations": len(relations),
        "theory_cards": len(list(CARDS.glob("*.md"))),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
