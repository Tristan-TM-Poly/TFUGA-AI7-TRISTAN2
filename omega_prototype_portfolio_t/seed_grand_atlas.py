"""Ω-PROTOTYPE-PORTFOLIO-T∞ R0.2 Grand Atlas seed.

The original R0.1 showcase remains intact. This shard adds conservative pointers
for major systems, lineages, repositories, campaigns and product hypotheses that
were absent from the 23-object seed. A pointer is not a validation claim.
"""
from __future__ import annotations

from typing import Mapping

from .seed import action, dims, ev, p, sigs

GRAND_ATLAS_MINIMUM = 131

FAMILY_SPECS = {'epistemic-constitution': [('evidence-reactor', 'Ω-EVIDENCE-REACTOR-T∞', 'ttm', 'PR#640', 'EVIDENCE_SYSTEM', 'tested'),
                             ('research-fabric', 'Ω-TRISTAN-RESEARCH-FABRIC-T', 'ttm', 'PR#666', 'EVIDENCE_SYSTEM', 'tested'),
                             ('claim-lifecycle', 'Ω-OMNIDOMAIN Claim Lifecycle R0.4', 'ttm', 'PR#622', 'GOVERNANCE', 'tested'),
                             ('memory-canon', 'Ω-MEMORY-CANON-T∞', 'ttm', 'PR#703', 'MEMORY', 'tested'),
                             ('ip-github', 'Ω-IP-GITHUB-T', 'ttm', 'PR#636', 'GOVERNANCE', 'tested'),
                             ('release-gravity', 'Ω-RELEASE-GRAVITY-T', 'ttm', 'PR#644', 'GOVERNANCE', 'structured'),
                             ('auto-evidence-foundry', 'Ω-AUTO-EVIDENCE-FOUNDRY-T', 'ttm', 'PR#672', 'FOUNDRY', 'tested'),
                             ('compensation-engine', 'Ω-COMPENSATION-T∞', 'ttm', 'PR#647', 'ENGINE', 'benchmarked'),
                             ('meta-search', 'Ω-META-SEARCH-T', 'ttm', 'PR#648', 'ENGINE', 'benchmarked')],
 'github-os': [('github-control-plane', 'Ω-GITHUB-CONTROL-PLANE-T', 'ttm', 'PR#670', 'OS', 'benchmarked'),
               ('github-repair-diagnosis', 'Ω-GITHUB-REPAIR-T', 'ttm', 'PR#698', 'ENGINE', 'tested'),
               ('pr-completion-os', 'Ω-PR-COMPLETION-OS-T∞', 'ttm', 'PR#688', 'OS', 'tested'),
               ('merged-pr-atlas', 'Ω-MERGED-PR-ATLAS-T∞', 'ttm', 'PR#699', 'MEMORY', 'tested'),
               ('github-work-audit', 'Ω-GITHUB-WORK-AUDIT-T', 'ttm', 'PR#681', 'CAMPAIGN', 'benchmarked'),
               ('ci-routing', 'Ω-CI-ROUTING-T', 'ttm', 'PR#702', 'GOVERNANCE', 'tested'),
               ('proof-autonomy', 'Ω-PROOF-AUTONOMY-T∞', 'main', 'PR#345', 'OS', 'tested'),
               ('gitmycelium', 'GitMyceliumOS-T', 'ttm', 'PR#653', 'OS', 'tested'),
               ('frontgraph-os', 'FrontGraphOS-T', 'ttm', 'PR#649', 'OS', 'benchmarked')],
 'generative-forges': [('metaforge', 'Ω-MÉTAFORGE-T∞', 'ttm', 'PR#629', 'FOUNDRY', 'tested'),
                       ('theory-to-proof', 'TheoryToProofForge-T', 'ttm', 'PR#637', 'FOUNDRY', 'benchmarked'),
                       ('openai-tristan-foundry', 'Ω-OPENAI-TRISTAN-FOUNDRY-T', 'ttm', 'PR#624', 'FOUNDRY', 'tested'),
                       ('intent-compiler', 'Ω-INTENT-COMPILER-T∞', 'ttm', 'PR#684', 'ENGINE', 'benchmarked'),
                       ('discovery-kernel', 'Ω-DISCOVERY-KERNEL-T∞', 'ttm', 'PR#680', 'FOUNDRY', 'benchmarked'),
                       ('experiment-evolve', 'Ω-EXPERIMENT-EVOLVE-T∞', 'ttm', 'PR#687', 'CAMPAIGN', 'benchmarked'),
                       ('sci-pub-auto', 'Ω-SCI-PUB-AUTO-T∞', 'ttm', 'PR#690', 'FOUNDRY', 'benchmarked'),
                       ('software-factory', 'Ω-SOFTWARE-FACTORY-T', 'tfug', 'registry:software-factory', 'FOUNDRY', 'structured'),
                       ('generator-discovery', 'Ω-GENERATOR-DISCOVERY-T', 'main', 'registry:generator-discovery', 'FOUNDRY', 'structured')],
 'mathematics': [('tensor-repair', 'Ω-TENSOR-REPAIR-T∞', 'main', 'registry:tensor-repair', 'ENGINE', 'structured'),
                 ('vla-typed-ir', 'Ω-VLA-T Typed IR', 'main', 'PR#316', 'KERNEL', 'tested'),
                 ('vla-operator-universe', 'Ω-VLA-T Operator Universe', 'main', 'PR#319', 'ENGINE', 'tested'),
                 ('millennium-atlas', 'Ω-MILLENNIUM-ATLAS-T', 'ttm', 'registry:millennium', 'LAB', 'structured'),
                 ('prime-value', 'Ω-PRIME-VALUE-T∞', 'main', 'registry:prime-value', 'FOUNDRY', 'structured'),
                 ('zeta-mandel', 'Ω-ZETA-MANDEL-T', 'main', 'registry:zeta-mandel', 'LAB', 'structured'),
                 ('probability-tristan', 'Ω-PROBABILITY-T∞', 'ttm', 'registry:probability', 'THEORY', 'structured'),
                 ('prime-factorization', 'Ω-PRIME-FACTORIZATION-T', 'ttm', 'registry:prime-factorization', 'ENGINE', 'structured'),
                 ('analytic-sequence-forms', 'Ω-ANALYTIC-SEQUENCE-FORMS-T', 'main', 'registry:analytic-sequences', 'LAB', 'structured')],
 'physical-science': [('fluid-tristan', 'Ω-FLUID-T', 'main', 'registry:fluid', 'LAB', 'structured'),
                      ('symflu-manifold', 'SymFluManifold-T', 'main', 'registry:symflu', 'ENGINE', 'structured'),
                      ('plasma-tristan', 'Ω-PLASMA-T', 'main', 'registry:plasma', 'LAB', 'structured'),
                      ('aero-hydro-propulsion', 'Ω-AERO-HYDRO-PROPULSION-T', 'main', 'registry:propulsion', 'LAB', 'structured'),
                      ('cyber-physical-systems', 'Ω-CYBER-PHYSICAL-SYSTEMS-T', 'main', 'registry:cps', 'OS', 'structured'),
                      ('particles-fields', 'Ω-PARTICLES-FIELDS-T∞', 'main', 'registry:particles-fields', 'THEORY', 'structured'),
                      ('gravity-tristan', 'Ω-GRAV-T', 'tfug', 'registry:gravity', 'THEORY', 'structured'),
                      ('solid-tristan', 'Ω-SOLID-T∞', 'tfug', 'registry:solids', 'LAB', 'structured'),
                      ('additive-manufacturing', 'Ω-3DP-T', 'tfug', 'registry:3dp', 'LAB', 'structured')],
 'spectroscopy-inference': [('raman-foundry', 'Ω-RAMAN-FOUNDRY-T', 'ttm', 'PR#625', 'LAB', 'benchmarked'),
                            ('raman-jointfit', 'Ω-RAMAN-JOINTFIT-T', 'ttm', 'PR#626', 'ENGINE', 'benchmarked'),
                            ('raman-known-methods', 'Ω-RAMAN-KNOWN-METHODS-T', 'ttm', 'PR#627', 'LAB', 'benchmarked'),
                            ('raman-exact-solvers', 'Ω-RAMAN-EXACT-SOLVERS-T', 'ttm', 'PR#628', 'LAB', 'benchmarked'),
                            ('raman-external-evidence', 'Ω-RAMAN-EXTERNAL-EVIDENCE-T', 'ttm', 'PR#638', 'DATASET', 'tested'),
                            ('universal-inference', 'Ω-UNIVERSAL-INFERENCE-FABRIC-T∞', 'ttm', 'PR#675', 'ENGINE', 'tested'),
                            ('sciinv', 'Ω-SCIINV-T', 'ttm', 'PR#685', 'LAB', 'tested'),
                            ('ffwt-hac', 'Ω-FFWT-HAC-CVCD', 'tfug', 'registry:ffwt-hac', 'ENGINE', 'structured'),
                            ('calibration-tristan', 'Ω-CALIB-T', 'tfug', 'registry:calibration', 'LAB', 'structured')],
 'knowledge-memory': [('hypercube-compiler', 'Ω-HYPERCUBE-COMPILER-T', 'ttm', 'PR#632', 'ENGINE', 'tested'),
                      ('hypercube-autopilot', 'Ω-HYPERCUBE-AUTOPILOT-T', 'ttm', 'PR#632', 'OS', 'tested'),
                      ('tlkf', 'Ω-TLKF-T', 'ttm', 'PR#623', 'FOUNDRY', 'tested'),
                      ('chatgpt-conversation-corpus', 'ChatGPT Conversation Corpus Ω', 'ttm', 'PR#661', 'MEMORY', 'tested'),
                      ('chatgpt-chrome-archive', 'Ω-CHATGPT-CHROME-ARCHIVE-T', 'ttm', 'PR#652', 'PRODUCT', 'tested'),
                      ('chatgpt-vault-exporter', 'Ω-CHGPT-VAULT-T', 'ttm', 'PR#686', 'PRODUCT', 'tested'),
                      ('advances-atlas-2026', 'Ω-2026-ADVANCES-ATLAS-T', 'ttm', 'PR#673', 'EVIDENCE_SYSTEM', 'structured'),
                      ('atlas-c4', 'Ω-ATLAS-T C4', 'ttm', 'PR#683', 'OS', 'tested'),
                      ('living-thesis-os', 'Ω-LIVING-THESIS-OS-T', 'ttm', 'registry:living-thesis', 'FOUNDRY', 'structured')],
 'venture-corporate': [('startup-r2', 'Ω-STARTUP-T∞ R2', 'ttm', 'PR#695', 'VENTURE', 'tested'),
                       ('oak-audit-offer', 'OAK Repo Audit Express', 'ttm', 'PR#654', 'SERVICE', 'tested'),
                       ('company-autopilot', 'Ω-COMPANY-AUTOPILOT-T', 'main', 'registry:company-autopilot', 'OS', 'structured'),
                       ('company-policy-atlas', 'Ω-COMPANY-POLICY-ATLAS-T', 'main', 'registry:company-policy', 'GOVERNANCE', 'structured'),
                       ('mail-os', 'Ω-MAIL-T', 'main', 'registry:mail', 'OS', 'structured'),
                       ('legal-production-os', 'Ω-LEGAL-PRODUCTION-OS-T', 'main', 'registry:legal-production', 'OS', 'structured'),
                       ('intercompany-mesh', 'Ω-INTERCOMPANY-MESH-T', 'main', 'registry:intercompany', 'OS', 'structured'),
                       ('company-outreach', 'Ω-COMPANY-OUTREACH-T', 'main', 'registry:outreach', 'SERVICE', 'structured'),
                       ('github-revenue', 'Ω-GITHUB-REVENUE-T', 'main', 'registry:github-revenue', 'ENGINE', 'structured')],
 'learning-creative': [('gameengine-tristan', 'Ω-GAMEENGINE-T', 'tfug', 'registry:gameengine', 'ENGINE', 'structured'),
                       ('gamemaster-tristan', 'Ω-GAMEMASTER-T', 'tfug', 'registry:gamemaster', 'ENGINE', 'structured'),
                       ('anime-studio', 'Ω-ANIME-STUDIO-T', 'main', 'registry:anime-studio', 'FOUNDRY', 'structured'),
                       ('learning-tristan', 'Ω-LEARN-T', 'tfug', 'registry:learn', 'OS', 'structured'),
                       ('mahouka-map', 'Ω-MAHOUKA-TRISTAN MAP', 'ttm', 'PR#629', 'THEORY', 'structured'),
                       ('omni-fiction-forge', 'Ω-OMNI-FICTION-FORGE-T∞', 'ttm', 'PR#629', 'FOUNDRY', 'structured'),
                       ('signal-genome', 'SignalGenome++', 'tfug', 'PR#60', 'ENGINE', 'tested'),
                       ('stark-tech-atlas', 'Ω-STARK-TECH-ATLAS-T∞', 'tfug', 'PR#337', 'LAB', 'tested'),
                       ('daily-omega', 'Daily Ω', 'tfug', 'PR#60', 'OS', 'tested')],
 'web-data': [('websearch-tristan', 'Ω-WEBSEARCH-T', 'tfug', 'registry:websearch', 'ENGINE', 'structured'),
              ('open-evidence-foundry', 'Ω-OPEN-EVIDENCE-FOUNDRY-T', 'ttm', 'PR#672', 'FOUNDRY', 'tested'),
              ('datalock', 'DataLock-T', 'ttm', 'PR#672', 'EVIDENCE_SYSTEM', 'tested'),
              ('source-trust-ledger', 'SourceTrustLedger-T', 'tfug', 'registry:source-trust', 'EVIDENCE_SYSTEM', 'structured'),
              ('synthetic-source-detector', 'SyntheticSourceDetector-T', 'tfug', 'registry:synthetic-source', 'ENGINE', 'structured'),
              ('evidence-vault', 'EvidenceVault-T', 'tfug', 'registry:evidence-vault', 'MEMORY', 'structured'),
              ('chrome-extension-foundry', 'Ω-CHROME-EXT-GEN-T', 'ttm', 'PR#671', 'FOUNDRY', 'benchmarked'),
              ('web-hg-source-adapters', 'Ω-WEB-HG Source Adapters', 'main', 'PR#321', 'ENGINE', 'tested'),
              ('research-provider-adapters', 'Research Provider Adapters', 'ttm', 'registry:research-providers', 'ENGINE', 'structured')],
 'civilization-governance': [('omnidomain', 'Ω-OMNIDOMAIN-T', 'ttm', 'PR#621', 'OS', 'tested'),
                             ('polyverse-foundry', 'Ω-POLYVERSE-FOUNDRY-T', 'ttm', 'PR#620', 'OS', 'structured'),
                             ('front-parallel', 'Ω-FRONT-PARALLÈLE-T', 'ttm', 'PR#634', 'OS', 'benchmarked'),
                             ('convergence-os', 'Ω-CONVERGENCE-OS-T', 'main', 'registry:convergence', 'OS', 'structured'),
                             ('tristan-self-os', 'Ω-TRISTAN-SELF-OS', 'tfug', 'registry:self-os', 'OS', 'structured'),
                             ('corp-jarvis', 'Ω-CORP-JARVIS-T', 'tfug', 'registry:corp-jarvis', 'OS', 'structured'),
                             ('auto2', 'Ω-AUTO²-T', 'tfug', 'registry:auto2', 'OS', 'structured'),
                             ('action-ext', 'Ω-ACTION-EXT-T', 'tfug', 'registry:action-ext', 'OS', 'structured'),
                             ('asset-factory', 'Ω-ASSET-FACTORY-T', 'ttm', 'registry:asset-factory', 'FOUNDRY', 'structured')],
 'repository-forest': [('repo-tfug-biosphere', 'TFUG Research Biosphere', 'tfug', 'commit:9171a06', 'REPOSITORY', 'externally_observed'),
                       ('repo-ttm-canonical-forge', 'TTM Canonical Forge', 'ttm', 'commit:fb49a34', 'REPOSITORY', 'externally_observed'),
                       ('repo-tfuga-execution', 'TFUGA Execution Monorepo', 'main', 'commit:8f1fca3', 'REPOSITORY', 'externally_observed'),
                       ('repo-pefa-energy', 'PEFA Energy Laboratory', 'pefa', 'commit:d5ee7db', 'REPOSITORY', 'externally_observed'),
                       ('repo-tfacc-formal', 'TFACC Formal Laboratory', 'tfacc', 'commit:399bf8e', 'REPOSITORY', 'externally_observed'),
                       ('repo-tfugag-gateway', 'TFUGAG Public Gateway', 'tfugag', 'commit:c28e51d', 'REPOSITORY', 'externally_observed'),
                       ('cross-repo-capability-graph', 'Cross-Repository Capability Graph', 'ttm', 'PR#696', 'MEMORY', 'tested'),
                       ('canonical-source-registry', 'Ω-CANON-SOURCE-T', 'ttm', 'PR#703', 'MEMORY', 'tested'),
                       ('tristan-kernel-v2', 'Ω-TRISTAN-KERNEL-V2', 'ttm', 'PR#703', 'OS', 'structured')]}

