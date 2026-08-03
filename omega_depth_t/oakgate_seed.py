from __future__ import annotations

from typing import Any

from .graph import DepthGraph
from .model import CodeStatus, IpStatus, NodeContract, OakStatus, RiskLevel


def _node(
    *,
    node_id: str,
    name: str,
    depth: int,
    path: str,
    parent_id: str | None,
    role: str,
    oak_status: OakStatus = OakStatus.DEFINED,
    code_status: CodeStatus = CodeStatus.SKELETON,
    risk_level: RiskLevel = RiskLevel.LOW,
    interfaces: tuple[str, ...] = (),
    tests: tuple[str, ...] = (),
    next_proof: str = "",
    next_action: str = "",
    metadata: dict[str, Any] | None = None,
    failure_modes: tuple[str, ...] = (),
    constraints: tuple[str, ...] = (),
    outputs: tuple[str, ...] = (),
    inputs: tuple[str, ...] = (),
    baselines: tuple[str, ...] = (),
) -> NodeContract:
    return NodeContract(
        id=node_id,
        name=name,
        depth=depth,
        path=path,
        parent_id=parent_id,
        root_creation="OAKGate",
        role=role,
        inputs=inputs,
        outputs=outputs,
        constraints=constraints,
        interfaces=interfaces,
        failure_modes=failure_modes,
        oak_status=oak_status,
        code_status=code_status,
        ip_status=IpStatus.PUBLIC,
        risk_level=risk_level,
        tests=tests,
        baselines=baselines,
        next_proof=next_proof,
        next_action_under_2h=next_action,
        metadata=metadata or {"atomic": False},
        tags=("oakgate", f"depth-{depth}"),
    )


