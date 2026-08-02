from __future__ import annotations

import hashlib
import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]

DOMAINS = {
    'ip_vision': ['VisionCompiler','PremiseForge','ThemeGraph','GenreTensor','AudienceContract','EmotionalPromiseLedger','OriginalityMap','InspirationProvenance','IPClassificationGate','FranchiseIdentityKernel','TitleGenerator','SymbolicSignatureEngine','CanonBoundaryManager','DisclosureRiskScanner','BrandContinuityChecker','CreativeSovereigntyLedger'],
    'world_causality': ['WorldGraph','TimelineGraph','GeographyCompiler','CivilizationForge','InstitutionGraph','EconomySimulator','ResourceFlowEngine','TechnologyTree','MythologyCompiler','LawAndCustomGraph','EcologyEngine','HistoricalDebtLedger','SecretAndRumorGraph','CausalConstraintSolver','CounterfactualWorldEngine','WorldConsistencyOAK'],
    'characters': ['CharacterTensor','DesireNeedConflict','FearContradictionEngine','MoralBoundaryGraph','MemoryTimeline','RelationshipHypergraph','KnowledgeStateTracker','SecretLedger','CharacterVoiceDNA','BodyLanguageGrammar','CostumeEvolutionGraph','AbilityLimitEngine','TraumaAndRecoveryMap','CharacterArcCompiler','CharacterConsistencyLinter','EnsembleBalanceOptimizer'],
    'narrative': ['StoryCompiler','ArcGenerator','EpisodePlanner','SequenceBuilder','SceneCompiler','BeatGraph','ConflictEscalator','ReversalEngine','RevelationScheduler','ForeshadowingLedger','MysteryResolutionGraph','CliffhangerDesigner','PacingOptimizer','NarrativeDebtManager','CausalPlotValidator','EndingSatisfactionAnalyzer'],
    'dialogue_language': ['DialogueCompiler','CharacterVoiceModel','SubtextEngine','ExpositionDetector','RepetitionScanner','VocabularyProfile','SocialRegisterManager','EmotionalSpeechState','InterruptionAndSilencePlanner','ConflictDialogueEngine','ScientificDialogueGuard','HumorTimingEngine','MonologueCompressor','LipSyncPhonemeMap','LocalizationDialogueAdapter','DialogueOAK'],
    'visual_design': ['StyleDNA','ShapeLanguage','ColorSystem','MaterialGrammar','LightingBible','CompositionRules','SilhouetteValidator','CharacterTurnaroundPlanner','ExpressionAtlas','CostumeGraph','PropDesignSystem','EnvironmentDesignCompiler','VisualSymbolLedger','VisualContinuityChecker','StyleDriftDetector','AssetProvenanceGate'],
    'motion_animation': ['MotionDNA','PoseGraph','GestureLibrary','WalkCycleCompiler','ActingPlanner','FacialMotionGraph','EyeAndGazeEngine','SecondaryMotionPlanner','ClothMotionAdapter','HairMotionAdapter','ImpactMotionEngine','TimingSpacingCompiler','KeyframePlanner','InbetweenEstimator','MotionContinuityValidator','AnimationCostEstimator'],
    'camera_editing': ['ShotGraph','ShotPurposeClassifier','CameraPositionSolver','LensIntentModel','CameraMotionPlanner','ScreenDirectionValidator','SpatialContinuityGraph','EyelineMatcher','TransitionCompiler','MontageRhythmEngine','AttentionFlowModel','VisualRevealScheduler','ShotDurationOptimizer','CoveragePlanner','EditContinuityLinter','CinematicCostRouter'],
    'audio_voice_music': ['SoundGraph','VoiceCastingProfile','VoiceProvenanceLedger','DialogueRecordingPlanner','AmbienceGeneratorPlan','FoleyGraph','ImpactSoundEngine','SilencePlanner','LeitmotifGraph','MusicEmotionMap','HarmonyNarrativeEngine','TempoSynchronization','SpatialAudioPlanner','LoudnessValidator','AudioContinuityChecker','MusicAndVoiceIPGate'],
    'physics_powers': ['AbilitySystemCompiler','EnergyAccounting','ConstraintGraph','CostAndFailureEngine','CountermeasureGenerator','PhysicsApproximationLedger','TechnologyPlausibilityMap','MaterialInteractionEngine','DestructionContinuityGraph','EnvironmentResponseEngine','InjuryConsequenceTracker','ScaleConsistencyValidator','ScientificClaimGuard','SimulationAdapter','RuleExceptionLedger','PowerEscalationOAK'],
    'production': ['ProductionGraph','TaskDependencyEngine','AssetRegistry','VersionManager','ReviewStateMachine','DepartmentRouter','WorkloadEstimator','ScheduleSimulator','BudgetEstimator','RenderCostPlanner','ReuseOptimizer','BottleneckDetector','DeliveryCompiler','ArchiveManager','RollbackPlanner','ProductionOAKGate'],
    'oak_memory': ['NarrativeOAK','VisualOAK','AudioOAK','PhysicsOAK','ContinuityOAK','ProductionOAK','IPOAK','AudienceOAK','AccessibilityOAK','SafetyOAK','MMinusRegistry','MPlusRegistry','RegressionGenerator','FailureReplayEngine','ConfidenceDebtTracker','CanonPromotionGate'],
    'audience_experiment': ['AudiencePanelSchema','ComprehensionTest','CharacterRecallTest','EmotionalCurveRecorder','ConfusionMap','BoredomSignalAnalyzer','RewatchValueEstimator','RevealPredictabilityTest','ScenePreferenceMap','AccessibilityFeedback','DemographicSegmentationGuard','SyntheticAudienceSandbox','HumanAudienceComparator','CutABTesting','FeedbackEvidenceLedger','AudienceOAKGate'],
    'localization_accessibility': ['LocalizationGraph','TerminologyLedger','CulturalReferenceAdapter','SubtitleCompiler','SubtitleTimingValidator','DubbingConstraintPlanner','LipSyncLanguageAdapter','ReadingSpeedChecker','AudioDescriptionPlanner','ClosedCaptionCompiler','ColorAccessibilityAudit','PhotosensitivityRiskAudit','CognitiveLoadAnalyzer','LanguageConsistencyChecker','LocalizationProvenance','AccessibilityOAK'],
    'transmedia_economy': ['FranchiseGraph','MangaAdapter','NovelAdapter','GameAdapter','VisualNovelAdapter','WebtoonAdapter','InteractiveEpisodeEngine','LoreDatabasePublisher','ArtbookCompiler','MusicReleasePlanner','MerchandiseAssetGraph','CommunityContentGate','RevenueScenarioModel','LicensingLedger','PartnerPackageCompiler','CommercialOAKGate'],
    'automation_github': ['AnimeRepoCompiler','SchemaGenerator','TestGenerator','CICompiler','AssetManifestGenerator','IssueGenerator','RoadmapCompiler','BranchPlanner','SemanticDiffEngine','DuplicateDetector','ShardedRegistryWriter','CheckpointManager','ArtifactBundleCompiler','GitHubTruthAudit','ReleaseGate','ZeroTouchOrchestrator'],
}

ARTIFACT_KINDS = [
    'schema','api','engine','generator','validator','test','fixture','example',
    'benchmark','policy','report','manifest','registry','adapter','cli','documentation',
    'm_minus_rule','m_plus_rule','provenance_record','risk_record','evidence_record','issue_template','metric','checkpoint',
    'rollback_plan','simulation','baseline','counterexample','property_test','integration_test','performance_test','release_gate',
]

assert len(DOMAINS) == 16
assert all(len(v) == 16 for v in DOMAINS.values())
assert len(ARTIFACT_KINDS) == 32

files: dict[str, str] = {}