_REPOSITORY_KEYS = {
    "main": "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",
    "ttm": "Tristan-TM-Poly/TTM-TFUGA-AI7-TRISTAN2",
    "tfug": "Tristan-TM-Poly/Tristan_Tardif-Morency_TFUG",
    "pefa": "Tristan-TM-Poly/PEFA-FractalEnergySystem",
    "tfacc": "Tristan-TM-Poly/TFACC",
    "tfugag": "Tristan-TM-Poly/Tristan_Tardif-Morency_TFUGAG",
}

_LEVELS: Mapping[str, dict[str, object]] = {
    "structured": {
        "status": "structured",
        "dimensions": dict(code=1, tests=0, baseline=0, reproducibility=1, integration=1, maintainability=2, external_validation=0),
        "signals": {},
        "strength": "DECLARED",
        "claim": "A named, reviewable capability pointer exists; executable closure is not established.",
        "action": ("Materialize one bounded executable vertical", "test", 8, "focused executable receipt"),
    },
    "tested": {
        "status": "tested",
        "dimensions": dict(code=3, tests=3, baseline=1, reproducibility=3, integration=2, maintainability=3, external_validation=0),
        "signals": dict(ci_green=True, cli_available=True, schema_available=True, deterministic=True, m_minus_available=True),
        "strength": "OBSERVED",
        "claim": "Bounded software contracts and internal tests are reported; external validation is not established.",
        "action": ("Add a frozen baseline and adversarial court", "benchmark", 12, "comparative benchmark receipt"),
    },
    "benchmarked": {
        "status": "benchmarked",
        "dimensions": dict(code=4, tests=4, baseline=4, reproducibility=4, integration=3, maintainability=4, external_validation=0),
        "signals": dict(ci_green=True, cli_available=True, schema_available=True, deterministic=True, m_minus_available=True),
        "strength": "REPRODUCED",
        "claim": "Internal benchmark evidence is reported; superiority and external replication are not established.",
        "action": ("Run an independently sourced locked benchmark", "benchmark", 16, "external baseline and residue packet"),
    },
    "externally_observed": {
        "status": "externally_observed",
        "dimensions": dict(code=3, tests=3, baseline=2, reproducibility=4, integration=4, maintainability=3, external_validation=1),
        "signals": dict(ci_green=True, cli_available=True, schema_available=True, deterministic=True, m_minus_available=True, real_data=True),
        "strength": "OBSERVED",
        "claim": "A live repository or external observation is recorded; adoption, scientific truth and value are not established.",
        "action": ("Refresh the exact-head observation and classify survivance", "integration", 8, "fresh repository passport"),
    },
}


