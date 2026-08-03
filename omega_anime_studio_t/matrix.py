"""The 16×16×32 Anime Studio matrix and deterministic registries."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

DOMAINS: dict[str, tuple[str, ...]] = {
    'ip_vision': ('VisionCompiler', 'PremiseForge', 'ThemeGraph', 'GenreTensor', 'AudienceContract', 'EmotionalPromiseLedger', 'OriginalityMap', 'InspirationProvenance', 'IPClassificationGate', 'FranchiseIdentityKernel', 'TitleGenerator', 'SymbolicSignatureEngine', 'CanonBoundaryManager', 'DisclosureRiskScanner', 'BrandContinuityChecker', 'CreativeSovereigntyLedger'),
    'world_causality': ('WorldGraph', 'TimelineGraph', 'GeographyCompiler', 'CivilizationForge', 'InstitutionGraph', 'EconomySimulator', 'ResourceFlowEngine', 'TechnologyTree', 'MythologyCompiler', 'LawAndCustomGraph', 'EcologyEngine', 'HistoricalDebtLedger', 'SecretAndRumorGraph', 'CausalConstraintSolver', 'CounterfactualWorldEngine', 'WorldConsistencyOAK'),
    'characters': ('CharacterTensor', 'DesireNeedConflict', 'FearContradictionEngine', 'MoralBoundaryGraph', 'MemoryTimeline', 'RelationshipHypergraph', 'KnowledgeStateTracker', 'SecretLedger', 'CharacterVoiceDNA', 'BodyLanguageGrammar', 'CostumeEvolutionGraph', 'AbilityLimitEngine', 'TraumaAndRecoveryMap', 'CharacterArcCompiler', 'CharacterConsistencyLinter', 'EnsembleBalanceOptimizer'),
    'narrative': ('StoryCompiler', 'ArcGenerator', 'EpisodePlanner', 'SequenceBuilder', 'SceneCompiler', 'BeatGraph', 'ConflictEscalator', 'ReversalEngine', 'RevelationScheduler', 'ForeshadowingLedger', 'MysteryResolutionGraph', 'CliffhangerDesigner', 'PacingOptimizer', 'NarrativeDebtManager', 'CausalPlotValidator', 'EndingSatisfactionAnalyzer'),
    'dialogue_language': ('DialogueCompiler', 'CharacterVoiceModel', 'SubtextEngine', 'ExpositionDetector', 'RepetitionScanner', 'VocabularyProfile', 'SocialRegisterManager', 'EmotionalSpeechState', 'InterruptionAndSilencePlanner', 'ConflictDialogueEngine', 'ScientificDialogueGuard', 'HumorTimingEngine', 'MonologueCompressor', 'LipSyncPhonemeMap', 'LocalizationDialogueAdapter', 'DialogueOAK'),
    'visual_design': ('StyleDNA', 'ShapeLanguage', 'ColorSystem', 'MaterialGrammar', 'LightingBible', 'CompositionRules', 'SilhouetteValidator', 'CharacterTurnaroundPlanner', 'ExpressionAtlas', 'CostumeGraph', 'PropDesignSystem', 'EnvironmentDesignCompiler', 'VisualSymbolLedger', 'VisualContinuityChecker', 'StyleDriftDetector', 'AssetProvenanceGate'),
    'motion_animation': ('MotionDNA', 'PoseGraph', 'GestureLibrary', 'WalkCycleCompiler', 'ActingPlanner', 'FacialMotionGraph', 'EyeAndGazeEngine', 'SecondaryMotionPlanner', 'ClothMotionAdapter', 'HairMotionAdapter', 'ImpactMotionEngine', 'TimingSpacingCompiler', 'KeyframePlanner', 'InbetweenEstimator', 'MotionContinuityValidator', 'AnimationCostEstimator'),
    'camera_editing': ('ShotGraph', 'ShotPurposeClassifier', 'CameraPositionSolver', 'LensIntentModel', 'CameraMotionPlanner', 'ScreenDirectionValidator', 'SpatialContinuityGraph', 'EyelineMatcher', 'TransitionCompiler', 'MontageRhythmEngine', 'AttentionFlowModel', 'VisualRevealScheduler', 'ShotDurationOptimizer', 'CoveragePlanner', 'EditContinuityLinter', 'CinematicCostRouter'),
    'audio_voice_music': ('SoundGraph', 'VoiceCastingProfile', 'VoiceProvenanceLedger', 'DialogueRecordingPlanner', 'AmbienceGeneratorPlan', 'FoleyGraph', 'ImpactSoundEngine', 'SilencePlanner', 'LeitmotifGraph', 'MusicEmotionMap', 'HarmonyNarrativeEngine', 'TempoSynchronization', 'SpatialAudioPlanner', 'LoudnessValidator', 'AudioContinuityChecker', 'MusicAndVoiceIPGate'),
    'physics_powers': ('AbilitySystemCompiler', 'EnergyAccounting', 'ConstraintGraph', 'CostAndFailureEngine', 'CountermeasureGenerator', 'PhysicsApproximationLedger', 'TechnologyPlausibilityMap', 'MaterialInteractionEngine', 'DestructionContinuityGraph', 'EnvironmentResponseEngine', 'InjuryConsequenceTracker', 'ScaleConsistencyValidator', 'ScientificClaimGuard', 'SimulationAdapter', 'RuleExceptionLedger', 'PowerEscalationOAK'),
    'production': ('ProductionGraph', 'TaskDependencyEngine', 'AssetRegistry', 'VersionManager', 'ReviewStateMachine', 'DepartmentRouter', 'WorkloadEstimator', 'ScheduleSimulator', 'BudgetEstimator', 'RenderCostPlanner', 'ReuseOptimizer', 'BottleneckDetector', 'DeliveryCompiler', 'ArchiveManager', 'RollbackPlanner', 'ProductionOAKGate'),
    'oak_memory': ('NarrativeOAK', 'VisualOAK', 'AudioOAK', 'PhysicsOAK', 'ContinuityOAK', 'ProductionOAK', 'IPOAK', 'AudienceOAK', 'AccessibilityOAK', 'SafetyOAK', 'MMinusRegistry', 'MPlusRegistry', 'RegressionGenerator', 'FailureReplayEngine', 'ConfidenceDebtTracker', 'CanonPromotionGate'),
    'audience_experiment': ('AudiencePanelSchema', 'ComprehensionTest', 'CharacterRecallTest', 'EmotionalCurveRecorder', 'ConfusionMap', 'BoredomSignalAnalyzer', 'RewatchValueEstimator', 'RevealPredictabilityTest', 'ScenePreferenceMap', 'AccessibilityFeedback', 'DemographicSegmentationGuard', 'SyntheticAudienceSandbox', 'HumanAudienceComparator', 'CutABTesting', 'FeedbackEvidenceLedger', 'AudienceOAKGate'),
    'localization_accessibility': ('LocalizationGraph', 'TerminologyLedger', 'CulturalReferenceAdapter', 'SubtitleCompiler', 'SubtitleTimingValidator', 'DubbingConstraintPlanner', 'LipSyncLanguageAdapter', 'ReadingSpeedChecker', 'AudioDescriptionPlanner', 'ClosedCaptionCompiler', 'ColorAccessibilityAudit', 'PhotosensitivityRiskAudit', 'CognitiveLoadAnalyzer', 'LanguageConsistencyChecker', 'LocalizationProvenance', 'AccessibilityOAK'),
    'transmedia_economy': ('FranchiseGraph', 'MangaAdapter', 'NovelAdapter', 'GameAdapter', 'VisualNovelAdapter', 'WebtoonAdapter', 'InteractiveEpisodeEngine', 'LoreDatabasePublisher', 'ArtbookCompiler', 'MusicReleasePlanner', 'MerchandiseAssetGraph', 'CommunityContentGate', 'RevenueScenarioModel', 'LicensingLedger', 'PartnerPackageCompiler', 'CommercialOAKGate'),
    'automation_github': ('AnimeRepoCompiler', 'SchemaGenerator', 'TestGenerator', 'CICompiler', 'AssetManifestGenerator', 'IssueGenerator', 'RoadmapCompiler', 'BranchPlanner', 'SemanticDiffEngine', 'DuplicateDetector', 'ShardedRegistryWriter', 'CheckpointManager', 'ArtifactBundleCompiler', 'GitHubTruthAudit', 'ReleaseGate', 'ZeroTouchOrchestrator'),

}

ARTIFACT_KINDS: tuple[str, ...] = (
    'schema','api','engine','generator','validator','test','fixture','example',
    'benchmark','policy','report','manifest','registry','adapter','cli','documentation',
    'm_minus_rule','m_plus_rule','provenance_record','risk_record','evidence_record',
    'issue_template','metric','checkpoint','rollback_plan','simulation','baseline',
    'counterexample','property_test','integration_test','performance_test','release_gate',
)

PROOF_BY_KIND = {
    'schema': 'valid instance plus invalid counterexample',
    'api': 'contract test',
    'engine': 'baseline comparison and failure condition',
    'generator': 'determinism or documented stochastic seed',
    'validator': 'positive and negative fixtures',
    'test': 'reproducible assertion',
    'benchmark': 'measured baseline and environment manifest',
    'policy': 'human review and enforcement test',
    'release_gate': 'explicit approval and rollback proof',
}

RISK_BY_DOMAIN = {
    'ip_vision': 'premature disclosure or derivative similarity',
    'world_causality': 'inconsistent world propagation',
    'characters': 'flat or contradictory characterization',
    'narrative': 'causal break or unresolved debt',
    'dialogue_language': 'voice collapse or exposition overload',
    'visual_design': 'style drift or unclear provenance',
    'motion_animation': 'motion discontinuity or cost explosion',
    'camera_editing': 'spatial discontinuity or attention loss',
    'audio_voice_music': 'license, voice-consent or loudness risk',
    'physics_powers': 'unbounded power or false scientific implication',
    'production': 'dependency bottleneck or irreversible loss',
    'oak_memory': 'overblocking or false confidence',
    'audience_experiment': 'synthetic feedback presented as market proof',
    'localization_accessibility': 'meaning loss or inaccessible delivery',
    'transmedia_economy': 'premature monetization or licensing conflict',
    'automation_github': 'unsafe mutation or non-reproducible generation',
}


@dataclass(frozen=True)
class MatrixCell:
    cell_id: str
    domain_index: int
    domain: str
    module_index: int
    module: str
    artifact_index: int
    artifact_kind: str
    status: str
    proof_required: str
    primary_risk: str
    generator_version: str = 'omega-anime-studio/r1'

    def to_dict(self) -> dict[str, object]:
        return {
            'cell_id': self.cell_id,
            'domain_index': self.domain_index,
            'domain': self.domain,
            'module_index': self.module_index,
            'module': self.module,
            'artifact_index': self.artifact_index,
            'artifact_kind': self.artifact_kind,
            'status': self.status,
            'proof_required': self.proof_required,
            'primary_risk': self.primary_risk,
            'generator_version': self.generator_version,
        }


def iter_matrix_cells() -> Iterator[MatrixCell]:
    for domain_index, (domain, modules) in enumerate(DOMAINS.items(), start=1):
        for module_index, module in enumerate(modules, start=1):
            for artifact_index, artifact_kind in enumerate(ARTIFACT_KINDS, start=1):
                yield MatrixCell(
                    cell_id=(
                        f'ANIME-R1-D{domain_index:02d}-M{module_index:02d}'
                        f'-A{artifact_index:02d}'
                    ),
                    domain_index=domain_index,
                    domain=domain,
                    module_index=module_index,
                    module=module,
                    artifact_index=artifact_index,
                    artifact_kind=artifact_kind,
                    status='PLANNED',
                    proof_required=PROOF_BY_KIND.get(
                        artifact_kind,
                        'reviewable artifact, provenance, test and rollback path',
                    ),
                    primary_risk=RISK_BY_DOMAIN[domain],
                )


def matrix_summary() -> dict[str, object]:
    cells = list(iter_matrix_cells())
    ids = [cell.cell_id for cell in cells]
    payload = '\n'.join(
        json.dumps(cell.to_dict(), ensure_ascii=False, sort_keys=True)
        for cell in cells
    ).encode('utf-8')
    return {
        'domain_count': len(DOMAINS),
        'module_count': sum(len(modules) for modules in DOMAINS.values()),
        'artifact_kind_count': len(ARTIFACT_KINDS),
        'cell_count': len(cells),
        'unique_cell_count': len(set(ids)),
        'sha256': hashlib.sha256(payload).hexdigest(),
        'no_permanent_total_cap': True,
    }


def write_matrix_jsonl(path: str | Path) -> dict[str, object]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    count = 0
    with target.open('w', encoding='utf-8', newline='\n') as handle:
        for cell in iter_matrix_cells():
            line = json.dumps(cell.to_dict(), ensure_ascii=False, sort_keys=True) + '\n'
            handle.write(line)
            digest.update(line.encode('utf-8'))
            count += 1
    summary = matrix_summary()
    summary.update({'written': count, 'file_sha256': digest.hexdigest()})
    return summary


def validate_matrix() -> list[str]:
    errors: list[str] = []
    if len(DOMAINS) != 16:
        errors.append('matrix: exactly 16 domains required')
    for domain, modules in DOMAINS.items():
        if len(modules) != 16:
            errors.append(f'matrix.{domain}: exactly 16 modules required')
        if len(set(modules)) != len(modules):
            errors.append(f'matrix.{domain}: duplicate module')
    if len(ARTIFACT_KINDS) != 32:
        errors.append('matrix: exactly 32 artifact kinds required for R1 frontier')
    cells = list(iter_matrix_cells())
    if len(cells) != 8192:
        errors.append(f'matrix: expected 8192 cells, got {len(cells)}')
    if len({cell.cell_id for cell in cells}) != len(cells):
        errors.append('matrix: duplicate cell ids')
    return errors