files['omega_anime_studio_t/models.py'] = dedent('''
    """Typed Anime-IR models for Ω-ANIME-STUDIO-T∞ R1.

    The models separate internal coherence from artistic quality, market proof,
    legal clearance and scientific truth.  Only standard-library types are used
    so the kernel stays portable and auditable.
    """

    from __future__ import annotations

    from dataclasses import asdict, dataclass, field, is_dataclass
    from enum import Enum
    from typing import Any, Iterable


    class OakStatus(str, Enum):
        EXPLORATORY = "EXPLORATORY"
        FORMALIZED = "FORMALIZED"
        SIMULATED = "SIMULATED"
        DEMONSTRATED = "DEMONSTRATED"
        REPLICATED = "REPLICATED"
        CANONICAL = "CANONICAL"


    class InformationStatus(str, Enum):
        OBSERVED = "OBSERVED"
        INFERRED = "INFERRED"
        POSSIBLE = "POSSIBLE"
        PROJECTED = "PROJECTED"
        DESIRED = "DESIRED"
        MANIPULATED = "MANIPULATED"
        UNKNOWN = "UNKNOWN"


    class AssetState(str, Enum):
        IDEA = "IDEA"
        DRAFT = "DRAFT"
        REVIEW = "REVIEW"
        REVISE = "REVISE"
        APPROVED = "APPROVED"
        LOCKED = "LOCKED"
        PRODUCED = "PRODUCED"
        INTEGRATED = "INTEGRATED"
        ARCHIVED = "ARCHIVED"


    class FrontierDecision(str, Enum):
        EXPAND = "EXPAND"
        HOLD = "HOLD"
        RESHARD = "RESHARD"
        DEFER = "DEFER"
        COMPRESS = "COMPRESS"
        REGENERATE = "REGENERATE"
        REDESIGN = "REDESIGN"
        STOP_SAFELY = "STOP-SAFELY"


    class ValidationError(ValueError):
        pass


    def json_ready(value: Any) -> Any:
        if is_dataclass(value):
            return json_ready(asdict(value))
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, dict):
            return {str(k): json_ready(v) for k, v in value.items()}
        if isinstance(value, (tuple, list, set)):
            return [json_ready(item) for item in value]
        return value


    def require_text(value: str, location: str, errors: list[str]) -> None:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{location}: non-empty text required")


    @dataclass(frozen=True)
    class Provenance:
        source_id: str
        source_kind: str
        license_id: str
        created_by: str
        created_at: str
        derivation: tuple[str, ...] = ()
        private: bool = True

        def validate(self) -> list[str]:
            errors: list[str] = []
            for name in ("source_id", "source_kind", "license_id", "created_by", "created_at"):
                require_text(getattr(self, name), f"provenance.{name}", errors)
            return errors


    @dataclass(frozen=True)
    class AnimeNode:
        node_id: str
        node_type: str
        label: str
        status: OakStatus = OakStatus.FORMALIZED
        attributes: dict[str, Any] = field(default_factory=dict)

        def validate(self) -> list[str]:
            errors: list[str] = []
            require_text(self.node_id, "node.node_id", errors)
            require_text(self.node_type, f"node.{self.node_id}.node_type", errors)
            require_text(self.label, f"node.{self.node_id}.label", errors)
            return errors


    @dataclass(frozen=True)
    class HyperEdge:
        edge_id: str
        edge_type: str
        sources: tuple[str, ...]
        targets: tuple[str, ...]
        confidence: float = 1.0
        attributes: dict[str, Any] = field(default_factory=dict)

        def validate(self) -> list[str]:
            errors: list[str] = []
            require_text(self.edge_id, "edge.edge_id", errors)
            require_text(self.edge_type, f"edge.{self.edge_id}.edge_type", errors)
            if not self.sources:
                errors.append(f"edge.{self.edge_id}.sources: at least one source required")
            if not self.targets:
                errors.append(f"edge.{self.edge_id}.targets: at least one target required")
            if not 0.0 <= self.confidence <= 1.0:
                errors.append(f"edge.{self.edge_id}.confidence: must be in [0, 1]")
            return errors


    @dataclass(frozen=True)
    class CharacterIR:
        character_id: str
        name: str
        desire: str
        need: str
        fear: str
        contradiction: str
        power: str
        limitation: str
        moral_boundary: str
        voice_markers: tuple[str, ...] = ()
        motion_markers: tuple[str, ...] = ()
        knowledge: tuple[str, ...] = ()
        relationships: tuple[str, ...] = ()

        def validate(self) -> list[str]:
            errors: list[str] = []
            for name in (
                "character_id", "name", "desire", "need", "fear",
                "contradiction", "power", "limitation", "moral_boundary",
            ):
                require_text(getattr(self, name), f"character.{self.character_id}.{name}", errors)
            if self.power.strip().casefold() == self.limitation.strip().casefold():
                errors.append(f"character.{self.character_id}: power and limitation must differ")
            return errors


    @dataclass(frozen=True)
    class SceneIR:
        scene_id: str
        episode_id: str
        sequence_id: str
        order: int
        title: str
        duration_target_s: int
        objective: str
        conflict: str
        irreversible_change: str
        audience_before: tuple[str, ...]
        audience_after: tuple[str, ...]
        characters: tuple[str, ...]
        location_id: str
        promise_ids: tuple[str, ...] = ()
        causal_debt_ids: tuple[str, ...] = ()
        asset_ids: tuple[str, ...] = ()
        oak_status: OakStatus = OakStatus.FORMALIZED

        def validate(self) -> list[str]:
            errors: list[str] = []
            for name in (
                "scene_id", "episode_id", "sequence_id", "title", "objective",
                "conflict", "irreversible_change", "location_id",
            ):
                require_text(str(getattr(self, name)), f"scene.{self.scene_id}.{name}", errors)
            if self.order < 1:
                errors.append(f"scene.{self.scene_id}.order: must be >= 1")
            if self.duration_target_s < 1:
                errors.append(f"scene.{self.scene_id}.duration_target_s: must be >= 1")
            if not self.characters:
                errors.append(f"scene.{self.scene_id}.characters: at least one required")
            if set(self.audience_before) == set(self.audience_after):
                errors.append(f"scene.{self.scene_id}: audience information state must change")
            return errors


    @dataclass(frozen=True)
    class ShotIR:
        shot_id: str
        scene_id: str
        order: int
        duration_s: float
        purpose: str
        framing: str
        camera_motion: str
        subject_ids: tuple[str, ...]
        information_revealed: tuple[str, ...] = ()
        continuity_in: tuple[str, ...] = ()
        continuity_out: tuple[str, ...] = ()
        asset_ids: tuple[str, ...] = ()
        estimated_cost_units: float = 1.0

        def validate(self) -> list[str]:
            errors: list[str] = []
            for name in ("shot_id", "scene_id", "purpose", "framing", "camera_motion"):
                require_text(str(getattr(self, name)), f"shot.{self.shot_id}.{name}", errors)
            if self.order < 1:
                errors.append(f"shot.{self.shot_id}.order: must be >= 1")
            if self.duration_s <= 0:
                errors.append(f"shot.{self.shot_id}.duration_s: must be positive")
            if not self.subject_ids:
                errors.append(f"shot.{self.shot_id}.subject_ids: at least one required")
            if self.estimated_cost_units < 0:
                errors.append(f"shot.{self.shot_id}.estimated_cost_units: cannot be negative")
            return errors


    @dataclass(frozen=True)
    class CausalDebt:
        debt_id: str
        origin_scene_id: str
        local_benefit: str
        displaced_constraint: str
        affected_system: str
        certainty: float
        status: str = "OPEN"
        deadline: str = "UNKNOWN"

        def validate(self) -> list[str]:
            errors: list[str] = []
            for name in (
                "debt_id", "origin_scene_id", "local_benefit",
                "displaced_constraint", "affected_system", "status", "deadline",
            ):
                require_text(str(getattr(self, name)), f"causal_debt.{self.debt_id}.{name}", errors)
            if not 0.0 <= self.certainty <= 1.0:
                errors.append(f"causal_debt.{self.debt_id}.certainty: must be in [0,1]")
            return errors


    @dataclass(frozen=True)
    class AssetRecord:
        asset_id: str
        asset_type: str
        name: str
        state: AssetState
        provenance: Provenance
        dependencies: tuple[str, ...] = ()
        license_risk: str = "REVIEW"
        reusable: bool = True

        def validate(self) -> list[str]:
            errors: list[str] = []
            for name in ("asset_id", "asset_type", "name", "license_risk"):
                require_text(str(getattr(self, name)), f"asset.{self.asset_id}.{name}", errors)
            errors.extend(self.provenance.validate())
            return errors


    @dataclass(frozen=True)
    class AnimeProjectR1:
        project_id: str
        title: str
        logline: str
        theme_question: str
        target_duration_s: int
        world_rules: tuple[str, ...]
        visual_invariants: tuple[str, ...]
        characters: tuple[CharacterIR, ...]
        scenes: tuple[SceneIR, ...]
        shots: tuple[ShotIR, ...]
        causal_debts: tuple[CausalDebt, ...]
        assets: tuple[AssetRecord, ...]
        nodes: tuple[AnimeNode, ...]
        edges: tuple[HyperEdge, ...]
        oak_status: OakStatus = OakStatus.FORMALIZED
        risks: tuple[str, ...] = ()
        next_actions: tuple[str, ...] = ()
        metadata: dict[str, Any] = field(default_factory=dict)

        def validate(self) -> list[str]:
            errors: list[str] = []
            for name in ("project_id", "title", "logline", "theme_question"):
                require_text(str(getattr(self, name)), f"project.{name}", errors)
            if not self.theme_question.rstrip().endswith("?"):
                errors.append("project.theme_question: explicit question required")
            if self.target_duration_s < 30:
                errors.append("project.target_duration_s: must be >= 30")
            if len(self.world_rules) < 3:
                errors.append("project.world_rules: at least three required")
            if not self.visual_invariants:
                errors.append("project.visual_invariants: at least one required")
            if not self.risks:
                errors.append("project.risks: risk ledger required")

            collections: Iterable[Iterable[Any]] = (
                self.characters, self.scenes, self.shots, self.causal_debts,
                self.assets, self.nodes, self.edges,
            )
            for collection in collections:
                for item in collection:
                    errors.extend(item.validate())

            scene_ids = {scene.scene_id for scene in self.scenes}
            shot_scene_ids = {shot.scene_id for shot in self.shots}
            unknown_scene_ids = shot_scene_ids - scene_ids
            if unknown_scene_ids:
                errors.append(f"project.shots: unknown scene ids {sorted(unknown_scene_ids)}")

            character_ids = {character.character_id for character in self.characters}
            for scene in self.scenes:
                unknown = set(scene.characters) - character_ids
                if unknown:
                    errors.append(f"scene.{scene.scene_id}: unknown characters {sorted(unknown)}")

            asset_ids = {asset.asset_id for asset in self.assets}
            for shot in self.shots:
                unknown = set(shot.asset_ids) - asset_ids
                if unknown:
                    errors.append(f"shot.{shot.shot_id}: unknown assets {sorted(unknown)}")

            node_ids = {node.node_id for node in self.nodes}
            if len(node_ids) != len(self.nodes):
                errors.append("project.nodes: duplicate node_id")
            for edge in self.edges:
                missing = (set(edge.sources) | set(edge.targets)) - node_ids
                if missing:
                    errors.append(f"edge.{edge.edge_id}: unknown nodes {sorted(missing)}")

            scene_orders = [scene.order for scene in self.scenes]
            if scene_orders != sorted(scene_orders) or len(scene_orders) != len(set(scene_orders)):
                errors.append("project.scenes: order must be unique and ascending")

            for scene in self.scenes:
                scene_shots = sorted(
                    (shot for shot in self.shots if shot.scene_id == scene.scene_id),
                    key=lambda shot: shot.order,
                )
                if not scene_shots:
                    errors.append(f"scene.{scene.scene_id}: at least one shot required")
                    continue
                orders = [shot.order for shot in scene_shots]
                if orders != list(range(1, len(orders) + 1)):
                    errors.append(f"scene.{scene.scene_id}: shot order must be contiguous")
                duration = sum(shot.duration_s for shot in scene_shots)
                tolerance = max(1.0, scene.duration_target_s * 0.05)
                if abs(duration - scene.duration_target_s) > tolerance:
                    errors.append(
                        f"scene.{scene.scene_id}: shot duration {duration:.2f}s differs from target"
                    )

            total_scene_duration = sum(scene.duration_target_s for scene in self.scenes)
            if total_scene_duration != self.target_duration_s:
                errors.append(
                    f"project.duration: scene total {total_scene_duration} != target {self.target_duration_s}"
                )
            return errors

        def require_valid(self) -> None:
            errors = self.validate()
            if errors:
                raise ValidationError("\\n".join(errors))

        def to_dict(self) -> dict[str, Any]:
            return json_ready(asdict(self))
''').lstrip()

files['omega_anime_studio_t/matrix.py'] = dedent('''
    """The 16×16×32 Anime Studio matrix and deterministic registries."""

    from __future__ import annotations

    import hashlib
    import json
    from dataclasses import dataclass
    from pathlib import Path
    from typing import Iterator

    DOMAINS: dict[str, tuple[str, ...]] = {
''').lstrip() + ''.join(
    f'    {domain!r}: {tuple(modules)!r},\n' for domain, modules in DOMAINS.items()
) + dedent('''
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
        payload = '\\n'.join(
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
        with target.open('w', encoding='utf-8', newline='\\n') as handle:
            for cell in iter_matrix_cells():
                line = json.dumps(cell.to_dict(), ensure_ascii=False, sort_keys=True) + '\\n'
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
''')

