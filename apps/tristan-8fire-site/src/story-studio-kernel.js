"use strict";

export const STORY_CONSTITUTION = Object.freeze([
  "Generated != Verified",
  "Generated != Canon",
  "Generator != Judge",
  "AudienceModel != Audience",
  "Simulation != Reality",
  "Popularity != Quality",
  "Style != Identity",
  "SameCanon != SamePresentation",
  "MoreMeta != Better",
  "MoreContent != MoreValue"
]);

const C = (id, title, layer, status, purpose) => Object.freeze({ id, title, layer, status, purpose });

export const STORY_CAPABILITIES = Object.freeze([
  C("storyworld", "StoryWorld", "world", "core", "Monde causal exécutable dont les œuvres sont des projections."),
  C("story-ir", "Universal StoryIR", "world", "core", "IR commune pour entités, règles, causalité, narration et présentation."),
  C("manga-genome", "MangaGenome", "world", "core", "Génome source unifié pour monde, personnages, lore, arcs, visuel, son et contraintes."),
  C("world-genome", "WorldGenome", "world", "core", "Règles, géographie, histoire, sociétés, ressources et possibilités du monde."),
  C("character-genome", "CharacterGenome", "character", "core", "Identité, buts, peurs, mémoire, relations, voix, capacités et arc."),
  C("character-state", "Character StateTimeline", "character", "core", "État physique, émotionnel, connaissance, inventaire, relations et objectifs dans le temps."),
  C("identity-manifold", "Character Identity Manifold", "character", "experimental", "Préserve l'identité visuelle sous angle, âge, expression, lumière, mouvement et stylisation."),
  C("agency-test", "Character Agency Test", "character", "core", "Mesure l'écart entre action scénarisée et action plausible selon l'état interne du personnage."),
  C("dialogue-fingerprint", "Dialogue Fingerprints", "character", "core", "Différencie vocabulaire, syntaxe, rythme, humour, politesse, métaphores et silences."),
  C("subtext", "Subtext Engine", "character", "experimental", "Sépare texte parlé et intention afin de générer des dialogues multi-couches."),
  C("emotion-space", "Emotional State Space", "character", "experimental", "Fait évoluer confiance, amour, peur, ressentiment, admiration, dépendance et loyauté."),
  C("world-simulator", "World Causal Simulator", "simulation", "experimental", "Fait évoluer factions, villes, organisations et agents hors écran."),
  C("narrative-physics", "Narrative Physics Engine", "simulation", "experimental", "Suit tension, émotion, information, mystère, conflit, attachement et nouveauté comme signaux."),
  C("conservation-ledger", "Narrative Conservation Ledger", "simulation", "core", "Suit promesses, paiements, connaissances, blessures, objets, pouvoirs, causes et conséquences."),
  C("causal-graph", "Causal Story Graph", "simulation", "core", "Exige un support causal explicite pour les événements majeurs et suit la dette de coïncidence."),
  C("counterfactual", "Counterfactual Story Engine", "simulation", "experimental", "Explore des décisions alternatives et compare valeur narrative, complexité et contrivance."),
  C("negative-space", "Negative Space Storytelling", "simulation", "experimental", "Conserve les possibilités implicites non montrées sans gonfler l'exposition."),
  C("mystery-info", "Mystery Information Theory", "simulation", "experimental", "Gère l'incertitude du lecteur et la valeur informationnelle des indices."),
  C("power-system", "Power-System Compiler", "simulation", "core", "Définit source, transformation, contraintes, coûts, contres, échecs et limites des pouvoirs."),
  C("combat", "Combat Compiler", "simulation", "core", "Planifie positions, ressources, information, objectifs, actions, contres, adaptations et conséquences."),
  C("story-compiler", "StoryCompiler-T", "narrative", "core", "Compile thème, conflit, personnages, monde, arcs, scènes, beats, plans et panels."),
  C("foreshadow", "ForeshadowingCompiler-T", "narrative", "experimental", "Distribue des indices pour optimiser surprise et cohérence rétrospective."),
  C("residual-field", "Narrative Residual Field", "narrative", "core", "Cartographie promesses impayées, incohérences, redondances, tension faible et lore inutilisé."),
  C("story-tournament", "Story Tournament", "narrative", "core", "Fait concourir plusieurs variantes sous juges indépendants."),
  C("trope-genome", "Trope Genome", "narrative", "experimental", "Traite les tropes comme primitives mutables plutôt que comme éléments à éliminer."),
  C("originality-parallax", "Originality Parallax", "narrative", "experimental", "Évalue la nouveauté comme vecteur plot/personnage/visuel/monde/dialogue/mécanique."),
  C("eigenpaths", "Narrative Eigenpaths", "narrative", "experimental", "Recherche des trajectoires robustes sous critères et perturbations multiples."),
  C("manga-compiler", "MangaCompiler-T", "production", "core", "Compile scènes en beats, panels, composition, décors, dialogue et lettering."),
  C("anime-compiler", "AnimeCompiler-T", "production", "core", "Compile scènes en storyboard, plans, keyframes, mouvement, lumière, voix, son et montage."),
  C("shot-genome", "ShotGenome-T", "production", "core", "Formalise caméra, durée, mouvement, acting, lumière, dialogue, son et dépendances."),
  C("visual-dna", "VisualDNA-T", "production", "core", "Génère une grammaire visuelle originale à partir de primitives abstraites."),
  C("cinematic-grammar", "Cinematic Grammar Compiler", "production", "core", "Choisit plans et mouvements de caméra selon intention, émotion, géométrie et continuité."),
  C("camera-causality", "Camera Causality", "production", "experimental", "Exige une raison narrative mesurable pour chaque changement de caméra."),
  C("animation-budget", "Animation Budget Compiler", "production", "core", "Alloue temps, artistes, frames et compute selon valeur narrative et coût."),
  C("sakuga", "Sakuga Allocation Engine", "production", "experimental", "Concentre l'animation supplémentaire sur les scènes au meilleur gain marginal."),
  C("perceptual-animation", "Perceptual Animation Compiler", "production", "experimental", "Optimise perception du mouvement plutôt que FPS brut."),
  C("multires", "Multi-resolution Production", "production", "core", "Valide text → thumbnail → storyboard → animatic → layout → key animation → final."),
  C("proof-scene", "Proof-Carrying Scene", "production", "core", "Attache but, causes, états, promesses, contradictions, coût, alternatives et provenance à chaque scène."),
  C("consistency", "Consistency Engine", "production", "core", "Détecte faux raccords, chronologie impossible, vêtements, objets, pouvoirs et décors incohérents."),
  C("audience-mirrors", "Audience Mirrors", "validation", "experimental", "Utilise plusieurs lecteurs virtuels comme sondes divergentes, jamais comme public réel."),
  C("roundtrip", "Manga ↔ Anime Round Trip", "validation", "experimental", "Mesure le résidu d'adaptation entre médias."),
  C("story-renorm", "Story Renormalization Group", "validation", "experimental", "Compresse l'œuvre en préservant thème, causalité, motivations et moments critiques."),
  C("proof-franchise", "Regenerative Franchise", "validation", "experimental", "Teste la reconstruction d'œuvres et d'assets depuis un noyau compact."),
  C("canon-ledger", "Canon Ledger", "canon", "core", "Versionne DRAFT, POSSIBLE, CANON, RETCON, DEPRECATED et CONTRADICTED avec provenance."),
  C("retcon", "Retcon Compiler", "canon", "core", "Calcule l'impact d'un changement canonique et propose le retcon cohérent minimal."),
  C("narrative-git", "Narrative Git", "canon", "core", "Branches, diffs, reviews, merges et reverts pour arcs, fins, spin-offs et adaptations."),
  C("cross-media", "Shared Cross-Media Canon", "canon", "core", "Maintient un CanonGraph unique pour manga, anime, jeu, roman, web et wiki."),
  C("cross-media-invariant", "Cross-Media Invariant Compiler", "canon", "core", "Définit ce qui doit survivre à toutes les adaptations sans imposer la même présentation."),
  C("lazy-story-graph", "Infinite Story Graph / Lazy Expansion", "canon", "core", "Matérialise seulement les bifurcations à fort gain narratif attendu."),
  C("book0", "Manga/Story BOOK0", "canon", "core", "Noyau compact de lois, grammaires, genomes, timeline, invariants, tests et recettes."),
  C("provenance", "IP / Provenance Firewall", "rights", "core", "Distingue créations originales, références autorisées, licences, domaine public, génération et contributions humaines."),
  C("voice", "VoiceGenome", "rights", "core", "Décrit voix originales/autorisées sans usurpation implicite de personnes réelles."),
  C("music", "MusicGenome-T", "audio", "experimental", "Formalise thèmes, motifs, harmonie, rythme, instrumentation, émotion et liens personnages."),
  C("leitmotif", "Leitmotif Evolution", "audio", "experimental", "Transforme un motif musical au fil d'un arc narratif."),
  C("anti-generator", "Anti-Generator", "validation", "core", "Cherche ce qu'il faut retirer et mesure la valeur après ablation."),
  C("complexity-debt", "Complexity Debt", "validation", "core", "Rend explicite le coût futur des personnages, pouvoirs, lore et intrigues ajoutés."),
  C("story-compression", "Story Compression Ratio", "validation", "experimental", "Signal de contrôle valeur narrative/émotionnelle/mondiale par complexité."),
  C("audience-causal", "Audience Causal Lab", "validation", "experimental", "Sépare métriques d'audience et causes réelles via tests contrôlés quand disponibles."),
  C("anti-clickbait", "Anti-clickbait Constitution", "validation", "core", "Garde valeur long terme et confiance du public distinctes de watch time et cliffhangers."),
  C("reality-anchor", "Production Reality Anchor", "validation", "core", "Croise narration, visuel, continuité, production et droits avant promotion."),
  C("studio-twin", "Studio Digital Twin", "studio", "experimental", "Simule artistes, compute, budget, calendrier, assets, dépendances et chemin critique."),
  C("jit-studio", "JIT Virtual Studio", "studio", "core", "Compile une coalition d'agents adaptée à la tâche puis mesure les contributions par ablation."),
  C("fractal-studio", "Fractal Studio", "studio", "experimental", "Répète Generate → Verify → Compress → Crystallize de la franchise jusqu'au frame."),
  C("mycelial-assets", "Mycelial Story Asset Network", "studio", "core", "Réutilise et propage les assets via graphe de dépendances entre médias."),
  C("failure-genome", "Failure Genome", "studio", "core", "Convertit une erreur en contexte, cause, détection, correction, prévention et règle réutilisable."),
  C("immune-system", "Studio Immune System", "studio", "core", "Détecte dérive graphique, plagiat accidentel, répétition, incohérence, métriques manipulées et coûts incontrôlés."),
  C("self-crystal", "Self-crystallizing Studio", "studio", "experimental", "Promote les workflows stables en EigenMacros réutilisables."),
  C("dsl", "GO Story DSL", "studio", "core", "Expose GO WORLD/CHARACTER/ARC/EPISODE/FIGHT/OAK/CANON/REGENERATE/FRANCHISE/MAX."),
  C("storylife", "Ω-STORYLIFE", "studio", "experimental", "Traite manga, anime, jeu et roman comme projections d'un même univers causal exécutable."),
  C("meta-generalize", "Meta-Generalization", "meta", "core", "Fait de manga/anime des backends d'un GenerativeStoryArtifact commun."),
  C("generator-abi", "MetaGenerator Registry / ABI", "meta", "core", "Normalise plan, generate, verify, repair, compress et regenerate pour tous les générateurs."),
  C("generator-of-generators", "Generator-of-Generators", "meta", "experimental", "Synthétise de nouveaux générateurs à partir de résidus récurrents, puis les benchmarke."),
  C("meta-residual", "Meta-Residual Engine", "meta", "core", "Sépare erreurs d'artefact, générateur, architecture et processus d'amélioration."),
  C("automation-compiler", "AutomationCompiler-T", "meta", "core", "Détecte les workflows répétitifs à automatiser selon travail futur éliminé, fiabilité, coût et risque."),
  C("meta-agents", "Meta-Automation of Agents", "meta", "core", "Ablate les agents inutiles et cristallise les coalitions stables."),
  C("meta-agent-generator", "Meta-Agent Generator", "meta", "experimental", "Propose de nouveaux rôles formels quand un résidu ne correspond à aucun agent existant."),
  C("meta-regeneration", "Meta-Regeneration R0-R5", "meta", "core", "Reconstruit artifact, œuvre, univers, studio, architecture puis écosystème depuis BOOK0_MIN."),
  C("regen-closure", "Regeneration Closure", "meta", "core", "Mesure la fraction de capacités attendues réellement récupérées après régénération."),
  C("meta-book0", "STORY-BOOK0-MIN", "meta", "core", "Conserve schéma StoryIR, ABI, canon, OAK, rights, recettes, benchmarks et Failure Genomes."),
  C("improvement-object", "Improvement Object", "meta", "core", "Encode cible, hypothèse, changement, gain attendu, coût, risque et test."),
  C("improvement-tournament", "Improvement Tournament", "meta", "core", "Compare plusieurs améliorations sur gain vérifié par complexité, coût et dette."),
  C("meta-improvement", "Improvement-of-Improvement", "meta", "experimental", "Apprend quelles stratégies d'amélioration fonctionnent selon le type de résidu."),
  C("credit-assignment", "Causal Credit Assignment", "meta", "core", "Ablations, A/B, seeds et benchmarks gelés limitent les promotions par corrélation trompeuse."),
  C("meta-crystal", "Meta-Crystallization", "meta", "core", "Transforme expérience → pattern → primitive → crystal avec preuves et rollback."),
  C("eigen-primitives", "EigenPrimitive Discovery", "meta", "experimental", "Recherche les opérations qui survivent à de nombreux genres et workflows."),
  C("studio-renorm", "Studio Renormalization", "meta", "experimental", "Compresse beaucoup de modules vers peu de primitives sans perdre les capacités utiles."),
  C("capability-closure", "Capability Closure", "meta", "experimental", "Cherche le noyau minimal dont la fermeture régénère presque toutes les capacités."),
  C("emergent-capability", "Emergent Capability Detector", "meta", "experimental", "Détecte les capacités non factorisables qui émergent d'une composition."),
  C("synergy", "Synergy Compiler", "meta", "core", "Promote une composition seulement si le gain combiné dépasse les gains séparés."),
  C("fission", "FISSION / Anti-Synergy", "meta", "core", "Sépare les modules lorsque la spécialisation améliore performance et maintenabilité."),
  C("repr-tournament", "Representation Tournament", "meta", "core", "Compare texte, graphe, tenseur, timeline, simulation et système de contraintes."),
  C("repr-generator", "Representation Generator", "meta", "experimental", "Invente de nouvelles représentations intermédiaires puis teste leur utilité."),
  C("parallax", "Multi-representation Parallax", "meta", "core", "L'accord entre représentations renforce l'évidence; le désaccord crée un résidu prioritaire."),
  C("meta-oak", "Meta-OAK", "governance", "core", "Sépare Generator, Judge et JudgeDesigner; les changements de juge exigent une ancre externe."),
  C("frozen-anchor", "Frozen Reality Anchors", "governance", "core", "Gèle les benchmarks pendant un cycle d'évolution pour empêcher l'auto-notation opportuniste."),
  C("adversarial-meta", "Adversarial Meta-Evolution", "governance", "experimental", "Coévolution contrôlée entre générateurs et falsificateurs."),
  C("unknown-unknown", "Unknown-Unknown Generator", "governance", "experimental", "Cherche ce que le système n'est même pas encore capable de mesurer."),
  C("apoptosis", "Meta-Apoptosis", "governance", "core", "Détruit les modules dont l'utilité vérifiée tombe sous leur coût de maintenance."),
  C("forget-plus", "Forget+", "governance", "core", "Archive hors chemin actif sans supprimer les receipts historiques."),
  C("temporal-evolution", "Temporal Capability Evolution", "governance", "experimental", "Suit valeur, vieillissement et émergence des capacités dans le temps."),
  C("pareto", "Multi-objective Pareto Evolution", "governance", "core", "Optimise Story, Emotion, Originality, Continuity, Production, Rights, Trust et Cost sans score magique unique."),
  C("narrative-civilization", "Narrative Civilization", "ecosystem", "experimental", "Écosystème logiciel de générateurs, univers, critiques, archives, outils et variantes expérimentales."),
  C("story-university", "Virtual Story University", "ecosystem", "experimental", "Labs worldbuilding, character, animation, narrative science, cinematography, music et production engineering."),
  C("meta-franchise", "Meta-Franchise Genome", "ecosystem", "experimental", "Génère histoires principales, spin-offs, jeux, films, shorts, produits et mondes interactifs sous canon commun."),
  C("world-of-worlds", "World-of-Worlds", "ecosystem", "experimental", "Partage les capacités entre univers sans fusionner leurs canons."),
  C("studio-genome", "StudioGenome", "ecosystem", "experimental", "Encode générateurs, juges, workflow, représentations, stratégie de production et politiques de risque."),
  C("studio-darwinism", "Controlled Studio Darwinism", "ecosystem", "experimental", "Mutation, production, benchmark et sélection tout en conservant la diversité."),
  C("crystal-hierarchy", "Meta-Crystal Hierarchy", "ecosystem", "core", "Hiérarchise workflows, générateurs, coalitions, architectures et noyaux de régénération."),
  C("proof-crystal", "Proof-Carrying Crystal", "ecosystem", "core", "Un Crystal contient capacité, implémentation, preuves, benchmarks, dépendances, échecs, limites et rollback."),
  C("crystal-code", "Crystal-to-Code", "ecosystem", "core", "Compile concept → spec → schema → code → tests → benchmark → package."),
  C("crystal-compiler", "Meta-Crystallization Compiler", "ecosystem", "core", "Décide PROMOTE, KEEP_EXPERIMENTAL, MERGE, SPLIT, DEPRECATE ou DESTROY."),
  C("crystal-forest", "Regenerative Crystal Forest", "ecosystem", "experimental", "Réseau substituable et testable de capacités régénératives."),
  C("omnistory", "Ω-OMNISTORY-T∞Ω", "ecosystem", "core", "Foundry universelle qui génère, falsifie, cristallise et régénère StoryWorlds, médias et studios.")
]);