def _category(family: str, artifact_type: str) -> str:
    if family == "mathematics":
        return "mathematics"
    if family in {"physical-science", "spectroscopy-inference"}:
        return "science"
    if artifact_type == "THEORY":
        return "theory"
    if artifact_type in {"PRODUCT", "SERVICE", "VENTURE"}:
        return "product"
    if artifact_type in {"OS", "GOVERNANCE", "CAMPAIGN"}:
        return "operations"
    return "infrastructure"


def _summary(name: str, family: str, artifact_type: str) -> str:
    return (
        f"{name} is registered as a {artifact_type.lower()} in the "
        f"{family.replace('-', ' ')} family. The record preserves identity, "
        "scope, evidence level and the next falsifiable closure gate."
    )


def items(main: str, ttm: str, tfug: str):
    del main, ttm, tfug  # repository names are resolved from the closed registry above
    records = []
    for family, specs in FAMILY_SPECS.items():
        for prototype_id, name, repo_key, ref, artifact_type, level in specs:
            policy = _LEVELS[level]
            repository = _REPOSITORY_KEYS[repo_key]
            evidence = [ev("pointer", f"{repository}@{ref}", str(policy["strength"]), "Grand Atlas identity pointer")]
            if level in {"tested", "benchmarked"}:
                evidence.append(ev("test", f"{repository}@{ref} internal court", str(policy["strength"]), "Reported bounded software evidence"))
            elif level == "externally_observed":
                evidence.append(ev("external", f"{repository}@{ref} exact-head observation", "OBSERVED", "Repository observation, not independent validation"))
            action_spec = policy["action"]
            records.append(
                p(
                    prototype_id,
                    name,
                    _category(family, artifact_type),
                    repository,
                    ref,
                    _summary(name, family, artifact_type),
                    dimensions=dims(**policy["dimensions"]),
                    signals=sigs(**policy["signals"]),
                    evidence=tuple(evidence),
                    status=str(policy["status"]),
                    claim=str(policy["claim"]),
                    risks=(
                        "pointer coverage can become stale",
                        "named capability is not proof of integration, use or value",
                    ),
                    next_action=action(*action_spec),
                    limitations=(
                        "Grand Atlas entry is a conservative navigation record",
                        "fresh exact-head inspection is required before promotion",
                    ),
                    tags=(
                        f"type:{artifact_type}",
                        f"family:{family}",
                        f"level:{level}",
                        "atlas:r0.2",
                        "memory:canonical-pointer",
                    ),
                )
            )
    return tuple(records)