files['omega_anime_studio_t/graph.py'] = dedent('''
    """Minimal deterministic hypergraph for worlds, narratives and production."""

    from __future__ import annotations

    from collections import defaultdict, deque
    from dataclasses import dataclass, field
    from typing import Iterable

    from .models import AnimeNode, HyperEdge


    @dataclass
    class AnimeGraph:
        nodes: dict[str, AnimeNode] = field(default_factory=dict)
        edges: dict[str, HyperEdge] = field(default_factory=dict)

        def add_node(self, node: AnimeNode) -> None:
            if node.node_id in self.nodes:
                raise ValueError(f'duplicate node: {node.node_id}')
            errors = node.validate()
            if errors:
                raise ValueError('; '.join(errors))
            self.nodes[node.node_id] = node

        def add_edge(self, edge: HyperEdge) -> None:
            if edge.edge_id in self.edges:
                raise ValueError(f'duplicate edge: {edge.edge_id}')
            errors = edge.validate()
            if errors:
                raise ValueError('; '.join(errors))
            missing = (set(edge.sources) | set(edge.targets)) - set(self.nodes)
            if missing:
                raise ValueError(f'edge {edge.edge_id} references unknown nodes: {sorted(missing)}')
            self.edges[edge.edge_id] = edge

        def extend_nodes(self, nodes: Iterable[AnimeNode]) -> None:
            for node in nodes:
                self.add_node(node)

        def extend_edges(self, edges: Iterable[HyperEdge]) -> None:
            for edge in edges:
                self.add_edge(edge)

        def validate(self) -> list[str]:
            errors: list[str] = []
            for node in self.nodes.values():
                errors.extend(node.validate())
            for edge in self.edges.values():
                errors.extend(edge.validate())
                missing = (set(edge.sources) | set(edge.targets)) - set(self.nodes)
                if missing:
                    errors.append(f'edge.{edge.edge_id}: unknown nodes {sorted(missing)}')
            return errors

        def adjacency(self, edge_type: str | None = None) -> dict[str, set[str]]:
            result: dict[str, set[str]] = defaultdict(set)
            for edge in self.edges.values():
                if edge_type is not None and edge.edge_type != edge_type:
                    continue
                for source in edge.sources:
                    result[source].update(edge.targets)
            return result

        def topological_order(self, edge_type: str = 'DEPENDS_ON') -> list[str]:
            adjacency = self.adjacency(edge_type)
            indegree = {node_id: 0 for node_id in self.nodes}
            for targets in adjacency.values():
                for target in targets:
                    indegree[target] += 1
            queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
            output: list[str] = []
            while queue:
                node = queue.popleft()
                output.append(node)
                for target in sorted(adjacency.get(node, ())):
                    indegree[target] -= 1
                    if indegree[target] == 0:
                        queue.append(target)
            if len(output) != len(self.nodes):
                cyclic = sorted(node for node, degree in indegree.items() if degree > 0)
                raise ValueError(f'cycle detected for {edge_type}: {cyclic}')
            return output

        def orphan_nodes(self) -> list[str]:
            connected: set[str] = set()
            for edge in self.edges.values():
                connected.update(edge.sources)
                connected.update(edge.targets)
            return sorted(set(self.nodes) - connected)
''').lstrip()

files['omega_anime_studio_t/frontier.py'] = dedent('''
    """Adaptive frontier controller with no permanent total-object ceiling."""

    from __future__ import annotations

    import hashlib
    import json
    from dataclasses import asdict, dataclass, field
    from itertools import product
    from pathlib import Path
    from typing import Iterator

    from .models import FrontierDecision


    @dataclass(frozen=True)
    class FrontierBudget:
        memory_bytes: int
        wall_time_s: float
        output_bytes: int
        quality_floor: float = 0.70
        duplicate_ceiling: float = 0.02
        blocking_error_ceiling: int = 0

        def validate(self) -> list[str]:
            errors: list[str] = []
            if self.memory_bytes <= 0:
                errors.append('budget.memory_bytes: positive value required')
            if self.wall_time_s <= 0:
                errors.append('budget.wall_time_s: positive value required')
            if self.output_bytes <= 0:
                errors.append('budget.output_bytes: positive value required')
            if not 0 <= self.quality_floor <= 1:
                errors.append('budget.quality_floor: must be in [0,1]')
            return errors


    @dataclass
    class FrontierState:
        generated: int = 0
        unique: int = 0
        accepted: int = 0
        duplicates: int = 0
        blocking_errors: int = 0
        estimated_memory_bytes: int = 0
        output_bytes: int = 0
        batch_size: int = 128
        shard_count: int = 1
        quality_sum: float = 0.0
        decisions: list[str] = field(default_factory=list)
        m_minus: list[dict[str, object]] = field(default_factory=list)

        @property
        def quality_mean(self) -> float:
            return self.quality_sum / self.generated if self.generated else 0.0

        @property
        def duplicate_rate(self) -> float:
            return self.duplicates / self.generated if self.generated else 0.0

        def to_dict(self) -> dict[str, object]:
            payload = asdict(self)
            payload['quality_mean'] = self.quality_mean
            payload['duplicate_rate'] = self.duplicate_rate
            return payload


    @dataclass(frozen=True)
    class SceneVariant:
        variant_id: str
        scene_id: str
        objective: str
        conflict: str
        revelation: str
        cost: str
        staging: str
        quality: float
        signature: str

        def to_dict(self) -> dict[str, object]:
            return asdict(self)


    OBJECTIVES = (
        'clarify anomaly', 'intensify responsibility', 'expose opposition',
        'test relationship', 'reveal causal debt', 'force irreversible choice',
        'compress world history', 'demonstrate power limit',
    )
    CONFLICTS = (
        'instrument disagreement', 'time pressure', 'ethical veto', 'resource loss',
        'misread relation', 'institutional secrecy', 'ally opposition', 'remote consequence',
    )
    REVELATIONS = (
        'shared constraint', 'hidden observer', 'false positive', 'displaced cost',
        'manipulated evidence', 'unknown branch', 'memory inconsistency', 'countermeasure',
    )
    COSTS = (
        'cognitive overload', 'lost trust', 'energy debt', 'injury risk',
        'exposed secret', 'closed future', 'asset destruction', 'moral compromise',
    )
    STAGINGS = (
        'single locked camera', 'subjective network vision', 'cross-cut consequence',
        'silent close-up', 'wide spatial proof', 'reflection composition',
        'handheld uncertainty', 'geometric overhead',
    )


    def iter_scene_variants(scene_id: str) -> Iterator[SceneVariant]:
        for index, values in enumerate(
            product(OBJECTIVES, CONFLICTS, REVELATIONS, COSTS, STAGINGS), start=1
        ):
            objective, conflict, revelation, cost, staging = values
            raw = '|'.join((scene_id, *values))
            signature = hashlib.sha256(raw.encode('utf-8')).hexdigest()
            # Stable heuristic: useful for deterministic routing, not artistic truth.
            quality = 0.55 + (int(signature[:8], 16) % 4500) / 10000
            yield SceneVariant(
                variant_id=f'{scene_id}-V{index:05d}',
                scene_id=scene_id,
                objective=objective,
                conflict=conflict,
                revelation=revelation,
                cost=cost,
                staging=staging,
                quality=round(min(0.9999, quality), 4),
                signature=signature,
            )


    class AdaptiveFrontierController:
        def __init__(self, budget: FrontierBudget, state: FrontierState | None = None):
            errors = budget.validate()
            if errors:
                raise ValueError('; '.join(errors))
            self.budget = budget
            self.state = state or FrontierState()
            self._seen: set[str] = set()

        def observe(self, variant: SceneVariant) -> None:
            state = self.state
            state.generated += 1
            state.quality_sum += variant.quality
            encoded_size = len(json.dumps(variant.to_dict(), ensure_ascii=False)) + 1
            state.output_bytes += encoded_size
            state.estimated_memory_bytes = len(self._seen) * 96
            if variant.signature in self._seen:
                state.duplicates += 1
                return
            self._seen.add(variant.signature)
            state.unique += 1
            if variant.quality >= self.budget.quality_floor:
                state.accepted += 1

        def decide(self) -> FrontierDecision:
            state = self.state
            if state.blocking_errors > self.budget.blocking_error_ceiling:
                decision = FrontierDecision.REDESIGN
            elif state.estimated_memory_bytes > self.budget.memory_bytes:
                decision = FrontierDecision.RESHARD
            elif state.output_bytes > self.budget.output_bytes:
                decision = FrontierDecision.COMPRESS
            elif state.duplicate_rate > self.budget.duplicate_ceiling:
                decision = FrontierDecision.REGENERATE
            elif state.generated and state.quality_mean < self.budget.quality_floor:
                decision = FrontierDecision.HOLD
            else:
                decision = FrontierDecision.EXPAND
            state.decisions.append(decision.value)
            return decision

        def adapt(self, decision: FrontierDecision) -> None:
            state = self.state
            if decision is FrontierDecision.EXPAND:
                finite_batch_budget = max(1, self.budget.memory_bytes // 256)
                state.batch_size = min(finite_batch_budget, max(1, (state.batch_size * 8) // 5))
            elif decision is FrontierDecision.RESHARD:
                previous = state.shard_count
                state.shard_count *= 2
                state.batch_size = max(1, state.batch_size // 2)
                state.m_minus.append({
                    'failure': 'memory pressure',
                    'previous_shards': previous,
                    'replacement': 'double shards and halve active batch',
                })
            elif decision is FrontierDecision.COMPRESS:
                state.batch_size = max(1, state.batch_size // 2)
                state.m_minus.append({
                    'failure': 'output budget pressure',
                    'replacement': 'retain generators, hashes and Pareto candidates',
                })
            elif decision in {FrontierDecision.HOLD, FrontierDecision.REDESIGN}:
                state.batch_size = max(1, state.batch_size // 2)

        def checkpoint(self, path: str | Path) -> None:
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps(self.state.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + '\\n',
                encoding='utf-8',
            )


    def compile_frontier_sample(
        path: str | Path,
        scene_ids: tuple[str, ...],
        work_items: int,
        budget: FrontierBudget,
    ) -> dict[str, object]:
        if work_items < 1:
            raise ValueError('work_items must be positive')
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        controller = AdaptiveFrontierController(budget)
        digest = hashlib.sha256()
        written = 0
        with target.open('w', encoding='utf-8', newline='\\n') as handle:
            iterators = [iter_scene_variants(scene_id) for scene_id in scene_ids]
            while written < work_items:
                progressed = False
                for iterator in iterators:
                    if written >= work_items:
                        break
                    try:
                        variant = next(iterator)
                    except StopIteration:
                        continue
                    progressed = True
                    controller.observe(variant)
                    line = json.dumps(variant.to_dict(), ensure_ascii=False, sort_keys=True) + '\\n'
                    handle.write(line)
                    digest.update(line.encode('utf-8'))
                    written += 1
                if not progressed:
                    break
                decision = controller.decide()
                controller.adapt(decision)
                if decision in {FrontierDecision.REDESIGN, FrontierDecision.STOP_SAFELY}:
                    break
        return {
            'written': written,
            'sha256': digest.hexdigest(),
            'state': controller.state.to_dict(),
            'no_permanent_total_cap': True,
            'finite_experiment_work_items': work_items,
        }
''').lstrip()