def build_oakgate_depth9() -> DepthGraph:
    graph = DepthGraph()
    graph.add(
        _node(
            node_id="oakgate",
            name="OAKGate",
            depth=0,
            path="oakgate",
            parent_id=None,
            role="Auditer les créations scientifiques, logicielles, documentaires et entrepreneuriales.",
            oak_status=OakStatus.CODED,
            code_status=CodeStatus.RUNNABLE,
            interfaces=("repository", "document", "claim", "evidence", "report"),
            tests=("test_graph_validity",),
            next_proof="Détecter une divergence réelle code-documentation dans un dépôt contrôlé.",
            next_action="Exécuter le paquet d'exemple et inspecter oak-report.json.",
        )
    )

    systems = (
        ("oak_code", "OAK-Code", "Auditer code, tests, dépendances et reproductibilité."),
        ("oak_documentation", "OAK-Documentation", "Auditer les affirmations et leur cohérence avec les artefacts."),
        ("oak_science", "OAK-Science", "Auditer hypothèses, unités, baselines, mesures et reproductibilité."),
        ("oak_security", "OAK-Security", "Auditer secrets, permissions, surfaces d'attaque et dépendances."),
        ("oak_ip", "OAK-IP", "Auditer licences, provenance et divulgations de propriété intellectuelle."),
        ("oak_product", "OAK-Product", "Auditer problème, utilisateur, valeur, coût et voie produit."),
        ("oak_evidence", "OAK-Evidence", "Compiler les preuves et leurs liens de provenance."),
        ("oak_uncertainty", "OAK-Uncertainty", "Propager et calibrer les incertitudes et méta-incertitudes."),
        ("oak_memory", "OAK-Memory", "Conserver M⁺, M⁻, résidus et décisions."),
        ("oak_reporting", "OAK-Reporting", "Produire des rapports lisibles et machine-readable."),
    )
    for node_id, name, role in systems:
        graph.add(
            _node(
                node_id=f"oakgate.{node_id}",
                name=name,
                depth=1,
                path=f"oakgate/{node_id}",
                parent_id="oakgate",
                role=role,
                interfaces=("oakgate-core",),
                next_proof=f"Définir un cas de test vérifiable pour {name}.",
                next_action=f"Créer le premier contrat de sous-système pour {name}.",
            )
        )

    code_children = (
        ("repository_scanner", "RepositoryScanner", "Inventorier fichiers, langages, métadonnées et limites d'analyse."),
        ("static_analyzer", "StaticAnalyzer", "Extraire structures statiques et risques sans exécuter le code."),
        ("test_inspector", "TestInspector", "Analyser présence, portée, assertions et lacunes des tests."),
        ("dependency_inspector", "DependencyInspector", "Analyser dépendances, versions, licences et vulnérabilités."),
        ("configuration_inspector", "ConfigurationInspector", "Analyser CI, packaging, paramètres et environnements."),
        ("doc_code_comparator", "DocumentationCodeComparator", "Comparer affirmations documentaires et comportement codé."),
        ("reproducibility_inspector", "ReproducibilityInspector", "Évaluer la reproductibilité locale et déclarative."),
        ("code_risk_aggregator", "CodeRiskAggregator", "Agrèger les signaux sans masquer leur provenance."),
    )
    for node_id, name, role in code_children:
        graph.add(
            _node(
                node_id=f"oakgate.oak_code.{node_id}",
                name=name,
                depth=2,
                path=f"oakgate/oak_code/{node_id}",
                parent_id="oakgate.oak_code",
                role=role,
                interfaces=("repository-snapshot", "oak-finding"),
                next_proof=f"Valider {name} sur un dépôt jouet annoté.",
                next_action=f"Écrire le contrat d'entrée-sortie de {name}.",
            )
        )

    test_modules = (
        ("test_discovery", "TestDiscovery", "Découvrir les tests et leurs frameworks."),
        ("test_classification", "TestClassification", "Classifier unité, intégration, propriété et système."),
        ("assertion_analyzer", "AssertionAnalyzer", "Inspecter la précision et la force des assertions."),
        ("coverage_analyzer", "CoverageAnalyzer", "Compiler plusieurs dimensions de couverture."),
        ("flaky_test_detector", "FlakyTestDetector", "Détecter les tests instables."),
        ("disabled_test_detector", "DisabledTestDetector", "Détecter tests ignorés, commentés ou conditionnels."),
        ("test_documentation_matcher", "TestDocumentationMatcher", "Relier affirmations et tests correspondants."),
        ("test_evidence_compiler", "TestEvidenceCompiler", "Compiler traces et preuves de test."),
    )
    for node_id, name, role in test_modules:
        graph.add(
            _node(
                node_id=f"oakgate.oak_code.test_inspector.{node_id}",
                name=name,
                depth=3,
                path=f"oakgate/oak_code/test_inspector/{node_id}",
                parent_id="oakgate.oak_code.test_inspector",
                role=role,
                interfaces=("test-inventory", "test-finding"),
                next_proof=f"Comparer {name} à une annotation humaine.",
                next_action=f"Créer un fixture minimal pour {name}.",
            )
        )

    coverage_components = (
        ("line_coverage", "LineCoverage", "Mesurer les lignes exécutées."),
        ("branch_coverage", "BranchCoverage", "Mesurer les décisions et branches exécutées."),
        ("function_coverage", "FunctionCoverage", "Mesurer les fonctions exercées."),
        ("path_coverage", "PathCoverage", "Échantillonner les chemins de contrôle pertinents."),
        ("requirement_coverage", "RequirementCoverage", "Relier exigences, affirmations et tests."),
        ("mutation_coverage", "MutationCoverage", "Mesurer la capacité des tests à tuer des mutations."),
        ("coverage_gap_ranker", "CoverageGapRanker", "Classer les lacunes selon criticité et preuve."),
    )
    for node_id, name, role in coverage_components:
        graph.add(
            _node(
                node_id=f"oakgate.oak_code.test_inspector.coverage_analyzer.{node_id}",
                name=name,
                depth=4,
                path=f"oakgate/oak_code/test_inspector/coverage_analyzer/{node_id}",
                parent_id="oakgate.oak_code.test_inspector.coverage_analyzer",
                role=role,
                interfaces=("coverage-events", "coverage-finding"),
                baselines=("coverage.py", "pytest-cov"),
                next_proof=f"Vérifier {name} sur un graphe de contrôle connu.",
                next_action=f"Définir un fixture pour {name}.",
            )
        )

    branch_children = (
        ("control_flow_graph_builder", "ControlFlowGraphBuilder", "Construire un graphe de contrôle normalisé."),
        ("decision_node_extractor", "DecisionNodeExtractor", "Extraire les nœuds de décision attendus."),
        ("executed_branch_collector", "ExecutedBranchCollector", "Collecter les branches observées."),
        ("missing_branch_detector", "MissingBranchDetector", "Comparer branches attendues et observées."),
        ("critical_branch_ranker", "CriticalBranchRanker", "Classer les branches manquantes par risque."),
        ("branch_coverage_reporter", "BranchCoverageReporter", "Produire un rapport traçable."),
    )
    for node_id, name, role in branch_children:
        graph.add(
            _node(
                node_id=f"oakgate.oak_code.test_inspector.coverage_analyzer.branch_coverage.{node_id}",
                name=name,
                depth=5,
                path=f"oakgate/oak_code/test_inspector/coverage_analyzer/branch_coverage/{node_id}",
                parent_id="oakgate.oak_code.test_inspector.coverage_analyzer.branch_coverage",
                role=role,
                interfaces=("control-flow-model", "branch-evidence"),
                next_proof=f"Tester {name} sur une fonction à branches annotées.",
                next_action=f"Définir l'API pure de {name}.",
            )
        )

    detector_id = "oakgate.oak_code.test_inspector.coverage_analyzer.branch_coverage.missing_branch_detector"
    detector_path = "oakgate/oak_code/test_inspector/coverage_analyzer/branch_coverage/missing_branch_detector"
    operators = (
        ("enumerate_expected_branches", "enumerate_expected_branches()", "Énumérer les branches attendues."),
        ("normalize_execution_trace", "normalize_execution_trace()", "Normaliser les traces observées."),
        ("compare_expected_to_observed", "compare_expected_to_observed()", "Calculer branches manquantes et inattendues."),
        ("classify_missing_branch", "classify_missing_branch()", "Classifier une branche manquante."),
        ("estimate_branch_risk", "estimate_branch_risk()", "Estimer le risque avec provenance."),
        ("emit_gap_record", "emit_gap_record()", "Émettre un enregistrement déterministe."),
    )
    for node_id, name, role in operators:
        atomic = node_id == "compare_expected_to_observed"
        graph.add(
            _node(
                node_id=f"{detector_id}.{node_id}",
                name=name,
                depth=6,
                path=f"{detector_path}/{node_id}",
                parent_id=detector_id,
                role=role,
                inputs=("expected_branches", "observed_branches"),
                outputs=("branch_gap_record",),
                constraints=("deterministic", "read-only", "preserve-provenance"),
                interfaces=("pure-function",),
                failure_modes=("incomplete instrumentation", "dynamic code", "platform-specific branch"),
                tests=("test_one_branch_missing",) if atomic else (f"test_{node_id}",),
                next_proof="Détecter exactement une branche absente dans un fixture annoté.",
                next_action="Implémenter la comparaison par ensembles et trois tests unitaires.",
                metadata={"atomic": atomic},
            )
        )

    compare_id = f"{detector_id}.compare_expected_to_observed"
    compare_path = f"{detector_path}/compare_expected_to_observed"
    tests = (
        "test_all_branches_observed",
        "test_one_branch_missing",
        "test_multiple_branches_missing",
        "test_unexpected_observed_branch",
        "test_empty_expected_set",
        "test_empty_observed_set",
        "test_duplicate_trace_events",
        "test_platform_specific_branch",
        "test_deterministic_output_order",
    )
    for test_name in tests:
        graph.add(
            _node(
                node_id=f"{compare_id}.{test_name}",
                name=test_name,
                depth=7,
                path=f"{compare_path}/tests/{test_name}",
                parent_id=compare_id,
                role=f"Vérifier le cas {test_name}.",
                inputs=("fixture",),
                outputs=("assertion-result",),
                interfaces=("pytest-test",),
                tests=(test_name,),
                next_proof=f"Faire passer {test_name} avec sortie déterministe.",
                next_action=f"Coder le fixture de {test_name}.",
                metadata={"atomic": test_name != "test_one_branch_missing"},
            )
        )

    case_id = f"{compare_id}.test_one_branch_missing"
    case_path = f"{compare_path}/tests/test_one_branch_missing"
    case_parts = (
        ("given_expected", "Given: expected={A,B,C}", "Définir les branches attendues."),
        ("given_observed", "Given: observed={A,C}", "Définir les branches observées."),
        ("when_compare", "When: compare", "Exécuter la comparaison."),
        ("then_missing", "Then: missing={B}", "Vérifier la branche absente."),
        ("then_ratio", "Then: ratio=2/3", "Vérifier le ratio."),
        ("then_provenance", "Then: evidence→B", "Vérifier le lien de provenance."),
    )
    for node_id, name, role in case_parts:
        graph.add(
            _node(
                node_id=f"{case_id}.{node_id}",
                name=name,
                depth=8,
                path=f"{case_path}/{node_id}",
                parent_id=case_id,
                role=role,
                interfaces=("test-case-fragment",),
                tests=("test_one_branch_missing",),
                next_proof="Valider le fragment dans le test complet.",
                next_action="Matérialiser le fragment dans un fixture JSON.",
                metadata={"atomic": True},
            )
        )

    evidence_parent = f"{case_id}.then_provenance"
    evidence_path = f"{case_path}/then_provenance"
    evidence_fields = (
        "input_hash",
        "output_hash",
        "source_location",
        "test_run_id",
        "environment",
        "timestamp",
        "assertion_results",
        "execution_duration",
        "residuals",
    )
    for field_name in evidence_fields:
        graph.add(
            _node(
                node_id=f"{evidence_parent}.{field_name}",
                name=field_name,
                depth=9,
                path=f"{evidence_path}/evidence/{field_name}",
                parent_id=evidence_parent,
                role=f"Conserver le champ probatoire {field_name}.",
                interfaces=("evidence-field",),
                tests=("test_evidence_bundle_schema",),
                next_proof="Valider ce champ contre le schéma EvidenceBundle.",
                next_action=f"Ajouter {field_name} au fixture probatoire.",
                metadata={"atomic": True},
            )
        )

    doc_children = (
        ("claim_code_consistency", "ClaimCodeConsistency", "Comparer les affirmations au code."),
        ("claim_evidence_linker", "ClaimEvidenceLinker", "Relier chaque affirmation à ses preuves."),
        ("semantic_diff", "SemanticDiff", "Détecter les changements de sens entre versions."),
        ("documentation_risk_aggregator", "DocumentationRiskAggregator", "Agrèger les risques documentaires."),
    )
    for node_id, name, role in doc_children:
        graph.add(
            _node(
                node_id=f"oakgate.oak_documentation.{node_id}",
                name=name,
                depth=2,
                path=f"oakgate/oak_documentation/{node_id}",
                parent_id="oakgate.oak_documentation",
                role=role,
                interfaces=("document-snapshot", "claim-finding"),
                next_proof=f"Valider {name} sur un document annoté.",
                next_action=f"Créer un exemple contrôlé pour {name}.",
            )
        )

    graph.add(_node(node_id="oakgate.oak_documentation.claim_code_consistency.claim_extractor", name="ClaimExtractor", depth=3, path="oakgate/oak_documentation/claim_code_consistency/claim_extractor", parent_id="oakgate.oak_documentation.claim_code_consistency", role="Extraire des affirmations vérifiables depuis la documentation.", interfaces=("document", "claim-candidate"), next_proof="Extraire correctement un corpus de phrases annotées.", next_action="Créer dix phrases positives et négatives."))
    graph.add(_node(node_id="oakgate.oak_documentation.claim_code_consistency.claim_extractor.markdown_claim_extractor", name="MarkdownClaimExtractor", depth=4, path="oakgate/oak_documentation/claim_code_consistency/claim_extractor/markdown_claim_extractor", parent_id="oakgate.oak_documentation.claim_code_consistency.claim_extractor", role="Extraire les affirmations depuis Markdown en conservant les lignes.", interfaces=("markdown", "claim-candidate"), next_proof="Conserver exactement les lignes source de chaque affirmation.", next_action="Implémenter un extracteur de paragraphes."))
    graph.add(_node(node_id="oakgate.oak_documentation.claim_code_consistency.claim_extractor.markdown_claim_extractor.sentence_classifier", name="SentenceClassifier", depth=5, path="oakgate/oak_documentation/claim_code_consistency/claim_extractor/markdown_claim_extractor/sentence_classifier", parent_id="oakgate.oak_documentation.claim_code_consistency.claim_extractor.markdown_claim_extractor", role="Classer phrase informative, exigence, promesse ou opinion.", interfaces=("sentence", "claim-label"), next_proof="Atteindre une précision mesurée sur un petit corpus annoté.", next_action="Définir les classes et dix exemples."))
    classifier_id = "oakgate.oak_documentation.claim_code_consistency.claim_extractor.markdown_claim_extractor.sentence_classifier.classify_claim"
    graph.add(_node(node_id=classifier_id, name="classify_claim()", depth=6, path="oakgate/oak_documentation/claim_code_consistency/claim_extractor/markdown_claim_extractor/sentence_classifier/classify_claim", parent_id="oakgate.oak_documentation.claim_code_consistency.claim_extractor.markdown_claim_extractor.sentence_classifier", role="Classifier une phrase avec justification et incertitude.", inputs=("sentence", "context"), outputs=("claim-label", "confidence", "rationale"), interfaces=("pure-function",), tests=("test_capability_claim", "test_opinion_not_claim"), next_proof="Distinguer une promesse testable d'une opinion.", next_action="Implémenter une baseline à règles."))
    for test_name in ("test_capability_claim", "test_opinion_not_claim"):
        graph.add(_node(node_id=f"{classifier_id}.{test_name}", name=test_name, depth=7, path=f"oakgate/oak_documentation/claim_code_consistency/claim_extractor/markdown_claim_extractor/sentence_classifier/classify_claim/tests/{test_name}", parent_id=classifier_id, role=f"Tester {test_name}.", interfaces=("pytest-test",), tests=(test_name,), next_proof=f"Faire passer {test_name}.", next_action=f"Écrire {test_name}.", metadata={"atomic": True}))

    return graph