export const STORY_COMMANDS = Object.freeze([
  "GO MANGA ALL MAX", "GO WORLD MAX", "GO CHARACTER MAX", "GO ARC MAX", "GO CHAPTER MAX", "GO EPISODE MAX",
  "GO FIGHT MAX", "GO ROMANCE MAX", "GO MYSTERY MAX", "GO STORYBOARD MAX", "GO ANIMATION MAX", "GO OAK MAX",
  "GO ATTACK", "GO COMPRESS", "GO CANON", "GO RETCON", "GO REGENERATE", "GO FRANCHISE", "GO STORY META MAX",
  "META GENERALIZE", "META GENERATE", "META AUTOMATE", "META REGENERATE", "META IMPROVE", "META CRYSTALLIZE",
  "META ATTACK", "META ABLATE", "META COMPRESS", "META FISSION", "META MERGE", "META EVOLVE", "META PRUNE",
  "META FORGET", "META BENCHMARK"
]);

export const STORY_PIPELINE = Object.freeze([
  "INTENT", "STORYWORLD", "STORY IR", "SIMULATE", "BRANCH LAZILY", "TOURNAMENT", "MANGA / ANIME / GAME",
  "CONTINUITY", "OAK + RIGHTS", "CANON", "CRYSTALLIZE", "REGENERATE"
]);