files['omega_anime_studio_t/eighth_fire.py'] = dedent('''
    """Canonical R1 Anime-IR seed for *Le Huitième Feu*."""

    from __future__ import annotations

    from .models import (
        AnimeNode, AnimeProjectR1, AssetRecord, AssetState, CausalDebt,
        CharacterIR, HyperEdge, OakStatus, Provenance, SceneIR, ShotIR,
    )


    def _provenance(source_id: str) -> Provenance:
        return Provenance(
            source_id=source_id,
            source_kind='tristan-original-canon',
            license_id='PRIVATE-DRAFT-NOT-LICENSED',
            created_by='Tristan + Ω-ANIME-STUDIO-T∞',
            created_at='2026-08-02',
            derivation=('Ω-ANIME-T∞ R0.1', 'Ω-ANIME-STUDIO-T∞ R1'),
            private=True,
        )


    def _shots_for_scene(
        scene_id: str,
        durations: tuple[float, ...],
        purposes: tuple[str, ...],
        framings: tuple[str, ...],
        motions: tuple[str, ...],
        subjects: tuple[tuple[str, ...], ...],
        reveals: tuple[tuple[str, ...], ...],
        assets: tuple[tuple[str, ...], ...],
    ) -> tuple[ShotIR, ...]:
        shots: list[ShotIR] = []
        for index, values in enumerate(
            zip(durations, purposes, framings, motions, subjects, reveals, assets), start=1
        ):
            duration, purpose, framing, motion, subject_ids, information, asset_ids = values
            shots.append(
                ShotIR(
                    shot_id=f'{scene_id}-SH{index:02d}',
                    scene_id=scene_id,
                    order=index,
                    duration_s=duration,
                    purpose=purpose,
                    framing=framing,
                    camera_motion=motion,
                    subject_ids=subject_ids,
                    information_revealed=information,
                    continuity_in=(f'{scene_id}:entry',),
                    continuity_out=(f'{scene_id}:exit',),
                    asset_ids=asset_ids,
                    estimated_cost_units=round(1.0 + index * 0.35, 2),
                )
            )
        return tuple(shots)


    def build_eighth_fire_r1() -> AnimeProjectR1:
        characters = (
            CharacterIR(
                character_id='CHAR-TRISTAN',
                name='Tristan',
                desire='comprendre une anomalie rejetée comme bruit',
                need='séparer cohérence, causalité et responsabilité',
                fear='déplacer un danger en croyant le supprimer',
                contradiction='il refuse les limites arbitraires mais doit respecter les limites causales',
                power='percevoir et reconfigurer temporairement des relations entre systèmes',
                limitation='chaque intervention produit surcharge, incertitude ou dette causale',
                moral_boundary='ne pas sacrifier une personne invisible pour optimiser un système visible',
                voice_markers=('questions précises', 'phrases compressées sous pression'),
                motion_markers=('regard périphérique', 'mains immobiles avant décision'),
                knowledge=('physique expérimentale', 'mesure', 'modèles incomplets'),
                relationships=('CHAR-OBSERVATRICE', 'ORG-LAB', 'SYS-CAUSAL-NET'),
            ),
            CharacterIR(
                character_id='CHAR-OBSERVATRICE',
                name="L'Observatrice",
                desire='déterminer si Tristan est une bifurcation contrôlable',
                need='accepter qu’un futur fertile ne peut être entièrement sécurisé',
                fear='le retour d’une catastrophe issue d’une branche imprévisible',
                contradiction='elle protège le monde en supprimant sa capacité à changer',
                power='simuler et fermer des familles de futurs instables',
                limitation='ses modèles suppriment aussi des solutions qui n’existent pas encore',
                moral_boundary='aucune bifurcation ne doit menacer la continuité globale',
                voice_markers=('constats sans adjectifs', 'questions qui présupposent une réponse'),
                motion_markers=('immobilité dominante', 'déplacement hors champ'),
                knowledge=('archives du Huitième Feu', 'réseau de surveillance causal'),
                relationships=('CHAR-TRISTAN', 'ORG-CONVERGENCE'),
            ),
        )

        scenes = (
            SceneIR(
                scene_id='S01-NOISE', episode_id='E00-PILOT', sequence_id='Q01-LAB', order=1,
                title='Le bruit', duration_target_s=32,
                objective='établir une anomalie mesurable et la routine du laboratoire',
                conflict='les instruments rejettent la trace comme artefact',
                irreversible_change='Tristan conserve une trace que le protocole exige de supprimer',
                audience_before=('le laboratoire fonctionne normalement',),
                audience_after=('plusieurs sous-systèmes partagent une anomalie corrélée',),
                characters=('CHAR-TRISTAN',), location_id='LOC-LAB',
                promise_ids=('PROM-TRACE',), asset_ids=('ENV-LAB','PROP-SPECTROMETER','FX-NOISE'),
            ),
            SceneIR(
                scene_id='S02-NETWORK', episode_id='E00-PILOT', sequence_id='Q01-LAB', order=2,
                title='Le réseau', duration_target_s=34,
                objective='montrer la perception hypergraphique sans la certifier',
                conflict='Tristan ignore si le réseau est observé ou projeté',
                irreversible_change='il choisit un nœud minimal à perturber',
                audience_before=('la trace est une anomalie instrumentale possible',),
                audience_after=('les événements séparés peuvent partager une contrainte',),
                characters=('CHAR-TRISTAN',), location_id='LOC-LAB',
                promise_ids=('PROM-NETWORK',), asset_ids=('ENV-LAB','FX-CAUSAL-NET','PROP-CONTROL'),
            ),
            SceneIR(
                scene_id='S03-CORRECTION', episode_id='E00-PILOT', sequence_id='Q02-INTERVENTION', order=3,
                title='La correction', duration_target_s=34,
                objective='faire réussir une intervention locale crédible',
                conflict='le temps manque et aucune validation complète n’est possible',
                irreversible_change='le laboratoire évite une panne grâce à Tristan',
                audience_before=('Tristan peut voir le réseau',),
                audience_after=('Tristan peut modifier un chemin causal',),
                characters=('CHAR-TRISTAN',), location_id='LOC-LAB',
                promise_ids=('PROM-ABILITY',), asset_ids=('ENV-LAB','FX-CAUSAL-NET','PROP-CONTROL'),
            ),
            SceneIR(
                scene_id='S04-DISPLACEMENT', episode_id='E00-PILOT', sequence_id='Q02-INTERVENTION', order=4,
                title='Le déplacement', duration_target_s=38,
                objective='prouver que le pouvoir ne donne pas de solution gratuite',
                conflict='un système éloigné se désynchronise après le sauvetage local',
                irreversible_change='une dette causale est créée hors du laboratoire',
                audience_before=('la panne a été empêchée',),
                audience_after=('la contrainte a été déplacée vers le réseau du district',),
                characters=('CHAR-TRISTAN',), location_id='LOC-LAB',
                promise_ids=('PROM-DEBT',), causal_debt_ids=('CD-0001',),
                asset_ids=('ENV-LAB','ENV-GRID','FX-CAUSAL-FRACTURE'),
            ),
            SceneIR(
                scene_id='S05-EIGHTH-FIRE', episode_id='E00-PILOT', sequence_id='Q03-OBSERVATION', order=5,
                title='Le Huitième Feu', duration_target_s=42,
                objective='nommer le phénomène et ouvrir un antagonisme précis',
                conflict='une observatrice interprète l’acte avant Tristan',
                irreversible_change='Tristan est identifié par une organisation externe',
                audience_before=('la dette causale semble accidentelle',),
                audience_after=('le phénomène était surveillé et possède un nom',),
                characters=('CHAR-TRISTAN','CHAR-OBSERVATRICE'), location_id='LOC-LAB',
                promise_ids=('PROM-OBSERVER','PROM-EIGHTH-FIRE'), causal_debt_ids=('CD-0001',),
                asset_ids=('ENV-LAB','ENV-OBSERVATORY','FX-CAUSAL-NET','AUD-OBSERVER-VOICE'),
            ),
        )

        shot_specs = {
            'S01-NOISE': ((5,5,6,6,5,5), ('establish','measure','reject','notice','compare','decide'), ('wide','insert','screen close-up','eye close-up','split detail','hand close-up'), ('locked','micro push','locked','slow push','lateral slide','locked'), (('LOC-LAB',),('PROP-SPECTROMETER',),('PROP-SPECTROMETER',),('CHAR-TRISTAN',),('FX-NOISE','CHAR-TRISTAN'),('CHAR-TRISTAN','PROP-SPECTROMETER')), ((),('trace visible',),('protocol rejection',),('Tristan notices recurrence',),('cross-system correlation',),('trace retained',)), (('ENV-LAB',),('PROP-SPECTROMETER',),('PROP-SPECTROMETER','FX-NOISE'),('CHAR-TRISTAN-RIG',),('FX-NOISE','CHAR-TRISTAN-RIG'),('CHAR-TRISTAN-RIG','PROP-SPECTROMETER'))),
            'S02-NETWORK': ((5,6,6,6,6,5), ('re-enter','first filament','expand relation','question reality','choose node','commit'), ('medium','macro','subjective wide','close-up','insert','overhead'), ('locked','track filament','subjective drift','handheld micro','rack focus','geometric rise'), (('CHAR-TRISTAN',),('FX-CAUSAL-NET',),('LOC-LAB','FX-CAUSAL-NET'),('CHAR-TRISTAN',),('PROP-CONTROL',),('CHAR-TRISTAN','FX-CAUSAL-NET')), ((),('first relation',),('network topology',),('uncertainty status',),('candidate node',),('choice made',)), (('CHAR-TRISTAN-RIG','ENV-LAB'),('FX-CAUSAL-NET',),('ENV-LAB','FX-CAUSAL-NET'),('CHAR-TRISTAN-RIG',),('PROP-CONTROL',),('CHAR-TRISTAN-RIG','FX-CAUSAL-NET'))),
            'S03-CORRECTION': ((5,5,6,6,6,6), ('countdown','prepare','intervene','system response','false calm','confirm'), ('insert','medium','subjective close','wide','close-up','screen insert'), ('locked','slow orbit','network surge','snap wide','locked','micro push'), (('PROP-CONTROL',),('CHAR-TRISTAN',),('FX-CAUSAL-NET',),('LOC-LAB',),('CHAR-TRISTAN',),('PROP-SPECTROMETER',)), (('time pressure',),(),('path reconfigured',),('panne évitée',),('cost not yet visible',),('local success',)), (('PROP-CONTROL',),('CHAR-TRISTAN-RIG',),('FX-CAUSAL-NET',),('ENV-LAB',),('CHAR-TRISTAN-RIG',),('PROP-SPECTROMETER',))),
            'S04-DISPLACEMENT': ((6,6,7,7,6,6), ('silence','remote cut','desync','recognition','debt forms','return'), ('close-up','extreme wide','technical insert','eye close-up','subjective fracture','medium'), ('locked','hard cut','vibration','slow push','fracture spread','handheld settle'), (('CHAR-TRISTAN',),('ENV-GRID',),('ENV-GRID',),('CHAR-TRISTAN',),('FX-CAUSAL-FRACTURE',),('CHAR-TRISTAN',)), ((),('remote system',),('grid desynchronization',),('causal link recognized',),('debt created',),('responsibility begins',)), (('CHAR-TRISTAN-RIG',),('ENV-GRID',),('ENV-GRID','FX-CAUSAL-FRACTURE'),('CHAR-TRISTAN-RIG',),('FX-CAUSAL-FRACTURE',),('CHAR-TRISTAN-RIG','ENV-LAB'))),
            'S05-EIGHTH-FIRE': ((6,7,7,7,8,7), ('observe Tristan','reveal observer','name phenomenon','define distinction','expand network','end hook'), ('medium back','silhouette wide','mouthless close','network insert','cosmic wide','eye close-up'), ('slow pull','locked','invisible voice','filament track','rapid expansion','cut to black'), (('CHAR-TRISTAN',),('CHAR-OBSERVATRICE',),('AUD-OBSERVER-VOICE',),('FX-CAUSAL-NET',),('SYS-CAUSAL-NET',),('CHAR-TRISTAN',)), ((),('observer exists',),('Huitième Feu named',),('not energy but accessible paths',),('network is planetary',),('Tristan is watched',)), (('CHAR-TRISTAN-RIG','ENV-LAB'),('CHAR-OBSERVATRICE-RIG','ENV-OBSERVATORY'),('AUD-OBSERVER-VOICE',),('FX-CAUSAL-NET',),('FX-CAUSAL-NET','ENV-OBSERVATORY'),('CHAR-TRISTAN-RIG',))),
        }
        shots = tuple(
            shot
            for scene_id, spec in shot_specs.items()
            for shot in _shots_for_scene(scene_id, *spec)
        )

        debts = (
            CausalDebt(
                debt_id='CD-0001', origin_scene_id='S04-DISPLACEMENT',
                local_benefit='panne du laboratoire évitée',
                displaced_constraint='synchronisation énergétique devenue instable',
                affected_system='district-grid-07', certainty=0.62,
                status='OPEN', deadline='UNKNOWN',
            ),
        )

        asset_specs = (
            ('ENV-LAB','environment','Laboratoire principal'),
            ('ENV-GRID','environment','Réseau énergétique du district'),
            ('ENV-OBSERVATORY','environment','Observatoire de convergence'),
            ('CHAR-TRISTAN-RIG','character-rig','Rig Tristan R1'),
            ('CHAR-OBSERVATRICE-RIG','character-rig','Rig Observatrice R1'),
            ('PROP-SPECTROMETER','prop','Spectromètre analytique'),
            ('PROP-CONTROL','prop','Interface de contrôle'),
            ('FX-NOISE','effect','Bruit corrélé'),
            ('FX-CAUSAL-NET','effect','Réseau causal'),
            ('FX-CAUSAL-FRACTURE','effect','Fracture et dette causale'),
            ('AUD-OBSERVER-VOICE','audio','Voix temporaire de l’Observatrice'),
        )
        assets = tuple(
            AssetRecord(
                asset_id=asset_id, asset_type=asset_type, name=name,
                state=AssetState.DRAFT, provenance=_provenance(asset_id),
                dependencies=(), license_risk='PRIVATE-DRAFT', reusable=True,
            )
            for asset_id, asset_type, name in asset_specs
        )

        nodes = (
            AnimeNode('PROJECT-EIGHTH-FIRE','Project','Le Huitième Feu'),
            AnimeNode('E00-PILOT','Episode','Pilote 180 secondes'),
            *(AnimeNode(character.character_id,'Character',character.name) for character in characters),
            *(AnimeNode(scene.scene_id,'Scene',scene.title) for scene in scenes),
            *(AnimeNode(debt.debt_id,'CausalDebt',debt.displaced_constraint) for debt in debts),
            AnimeNode('LOC-LAB','Location','Laboratoire'),
            AnimeNode('SYS-CAUSAL-NET','System','Réseau causal'),
            AnimeNode('ORG-CONVERGENCE','Organization','Organisation de convergence'),
            AnimeNode('ORG-LAB','Organization','Laboratoire'),
        )
        edges = (
            HyperEdge('EDGE-PROJECT-EPISODE','CONTAINS',('PROJECT-EIGHTH-FIRE',),('E00-PILOT',)),
            *(HyperEdge(f'EDGE-E00-{scene.scene_id}','CONTAINS',('E00-PILOT',),(scene.scene_id,)) for scene in scenes),
            HyperEdge('EDGE-TRISTAN-LAB','MEMBER_OF',('CHAR-TRISTAN',),('ORG-LAB',)),
            HyperEdge('EDGE-OBSERVER-CONVERGENCE','MEMBER_OF',('CHAR-OBSERVATRICE',),('ORG-CONVERGENCE',)),
            HyperEdge('EDGE-TRISTAN-NET','PERCEIVES',('CHAR-TRISTAN',),('SYS-CAUSAL-NET',),0.68),
            HyperEdge('EDGE-S04-DEBT','CAUSES',('S04-DISPLACEMENT',),('CD-0001',),0.62),
            HyperEdge('EDGE-DEBT-NET','AFFECTS',('CD-0001',),('SYS-CAUSAL-NET',),0.62),
            HyperEdge('EDGE-OBSERVER-TRISTAN','OBSERVES',('CHAR-OBSERVATRICE',),('CHAR-TRISTAN',),0.99),
        )

        return AnimeProjectR1(
            project_id='omega-anime-studio/eighth-fire/pilot-r1',
            title='Le Huitième Feu',
            logline=(
                'Un étudiant qui perçoit les relations invisibles entre les systèmes '
                'sauve son laboratoire, puis découvre que sa correction a déplacé le danger.'
            ),
            theme_question='Peut-on améliorer un système sans devenir responsable de toutes ses conséquences?',
            target_duration_s=180,
            world_rules=(
                'Le Huitième Feu révèle des relations; il ne crée ni matière ni énergie.',
                'Toute reconfiguration locale conserve un coût ou déplace une contrainte.',
                'Une relation perçue peut être observée, inférée, possible, projetée ou manipulée.',
                'Plus le réseau observé est large, plus l’incertitude et la surcharge augmentent.',
                'Toute exception canonique doit être inscrite et testée.',
            ),
            visual_invariants=(
                'les filaments représentent des relations et non une décoration',
                'forme, stabilité, mouvement et son encodent le statut d’information',
                'les fractures signalent un résidu ou une dette causale',
                'la caméra reste physique avant chaque perception hypergraphique',
            ),
            characters=characters, scenes=scenes, shots=shots, causal_debts=debts,
            assets=assets, nodes=tuple(nodes), edges=tuple(edges),
            oak_status=OakStatus.FORMALIZED,
            risks=(
                'surcharge d’exposition scientifique',
                'confusion entre visualisation narrative et preuve physique',
                'ressemblance involontaire avec une œuvre existante',
                'coût de cohérence des effets et décors',
                'voix temporaire non publiable sans provenance et consentement',
            ),
            next_actions=(
                'produire un storyboard basse fidélité pour les trente plans',
                'tester la compréhension sans fournir la bible',
                'mesurer la durée réelle de chaque plan',
                'exécuter IPGate avant tout actif public',
            ),
            metadata={
                'version': 'R1', 'language': 'fr-CA',
                'publication_state': 'private-draft',
                'primary_artifact': 'animatic-180s',
            },
        )
''').lstrip()

files['omega_anime_studio_t/compiler.py'] = dedent('''
    """Deterministic compiler for reviewable Anime Studio R1 bundles."""

    from __future__ import annotations

    import hashlib
    import json
    from pathlib import Path
    from typing import Any, Iterable

    from .frontier import FrontierBudget, compile_frontier_sample
    from .matrix import matrix_summary, write_matrix_jsonl
    from .models import AnimeProjectR1, json_ready


    def canonical_json(payload: Any) -> str:
        return json.dumps(json_ready(payload), ensure_ascii=False, sort_keys=True, indent=2) + '\\n'


    def write_json(path: Path, payload: Any) -> None:
        path.write_text(canonical_json(payload), encoding='utf-8')


    def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
        count = 0
        with path.open('w', encoding='utf-8', newline='\\n') as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\\n')
                count += 1
        return count


    def file_hash(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()


    def compile_project_bundle(
        project: AnimeProjectR1,
        output_dir: str | Path,
        *,
        frontier_work_items: int = 2048,
    ) -> dict[str, Any]:
        project.require_valid()
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        write_json(output / 'anime-ir.json', project.to_dict())
        write_jsonl(output / 'characters.jsonl', (item.__dict__ for item in project.characters))
        write_jsonl(output / 'scenes.jsonl', (json_ready(item.__dict__) for item in project.scenes))
        write_jsonl(output / 'shots.jsonl', (json_ready(item.__dict__) for item in project.shots))
        write_jsonl(output / 'causal-debts.jsonl', (item.__dict__ for item in project.causal_debts))
        write_jsonl(output / 'assets.jsonl', (json_ready(item.__dict__) for item in project.assets))
        write_jsonl(output / 'nodes.jsonl', (json_ready(item.__dict__) for item in project.nodes))
        write_jsonl(output / 'edges.jsonl', (json_ready(item.__dict__) for item in project.edges))

        matrix_report = write_matrix_jsonl(output / 'matrix-8192.jsonl')
        write_json(output / 'matrix-summary.json', matrix_report)

        frontier_report = compile_frontier_sample(
            output / 'shot-frontier.jsonl',
            tuple(scene.scene_id for scene in project.scenes),
            frontier_work_items,
            FrontierBudget(
                memory_bytes=32 * 1024 * 1024,
                wall_time_s=60.0,
                output_bytes=64 * 1024 * 1024,
                quality_floor=0.70,
            ),
        )
        write_json(output / 'frontier-report.json', frontier_report)

        files = {}
        for path in sorted(output.iterdir()):
            if path.name in {'manifest.json', 'report.md'}:
                continue
            files[path.name] = {
                'sha256': file_hash(path),
                'bytes': path.stat().st_size,
            }

        manifest_base = {
            'schema_version': 'omega-anime-studio/r1',
            'project_id': project.project_id,
            'oak_status': project.oak_status.value,
            'publication_state': project.metadata.get('publication_state'),
            'scene_count': len(project.scenes),
            'shot_count': len(project.shots),
            'matrix_cell_count': matrix_summary()['cell_count'],
            'frontier_work_items': frontier_work_items,
            'files': files,
        }
        manifest_hash = hashlib.sha256(canonical_json(manifest_base).encode('utf-8')).hexdigest()
        manifest = {**manifest_base, 'manifest_sha256': manifest_hash}
        write_json(output / 'manifest.json', manifest)

        report = [
            '# Le Huitième Feu — Ω-ANIME-STUDIO-T∞ R1', '',
            f"- Project: `{project.project_id}`",
            f"- OAK status: `{project.oak_status.value}`",
            f"- Scenes: `{len(project.scenes)}`",
            f"- Shots: `{len(project.shots)}`",
            f"- Matrix cells: `{manifest['matrix_cell_count']}`",
            f"- Frontier sample: `{frontier_work_items}` variants",
            f"- Manifest: `{manifest_hash}`", '',
            '## Boundary', '',
            'The bundle proves deterministic structure and internal validation only.',
            'It does not prove artistic quality, audience demand, legal clearance,',
            'scientific truth, production feasibility or commercial success.', '',
        ]
        (output / 'report.md').write_text('\\n'.join(report), encoding='utf-8')
        return manifest
''').lstrip()