function clamp01(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(1, n));
}

function normalizedText(value) {
  return String(value ?? "").trim();
}

export function queryCapabilities(query = "", layer = "all") {
  const q = normalizedText(query).toLocaleLowerCase("fr-CA");
  return STORY_CAPABILITIES.filter((capability) => {
    const matchesLayer = layer === "all" || capability.layer === layer;
    const haystack = `${capability.id} ${capability.title} ${capability.layer} ${capability.status} ${capability.purpose}`.toLocaleLowerCase("fr-CA");
    return matchesLayer && (!q || haystack.includes(q));
  });
}

export function compileStoryProgram({ intent, medium = "manga", genre = "hybrid", objective = "coherent-world" } = {}) {
  const cleanIntent = normalizedText(intent) || "Créer un StoryWorld original et falsifiable";
  const outputs = medium === "franchise" ? ["manga", "anime", "game", "novel", "website"] : [medium];
  return Object.freeze({
    id: `story-${cleanIntent.toLocaleLowerCase("fr-CA").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40) || "seed"}`,
    intent: cleanIntent,
    medium,
    genre,
    objective,
    storyIR: ["Universe", "Agents", "Rules", "Chronology", "CausalGraph", "Narrative", "Presentation"],
    pipeline: STORY_PIPELINE,
    outputs,
    invariants: STORY_CONSTITUTION,
    canonStatus: "DRAFT",
    publication: "HOLD"
  });
}