files['omega_anime_studio_t/__init__.py'] = dedent('''
    """Ω-ANIME-STUDIO-T∞ R1 public API."""

    from .compiler import compile_project_bundle
    from .eighth_fire import build_eighth_fire_r1
    from .frontier import (
        AdaptiveFrontierController, FrontierBudget, FrontierState,
        compile_frontier_sample, iter_scene_variants,
    )
    from .graph import AnimeGraph
    from .matrix import (
        ARTIFACT_KINDS, DOMAINS, iter_matrix_cells, matrix_summary,
        validate_matrix, write_matrix_jsonl,
    )
    from .models import *

    __all__ = [
        'AdaptiveFrontierController','AnimeGraph','ARTIFACT_KINDS','DOMAINS',
        'FrontierBudget','FrontierState','build_eighth_fire_r1',
        'compile_frontier_sample','compile_project_bundle','iter_matrix_cells',
        'iter_scene_variants','matrix_summary','validate_matrix','write_matrix_jsonl',
    ]
    __version__ = '1.0.0'
''').lstrip()

files['omega_anime_studio_t/__main__.py'] = dedent('''
    """CLI for Ω-ANIME-STUDIO-T∞ R1."""

    from __future__ import annotations

    import argparse
    import json
    from pathlib import Path

    from .compiler import compile_project_bundle
    from .eighth_fire import build_eighth_fire_r1
    from .frontier import FrontierBudget, compile_frontier_sample
    from .matrix import matrix_summary, validate_matrix, write_matrix_jsonl


    def parser() -> argparse.ArgumentParser:
        root = argparse.ArgumentParser(prog='omega-anime-studio')
        commands = root.add_subparsers(dest='command', required=True)
        commands.add_parser('matrix-summary')
        matrix = commands.add_parser('write-matrix')
        matrix.add_argument('--output', type=Path, required=True)
        validate = commands.add_parser('validate-demo')
        compile_cmd = commands.add_parser('compile-demo')
        compile_cmd.add_argument('--output-dir', type=Path, required=True)
        compile_cmd.add_argument('--frontier-work-items', type=int, default=2048)
        frontier = commands.add_parser('frontier')
        frontier.add_argument('--output', type=Path, required=True)
        frontier.add_argument('--work-items', type=int, default=10000)
        return root


    def main(argv: list[str] | None = None) -> int:
        args = parser().parse_args(argv)
        if args.command == 'matrix-summary':
            print(json.dumps(matrix_summary(), sort_keys=True, indent=2))
            return 0
        if args.command == 'write-matrix':
            print(json.dumps(write_matrix_jsonl(args.output), sort_keys=True, indent=2))
            return 0
        if args.command == 'validate-demo':
            project = build_eighth_fire_r1()
            errors = [*validate_matrix(), *project.validate()]
            print(json.dumps({'errors': errors, 'valid': not errors}, ensure_ascii=False, indent=2))
            return 0 if not errors else 2
        if args.command == 'compile-demo':
            manifest = compile_project_bundle(
                build_eighth_fire_r1(), args.output_dir,
                frontier_work_items=args.frontier_work_items,
            )
            print(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2))
            return 0
        if args.command == 'frontier':
            report = compile_frontier_sample(
                args.output,
                ('S01-NOISE','S02-NETWORK','S03-CORRECTION','S04-DISPLACEMENT','S05-EIGHTH-FIRE'),
                args.work_items,
                FrontierBudget(
                    memory_bytes=64 * 1024 * 1024,
                    wall_time_s=120.0,
                    output_bytes=256 * 1024 * 1024,
                ),
            )
            print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
            return 0
        raise AssertionError(args.command)


    if __name__ == '__main__':
        raise SystemExit(main())
''').lstrip()

# JSON schema intentionally broad enough for nested R1 payload but strict at top level.
files['schemas/anime-ir-r1.schema.json'] = json.dumps({
    '$schema': 'https://json-schema.org/draft/2020-12/schema',
    '$id': 'https://tfuga.example/schemas/anime-ir-r1.schema.json',
    'title': 'Omega Anime Studio R1 Anime-IR',
    'type': 'object',
    'additionalProperties': False,
    'required': ['project_id','title','logline','theme_question','target_duration_s','world_rules','visual_invariants','characters','scenes','shots','causal_debts','assets','nodes','edges','oak_status','risks','next_actions','metadata'],
    'properties': {
        'project_id': {'type':'string','minLength':1},
        'title': {'type':'string','minLength':1},
        'logline': {'type':'string','minLength':20},
        'theme_question': {'type':'string','pattern':'\\?$'},
        'target_duration_s': {'type':'integer','minimum':30},
        'world_rules': {'type':'array','minItems':3,'items':{'type':'string','minLength':1}},
        'visual_invariants': {'type':'array','minItems':1,'items':{'type':'string','minLength':1}},
        'characters': {'type':'array','minItems':1,'items':{'$ref':'#/$defs/character'}},
        'scenes': {'type':'array','minItems':1,'items':{'$ref':'#/$defs/scene'}},
        'shots': {'type':'array','minItems':1,'items':{'$ref':'#/$defs/shot'}},
        'causal_debts': {'type':'array','items':{'type':'object'}},
        'assets': {'type':'array','minItems':1,'items':{'type':'object'}},
        'nodes': {'type':'array','minItems':1,'items':{'type':'object'}},
        'edges': {'type':'array','minItems':1,'items':{'type':'object'}},
        'oak_status': {'enum':['EXPLORATORY','FORMALIZED','SIMULATED','DEMONSTRATED','REPLICATED','CANONICAL']},
        'risks': {'type':'array','minItems':1,'items':{'type':'string'}},
        'next_actions': {'type':'array','items':{'type':'string'}},
        'metadata': {'type':'object'},
    },
    '$defs': {
        'character': {
            'type':'object','additionalProperties':False,
            'required':['character_id','name','desire','need','fear','contradiction','power','limitation','moral_boundary','voice_markers','motion_markers','knowledge','relationships'],
            'properties': {k: {'type':'string','minLength':1} for k in ['character_id','name','desire','need','fear','contradiction','power','limitation','moral_boundary']} | {
                k: {'type':'array','items':{'type':'string'}} for k in ['voice_markers','motion_markers','knowledge','relationships']
            },
        },
        'scene': {
            'type':'object','additionalProperties':False,
            'required':['scene_id','episode_id','sequence_id','order','title','duration_target_s','objective','conflict','irreversible_change','audience_before','audience_after','characters','location_id','promise_ids','causal_debt_ids','asset_ids','oak_status'],
            'properties': {
                **{k:{'type':'string','minLength':1} for k in ['scene_id','episode_id','sequence_id','title','objective','conflict','irreversible_change','location_id']},
                'order':{'type':'integer','minimum':1},'duration_target_s':{'type':'integer','minimum':1},
                **{k:{'type':'array','items':{'type':'string'}} for k in ['audience_before','audience_after','characters','promise_ids','causal_debt_ids','asset_ids']},
                'oak_status':{'type':'string'},
            },
        },
        'shot': {
            'type':'object','additionalProperties':False,
            'required':['shot_id','scene_id','order','duration_s','purpose','framing','camera_motion','subject_ids','information_revealed','continuity_in','continuity_out','asset_ids','estimated_cost_units'],
            'properties': {
                **{k:{'type':'string','minLength':1} for k in ['shot_id','scene_id','purpose','framing','camera_motion']},
                'order':{'type':'integer','minimum':1},'duration_s':{'type':'number','exclusiveMinimum':0},
                'estimated_cost_units':{'type':'number','minimum':0},
                **{k:{'type':'array','items':{'type':'string'}} for k in ['subject_ids','information_revealed','continuity_in','continuity_out','asset_ids']},
            },
        },
    },
}, ensure_ascii=False, indent=2, sort_keys=True) + '\n'

policy = {
    'policy_id':'omega-anime-studio/r1',
    'status':'OAK_SAFE_PRIVATE_DRAFT',
    'no_permanent_total_object_cap':True,
    'finite_runs_remain_resource_bounded':True,
    'adaptive_controls':['backpressure','sharding','streaming','checkpointing','quality_floor','deduplication','rollback','human_stop'],
    'human_approval_required':['public_release','merge_to_protected_branch','commercial_license','voice_or_likeness_use','paid_distribution','trademark_or_copyright_filing','irreversible_deletion'],
    'promotion_gates':{
        'FORMALIZED':['valid Anime-IR','world rules','characters','scenes','shots','risk ledger'],
        'SIMULATED':['timed storyboard or animatic','measured duration','continuity pass'],
        'DEMONSTRATED':['human audience test','baseline cut','failure conditions'],
        'REPLICATED':['independent review','second panel','reproducible asset manifest'],
        'CANONICAL':['showrunner approval','IP clearance','production feasibility','archived sources'],
    },
    'forbidden_shortcuts':['synthetic audience as market proof','internal coherence as artistic quality','visual metaphor as physical proof','living artist style imitation','unlicensed voice music font or image','automatic canon promotion'],
    'm_minus':[
        {'id':'M-ANIME-R1-001','failure':'volume treated as finished work','replacement':'every campaign must improve a watchable artifact'},
        {'id':'M-ANIME-R1-002','failure':'one file per micro-object','replacement':'JSONL shards, indexed stores and compact manifests'},
        {'id':'M-ANIME-R1-003','failure':'generation before invariants','replacement':'lock WorldRules, StyleDNA and CharacterDNA first'},
        {'id':'M-ANIME-R1-004','failure':'software tests mistaken for artistic validation','replacement':'add human review and audience experiments'},
        {'id':'M-ANIME-R1-005','failure':'automatic publication','replacement':'private-draft plus explicit IPGate and human approval'},
        {'id':'M-ANIME-R1-006','failure':'fixed arbitrary total cap','replacement':'adaptive finite experiments with saturation memory and redesign'},
    ],
}
files['policies/omega_anime_studio_r1.json'] = json.dumps(policy, ensure_ascii=False, indent=2, sort_keys=True) + '\n'

files['examples/omega_anime_studio_r1_demo.py'] = dedent('''
    """Compile the R1 studio bundle and print its evidence summary."""
    from pathlib import Path
    from omega_anime_studio_t import build_eighth_fire_r1, compile_project_bundle

    if __name__ == '__main__':
        output = Path('generated/omega_anime_studio_t/eighth_fire_r1')
        manifest = compile_project_bundle(build_eighth_fire_r1(), output)
        print(f"project={manifest['project_id']}")
        print(f"shots={manifest['shot_count']}")
        print(f"matrix_cells={manifest['matrix_cell_count']}")
        print(f"sha256={manifest['manifest_sha256']}")
''').lstrip()

files['tests/test_omega_anime_studio_t_r1.py'] = dedent('''
    from __future__ import annotations

    import json
    from dataclasses import replace

    import pytest

    from omega_anime_studio_t import (
        AdaptiveFrontierController, AnimeGraph, FrontierBudget,
        build_eighth_fire_r1, compile_frontier_sample, compile_project_bundle,
        iter_matrix_cells, iter_scene_variants, matrix_summary, validate_matrix,
        write_matrix_jsonl,
    )
    from omega_anime_studio_t.models import AnimeNode, HyperEdge


    def test_matrix_has_16_domains_256_modules_and_8192_cells() -> None:
        summary = matrix_summary()
        assert summary['domain_count'] == 16
        assert summary['module_count'] == 256
        assert summary['artifact_kind_count'] == 32
        assert summary['cell_count'] == 8192
        assert summary['unique_cell_count'] == 8192
        assert validate_matrix() == []


    def test_matrix_ids_are_deterministic_and_unique() -> None:
        first = list(iter_matrix_cells())
        second = list(iter_matrix_cells())
        assert first == second
        assert len({cell.cell_id for cell in first}) == len(first)
        assert first[0].cell_id == 'ANIME-R1-D01-M01-A01'
        assert first[-1].cell_id == 'ANIME-R1-D16-M16-A32'


    def test_write_matrix_jsonl(tmp_path) -> None:
        report = write_matrix_jsonl(tmp_path / 'matrix.jsonl')
        lines = (tmp_path / 'matrix.jsonl').read_text(encoding='utf-8').splitlines()
        assert len(lines) == 8192
        assert report['written'] == 8192
        assert len(report['file_sha256']) == 64
        assert json.loads(lines[0])['cell_id'] == 'ANIME-R1-D01-M01-A01'


    def test_eighth_fire_r1_is_valid() -> None:
        project = build_eighth_fire_r1()
        assert project.validate() == []
        project.require_valid()
        assert len(project.scenes) == 5
        assert len(project.shots) == 30
        assert sum(scene.duration_target_s for scene in project.scenes) == 180


    def test_each_scene_has_six_contiguous_shots() -> None:
        project = build_eighth_fire_r1()
        for scene in project.scenes:
            shots = [shot for shot in project.shots if shot.scene_id == scene.scene_id]
            assert len(shots) == 6
            assert [shot.order for shot in shots] == list(range(1, 7))
            assert sum(shot.duration_s for shot in shots) == scene.duration_target_s


    def test_every_power_has_a_limit_and_moral_boundary() -> None:
        for character in build_eighth_fire_r1().characters:
            assert character.power
            assert character.limitation
            assert character.moral_boundary
            assert character.power.casefold() != character.limitation.casefold()


    def test_every_asset_has_private_provenance() -> None:
        for asset in build_eighth_fire_r1().assets:
            assert asset.provenance.private is True
            assert asset.provenance.license_id == 'PRIVATE-DRAFT-NOT-LICENSED'


    def test_causal_debt_is_linked_to_scene() -> None:
        project = build_eighth_fire_r1()
        debt = project.causal_debts[0]
        scene = next(scene for scene in project.scenes if scene.scene_id == debt.origin_scene_id)
        assert debt.debt_id in scene.causal_debt_ids
        assert debt.status == 'OPEN'
        assert 0 <= debt.certainty <= 1


    def test_invalid_shot_scene_reference_is_rejected() -> None:
        project = build_eighth_fire_r1()
        shots = list(project.shots)
        shots[0] = replace(shots[0], scene_id='UNKNOWN')
        errors = replace(project, shots=tuple(shots)).validate()
        assert any('unknown scene ids' in error for error in errors)


    def test_invalid_character_reference_is_rejected() -> None:
        project = build_eighth_fire_r1()
        scenes = list(project.scenes)
        scenes[0] = replace(scenes[0], characters=('UNKNOWN',))
        errors = replace(project, scenes=tuple(scenes)).validate()
        assert any('unknown characters' in error for error in errors)


    def test_invalid_asset_reference_is_rejected() -> None:
        project = build_eighth_fire_r1()
        shots = list(project.shots)
        shots[0] = replace(shots[0], asset_ids=('UNKNOWN',))
        errors = replace(project, shots=tuple(shots)).validate()
        assert any('unknown assets' in error for error in errors)


    def test_graph_rejects_unknown_nodes() -> None:
        graph = AnimeGraph()
        graph.add_node(AnimeNode('A','Task','A'))
        with pytest.raises(ValueError):
            graph.add_edge(HyperEdge('E','DEPENDS_ON',('A',),('B',)))


    def test_graph_topological_order_and_cycle_detection() -> None:
        graph = AnimeGraph()
        graph.extend_nodes((AnimeNode('A','Task','A'), AnimeNode('B','Task','B')))
        graph.add_edge(HyperEdge('E1','DEPENDS_ON',('A',),('B',)))
        assert graph.topological_order() == ['A','B']
        graph.add_edge(HyperEdge('E2','DEPENDS_ON',('B',),('A',)))
        with pytest.raises(ValueError):
            graph.topological_order()


    def test_scene_variant_generator_is_large_and_deterministic() -> None:
        first = list(iter_scene_variants('S01'))
        second = list(iter_scene_variants('S01'))
        assert len(first) == 32768
        assert first[:10] == second[:10]
        assert len({item.signature for item in first}) == 32768


    def test_frontier_controller_has_no_total_cap() -> None:
        controller = AdaptiveFrontierController(
            FrontierBudget(memory_bytes=10_000_000, wall_time_s=1, output_bytes=10_000_000)
        )
        assert not hasattr(controller.budget, 'max_total')
        for variant in list(iter_scene_variants('S01'))[:100]:
            controller.observe(variant)
        assert controller.state.generated == 100
        assert controller.decide().value in {'EXPAND','HOLD'}


    def test_compile_frontier_sample(tmp_path) -> None:
        report = compile_frontier_sample(
            tmp_path / 'frontier.jsonl', ('S01','S02'), 2048,
            FrontierBudget(memory_bytes=10_000_000, wall_time_s=10, output_bytes=10_000_000),
        )
        assert report['written'] == 2048
        assert report['no_permanent_total_cap'] is True
        assert len(report['sha256']) == 64
        assert len((tmp_path / 'frontier.jsonl').read_text().splitlines()) == 2048


    def test_bundle_contains_expected_outputs(tmp_path) -> None:
        manifest = compile_project_bundle(build_eighth_fire_r1(), tmp_path)
        expected = {
            'anime-ir.json','characters.jsonl','scenes.jsonl','shots.jsonl',
            'causal-debts.jsonl','assets.jsonl','nodes.jsonl','edges.jsonl',
            'matrix-8192.jsonl','matrix-summary.json','shot-frontier.jsonl',
            'frontier-report.json','manifest.json','report.md',
        }
        assert {path.name for path in tmp_path.iterdir()} == expected
        assert manifest['matrix_cell_count'] == 8192
        assert manifest['shot_count'] == 30
        assert len(manifest['manifest_sha256']) == 64


    def test_bundle_is_deterministic(tmp_path) -> None:
        first = compile_project_bundle(build_eighth_fire_r1(), tmp_path / 'first', frontier_work_items=128)
        second = compile_project_bundle(build_eighth_fire_r1(), tmp_path / 'second', frontier_work_items=128)
        assert first == second
        for name in first['files']:
            assert (tmp_path / 'first' / name).read_bytes() == (tmp_path / 'second' / name).read_bytes()


    def test_payload_is_json_serializable() -> None:
        encoded = json.dumps(build_eighth_fire_r1().to_dict(), ensure_ascii=False, sort_keys=True)
        assert 'Le Huitième Feu' in encoded
        assert 'FORMALIZED' in encoded


    @pytest.mark.parametrize('work_items', [1, 17, 257, 2048])
    def test_frontier_respects_finite_experiment_request(tmp_path, work_items: int) -> None:
        report = compile_frontier_sample(
            tmp_path / f'{work_items}.jsonl', ('S01',), work_items,
            FrontierBudget(memory_bytes=50_000_000, wall_time_s=10, output_bytes=50_000_000),
        )
        assert report['written'] == work_items
        assert report['finite_experiment_work_items'] == work_items


    def test_project_rejects_duration_drift() -> None:
        project = build_eighth_fire_r1()
        scenes = list(project.scenes)
        scenes[0] = replace(scenes[0], duration_target_s=31)
        errors = replace(project, scenes=tuple(scenes)).validate()
        assert any('project.duration' in error for error in errors)


    def test_project_rejects_equal_information_states() -> None:
        project = build_eighth_fire_r1()
        scene = project.scenes[0]
        scenes = (replace(scene, audience_after=scene.audience_before),) + project.scenes[1:]
        errors = replace(project, scenes=scenes).validate()
        assert any('information state must change' in error for error in errors)


    def test_no_orphan_graph_nodes_in_canonical_seed() -> None:
        project = build_eighth_fire_r1()
        graph = AnimeGraph()
        graph.extend_nodes(project.nodes)
        graph.extend_edges(project.edges)
        assert graph.validate() == []
        # LOC-LAB is intentionally a world node not yet linked by R1 edges.
        assert set(graph.orphan_nodes()) <= {'LOC-LAB'}
''').lstrip()