export function evaluateSceneEnvelope(scene = {}) {
  const continuity = clamp01(scene.continuity ?? 0);
  const causality = clamp01(scene.causality ?? 0);
  const rights = Boolean(scene.rightsCleared);
  const provenance = Boolean(scene.provenance);
  const independentReview = Boolean(scene.independentReview);
  const attemptsCanon = Boolean(scene.attemptsCanon);
  const generatedOnly = scene.verified !== true;
  const score = (continuity + causality + (rights ? 1 : 0) + (provenance ? 1 : 0) + (independentReview ? 1 : 0)) / 5;
  const blockers = [];
  if (continuity < 0.7) blockers.push("continuity");
  if (causality < 0.7) blockers.push("causality");
  if (!rights) blockers.push("rights");
  if (!provenance) blockers.push("provenance");
  if (!independentReview) blockers.push("independent-review");
  if (attemptsCanon && generatedOnly) blockers.push("generated-is-not-canon");
  return Object.freeze({ score, status: blockers.length ? "HOLD" : "PASS", blockers });
}

export function metaPromotionDecision({ verifiedGain = 0, complexity = 0, cost = 0, risk = 0, frozenBenchmark = false, independentJudge = false } = {}) {
  const burden = Math.max(0.001, Number(complexity) + Number(cost) + Number(risk));
  const ratio = Number(verifiedGain) / burden;
  const blockers = [];
  if (!(Number(verifiedGain) > 0)) blockers.push("no-positive-verified-gain");
  if (!frozenBenchmark) blockers.push("benchmark-not-frozen");
  if (!independentJudge) blockers.push("generator-equals-judge-risk");
  if (!(ratio > 0)) blockers.push("gain-does-not-beat-burden");
  return Object.freeze({ ratio, decision: blockers.length ? "PRUNE" : "PROMOTE", blockers });
}

export function regenerationClosure(expectedCapabilities = [], recoveredCapabilities = []) {
  const expected = new Set(expectedCapabilities);
  const recovered = new Set(recoveredCapabilities);
  if (!expected.size) return Object.freeze({ ratio: 1, missing: [] });
  const missing = [...expected].filter((item) => !recovered.has(item));
  return Object.freeze({ ratio: (expected.size - missing.length) / expected.size, missing });
}

export function automationValue({ futureWorkEliminated = 0, reliability = 0, implementationCost = 0, risk = 0 } = {}) {
  const denominator = Math.max(0.001, Number(implementationCost) + Number(risk));
  return (Math.max(0, Number(futureWorkEliminated)) * clamp01(reliability)) / denominator;
}