files['docs/omega_anime_studio_t_r1.md'] = dedent('''
    # Ω-ANIME-STUDIO-T∞ R1

    ## Tristan Animation Operating System

    **Status:** OAK-safe software architecture and deterministic preproduction prototype.

    R1 expands the earlier Ω-ANIME-T∞ kernel into a structured studio operating system.
    It does not claim to replace artists, prove artistic quality, guarantee an audience,
    clear intellectual property automatically or turn narrative metaphors into physics.

    ## Core result

    The implementation provides:

    - Anime-IR typed models;
    - a 16-domain × 16-module × 32-artifact matrix;
    - 8,192 deterministic productive cells;
    - a world/narrative/production hypergraph;
    - five timed scenes and thirty shots for *Le Huitième Feu*;
    - explicit causal-debt objects;
    - asset provenance and production states;
    - a no-permanent-cap adaptive frontier controller;
    - deterministic JSON/JSONL evidence bundles;
    - schemas, policies, tests and CI proof gates.

    ## Matrix

    The matrix contains sixteen domains:

    1. IP, vision and identity;
    2. world and causality;
    3. characters;
    4. narrative;
    5. dialogue and language;
    6. visual design;
    7. motion and animation;
    8. camera and editing;
    9. audio, voice and music;
    10. physics, powers and technology;
    11. production;
    12. OAK and memory;
    13. audience experiments;
    14. localization and accessibility;
    15. transmedia and economy;
    16. automation and GitHub.

    Each domain contains sixteen modules.  Each module is crossed with thirty-two
    artifact kinds such as schema, engine, validator, test, benchmark, policy,
    provenance record, M⁻ rule, checkpoint and release gate.

    ```text
    16 × 16 × 32 = 8,192 cells
    ```

    A cell is a planned productive unit, not a claim that the module is implemented.
    Every cell records proof required and primary risk.

    ## No permanent total cap

    R1 does not define `MAX_TOTAL_SCENES`, `MAX_TOTAL_SHOTS` or `MAX_TOTAL_OBJECTS`.
    Individual executions remain finite and bounded by explicit memory, output,
    wall-time, quality, duplicate and safety budgets.

    Saturation produces a decision and memory:

    - `EXPAND`;
    - `HOLD`;
    - `RESHARD`;
    - `COMPRESS`;
    - `REGENERATE`;
    - `REDESIGN`;
    - `STOP-SAFELY`.

    Removing arbitrary total ceilings does not remove physical constraints, provider
    quotas, legal constraints, quality gates, budgets or human sovereignty.

    ## Anime-IR

    `AnimeProjectR1` connects:

    - world rules;
    - visual invariants;
    - characters;
    - scenes;
    - shots;
    - causal debts;
    - assets;
    - graph nodes and hyperedges;
    - OAK status;
    - risks and next actions.

    Every scene changes the audience information state and contains a conflict plus an
    irreversible change. Every shot carries duration, purpose, framing, camera motion,
    subjects, continuity, assets and estimated cost.

    ## Le Huitième Feu R1

    The canonical pilot remains 180 seconds but is now decomposed into:

    - five scenes;
    - thirty contiguous shots;
    - two character tensors;
    - one explicit causal debt;
    - eleven private-draft assets;
    - a project/episode/scene/character/system graph.

    The Huitième Feu reveals or reconfigures relations. It does not create matter or
    energy. A successful local intervention can displace a constraint, creating a debt
    that later becomes plot, responsibility, experiment or adversarial manipulation.

    ## Frontier generation

    The deterministic scene frontier combines:

    - eight objectives;
    - eight conflicts;
    - eight revelations;
    - eight costs;
    - eight staging strategies.

    This gives 32,768 candidates per scene before cross-scene campaigns. The checked-in
    dataset is a finite 2,048-line evidence sample; larger campaigns are regenerated by
    CLI instead of committing every temporary candidate.

    The quality score is a deterministic routing heuristic. It is not an artistic truth,
    an audience probability or a commercial forecast.

    ## CLI

    ```bash
    python -m omega_anime_studio_t matrix-summary
    python -m omega_anime_studio_t write-matrix --output /tmp/matrix.jsonl
    python -m omega_anime_studio_t validate-demo
    python -m omega_anime_studio_t compile-demo \\
      --output-dir generated/omega_anime_studio_t/eighth_fire_r1 \\
      --frontier-work-items 2048
    python -m omega_anime_studio_t frontier \\
      --output /tmp/frontier.jsonl \\
      --work-items 100000
    ```

    `--work-items` is the finite size of one experiment. It is not a permanent
    architectural ceiling.

    ## Bundle

    ```text
    anime-ir.json
    characters.jsonl
    scenes.jsonl
    shots.jsonl
    causal-debts.jsonl
    assets.jsonl
    nodes.jsonl
    edges.jsonl
    matrix-8192.jsonl
    matrix-summary.json
    shot-frontier.jsonl
    frontier-report.json
    manifest.json
    report.md
    ```

    ## OAK boundaries

    Internal validation proves only that the structured artifact satisfies declared
    constraints. It does not prove:

    - that the anime is emotionally effective;
    - that a public will watch it;
    - that an asset is legally cleared;
    - that a fictional power is physically real;
    - that production cost estimates are accurate;
    - that the work is commercially viable.

    Human approval remains mandatory for publication, protected-branch merge,
    commercial licenses, voice or likeness use, legal filings and irreversible deletion.

    ## Next promotion

    R1 remains `FORMALIZED`. Promotion to `SIMULATED` requires a timed storyboard or
    animatic, measured durations and a continuity review. The primary artifact remains
    one watchable 180-second pilot rather than opening multiple unfinished series.
''').lstrip()

files['.github/workflows/omega-anime-studio-r1.yml'] = dedent('''
    name: Omega Anime Studio R1

    on:
      pull_request:
        paths:
          - "omega_anime_studio_t/**"
          - "tests/test_omega_anime_studio_t_r1.py"
          - "schemas/anime-ir-r1.schema.json"
          - "policies/omega_anime_studio_r1.json"
          - "docs/omega_anime_studio_t_r1.md"
          - "examples/omega_anime_studio_r1_demo.py"
          - "generated/omega_anime_studio_t/**"
          - ".github/workflows/omega-anime-studio-r1.yml"
      workflow_dispatch:

    permissions:
      contents: read

    concurrency:
      group: omega-anime-studio-r1-${{ github.event.pull_request.number || github.ref }}
      cancel-in-progress: true

    jobs:
      anime-studio-oakbench:
        runs-on: ubuntu-24.04
        timeout-minutes: 15
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@v5
            with:
              python-version: "3.11"
          - name: Install validation dependencies
            run: python -m pip install --upgrade pip pytest jsonschema
          - name: Compile
            run: |
              python -m compileall omega_anime_studio_t tests/test_omega_anime_studio_t_r1.py examples/omega_anime_studio_r1_demo.py
          - name: Run targeted tests
            run: |
              pytest -q tests/test_omega_anime_studio_t_r1.py --durations=20 \\
                2>&1 | tee /tmp/omega-anime-studio-r1-tests.log
          - name: Validate Anime-IR schema
            run: |
              python - <<'PY'
              import json
              from pathlib import Path
              from jsonschema import Draft202012Validator
              from omega_anime_studio_t import build_eighth_fire_r1
              schema = json.loads(Path('schemas/anime-ir-r1.schema.json').read_text())
              payload = build_eighth_fire_r1().to_dict()
              Draft202012Validator(schema).validate(payload)
              print(json.dumps({'scenes':len(payload['scenes']),'shots':len(payload['shots'])}, indent=2))
              PY
          - name: Compile deterministic R1 evidence
            run: |
              python -m omega_anime_studio_t validate-demo
              python -m omega_anime_studio_t compile-demo \\
                --output-dir /tmp/omega-anime-studio-r1 \\
                --frontier-work-items 2048 \\
                | tee /tmp/omega-anime-studio-manifest.stdout.json
              PYTHONPATH=. python examples/omega_anime_studio_r1_demo.py
          - name: Enforce proof gates
            run: |
              python - <<'PY'
              import hashlib, json
              from pathlib import Path
              root = Path('/tmp/omega-anime-studio-r1')
              manifest = json.loads((root/'manifest.json').read_text())
              matrix = (root/'matrix-8192.jsonl').read_text().splitlines()
              frontier = (root/'shot-frontier.jsonl').read_text().splitlines()
              anime = json.loads((root/'anime-ir.json').read_text())
              assert manifest['matrix_cell_count'] == 8192
              assert len(matrix) == 8192
              assert len(frontier) == 2048
              assert manifest['shot_count'] == 30
              assert len(anime['scenes']) == 5
              assert sum(s['duration_target_s'] for s in anime['scenes']) == 180
              assert all(c['limitation'] and c['moral_boundary'] for c in anime['characters'])
              assert all(a['provenance']['private'] for a in anime['assets'])
              assert len(manifest['manifest_sha256']) == 64
              checked = Path('generated/omega_anime_studio_t/matrix-8192.jsonl')
              assert checked.exists() and len(checked.read_text().splitlines()) == 8192
              expected = hashlib.sha256(checked.read_bytes()).hexdigest()
              recorded = json.loads(Path('generated/omega_anime_studio_t/generated-manifest.json').read_text())
              assert recorded['matrix_sha256'] == expected
              print(json.dumps({'manifest':manifest['manifest_sha256'],'matrix':expected}, indent=2))
              PY
          - name: Preserve evidence
            if: always()
            uses: actions/upload-artifact@v4
            with:
              name: omega-anime-studio-r1
              path: |
                /tmp/omega-anime-studio-r1-tests.log
                /tmp/omega-anime-studio-manifest.stdout.json
                /tmp/omega-anime-studio-r1/manifest.json
                /tmp/omega-anime-studio-r1/matrix-summary.json
                /tmp/omega-anime-studio-r1/frontier-report.json
                /tmp/omega-anime-studio-r1/report.md
              retention-days: 14
''').lstrip()

# Generate checked-in deterministic datasets.
from importlib.util import spec_from_file_location, module_from_spec

for path, content in files.items():
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')

# Import generated package modules through normal path.
import sys
sys.path.insert(0, str(ROOT))
from omega_anime_studio_t.matrix import write_matrix_jsonl
from omega_anime_studio_t.frontier import FrontierBudget, compile_frontier_sample

matrix_path = ROOT / 'generated/omega_anime_studio_t/matrix-8192.jsonl'
matrix_report = write_matrix_jsonl(matrix_path)
frontier_path = ROOT / 'generated/omega_anime_studio_t/eighth-fire-shot-frontier-2048.jsonl'
frontier_report = compile_frontier_sample(
    frontier_path,
    ('S01-NOISE','S02-NETWORK','S03-CORRECTION','S04-DISPLACEMENT','S05-EIGHTH-FIRE'),
    2048,
    FrontierBudget(memory_bytes=32*1024*1024, wall_time_s=60, output_bytes=64*1024*1024),
)
manifest = {
    'generator_version':'omega-anime-studio/r1',
    'matrix_lines':8192,
    'matrix_sha256':hashlib.sha256(matrix_path.read_bytes()).hexdigest(),
    'frontier_lines':2048,
    'frontier_sha256':hashlib.sha256(frontier_path.read_bytes()).hexdigest(),
    'no_permanent_total_cap':True,
    'matrix_report':matrix_report,
    'frontier_report':frontier_report,
}
(ROOT/'generated/omega_anime_studio_t/generated-manifest.json').write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)+'\n', encoding='utf-8'
)

# Source inventory: only artifacts produced by this generator.
inventory = []
inventory_candidates = [ROOT / rel for rel in sorted(files)] + [
    matrix_path,
    frontier_path,
    ROOT / 'generated/omega_anime_studio_t/generated-manifest.json',
]
seen = set()
for path in inventory_candidates:
    resolved = path.resolve()
    if resolved in seen or not path.is_file():
        continue
    seen.add(resolved)
    rel = path.relative_to(ROOT)
    data = path.read_bytes()
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        continue
    inventory.append({
        'path': str(rel),
        'lines': len(text.splitlines()),
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
    })
inv_path = ROOT / 'generated/omega_anime_studio_t/source-inventory.json'
inv_path.write_text(json.dumps(inventory, indent=2) + '\n', encoding='utf-8')
print(json.dumps({
    'files': len(inventory),
    'lines': sum(item['lines'] for item in inventory),
    'bytes': sum(item['bytes'] for item in inventory),
}, indent=2))
