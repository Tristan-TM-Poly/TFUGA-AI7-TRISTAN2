"use strict";

export const EVIDENCE_LEVELS = Object.freeze([
  ["HYPOTHESIS", 0.12, 0.10],
  ["FORMALIZATION", 0.24, 0.18],
  ["PROTOTYPE", 0.42, 0.30],
  ["MEASURED", 0.62, 0.50],
  ["REPLICATED", 0.82, 0.75],
  ["PROVEN", 1.00, 1.00]
]);

export const PUBLIC_MEDIA_CONSTITUTION = Object.freeze([
  "AI ≠ Editor",
  "Recommendation ≠ EditorialTruth",
  "Popularity ≠ PublicValue",
  "Simulation ≠ Fact",
  "Synthesis ≠ Reporting",
  "Confidence ≠ Evidence",
  "Personalization ≠ PoliticalManipulation",
  "LocalPASS ≠ GlobalPASS",
  "PropagationRate ≤ CorrectionCapacity",
  "MediaAmplification ≤ EvidenceMaturity",
  "HumanFinalAuthority = 1"
]);

export const COGNITIVE_MEDIA_ISA = Object.freeze([
  "SHOW", "QUESTION", "COMPARE", "ZOOM", "TRACE", "DERIVE",
  "PERTURB", "SIMULATE", "TEST", "VERIFY", "FALSIFY", "CONNECT", "REMEMBER"
]);

export const MEDIA_FORMS = Object.freeze([
  "15s", "60s", "3min", "8min", "20min", "article", "radio", "balado",
  "tv", "interactive", "animation", "dataset", "github", "education"
]);

export const PROPAGATION_WAVES = Object.freeze([
  { id: "W1", label: "Validation indépendante", minimum: "PROTOTYPE" },
  { id: "W2", label: "Communauté technique", minimum: "PROTOTYPE" },
  { id: "W3", label: "Éducation / média scientifique", minimum: "MEASURED" },
  { id: "W4", label: "Grand public", minimum: "REPLICATED" }
]);

const LEVEL_INDEX = new Map(EVIDENCE_LEVELS.map(([name], index) => [name, index]));
const LEVEL_WEIGHT = new Map(EVIDENCE_LEVELS.map(([name, evidence]) => [name, evidence]));
const AMPLIFICATION_CAP = new Map(EVIDENCE_LEVELS.map(([name, , cap]) => [name, cap]));

export const RADIO_CANADA_MRU = Object.freeze({
  id: "RC-MRU-001",
  title: "Radio-Canada Evidence Workspace",
  affiliation: "Concept indépendant — aucune affiliation ou approbation de Radio-Canada",
  question: "Comment transformer un dossier en compréhension vérifiable sans automatiser l'autorité éditoriale ?",
  status: "PROTOTYPE",
  operations: ["TRACE", "COMPARE", "TIMELINE", "VERIFY", "UNCERTAINTY", "SOURCE"],
  claims: [
    { id: "C1", label: "Les claims doivent être reliés à leur provenance.", status: "DESIGN_INVARIANT" },
    { id: "C2", label: "Une correction doit retrouver les dérivés dépendants.", status: "PROTOTYPE_TARGET" },
    { id: "C3", label: "La publication finale reste une décision humaine.", status: "HARD_GATE" }
  ],
  timeline: [
    ["T0", "Question"],
    ["T1", "Claims + sources"],
    ["T2", "OAK / red team"],
    ["T3", "Représentations"],
    ["T4", "Revue éditoriale humaine"]
  ],
  unknowns: [
    "Gain réel de compréhension auprès de lecteurs",
    "Temps net économisé ou ajouté pour les journalistes",
    "Qualité des liens d'archives sur un corpus réel",
    "Calibration des seuils de diffusion"
  ]
});

function clamp(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return 0;
  return Math.max(0, Math.min(1, number));
}

function safeLevel(level) {
  return LEVEL_INDEX.has(level) ? level : "HYPOTHESIS";
}

export function stableMediaId(seed) {
  const text = JSON.stringify(seed, Object.keys(seed).sort());
  let hash = 2166136261;
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return `BKO-${(hash >>> 0).toString(16).padStart(8, "0")}`;
}

export function mediaReadiness(asset = {}) {
  const evidenceLevel = safeLevel(asset.evidenceLevel);
  const evidence = LEVEL_WEIGHT.get(evidenceLevel);
  const dimensions = {
    evidence,
    demonstrability: clamp(asset.demonstrability),
    visualPower: clamp(asset.visualPower),
    publicRelevance: clamp(asset.publicRelevance),
    clarity: clamp(asset.clarity),
    timeliness: clamp(asset.timeliness),
    reproducibility: clamp(asset.reproducibility),
    rightsReadiness: clamp(asset.rightsReadiness)
  };
  const weights = {
    evidence: 0.22,
    demonstrability: 0.14,
    visualPower: 0.10,
    publicRelevance: 0.16,
    clarity: 0.13,
    timeliness: 0.07,
    reproducibility: 0.12,
    rightsReadiness: 0.06
  };
  const score = Object.entries(dimensions).reduce((sum, [key, value]) => sum + value * weights[key], 0);
  return { evidenceLevel, score: Number(score.toFixed(4)), dimensions };
}

export function mediaOakGate(candidate = {}) {
  const required = [
    "question", "evidence", "limitations", "provenance", "rights", "correctionEndpoint", "humanEditorialReview"
  ];
  const passed = [];
  const failed = [];
  for (const key of required) (candidate[key] ? passed : failed).push(key);
  if (candidate.autoPublish) failed.push("auto_publish_forbidden");
  if (candidate.personalizePoliticalReality) failed.push("political_reality_personalization_forbidden");
  if (candidate.claimsProof && safeLevel(candidate.evidenceLevel) !== "PROVEN") failed.push("proof_claim_exceeds_evidence");
  const status = failed.length ? "HOLD" : "ELIGIBLE_FOR_EDITORIAL_REVIEW";
  return Object.freeze({ status, passed: [...new Set(passed)].sort(), failed: [...new Set(failed)].sort(), humanFinalAuthority: true });
}

export function amplificationDecision(asset = {}) {
  const readiness = mediaReadiness(asset);
  const cap = AMPLIFICATION_CAP.get(readiness.evidenceLevel);
  const correctionCapacity = clamp(asset.correctionCapacity ?? 0);
  const requestedReach = clamp(asset.requestedReach ?? 1);
  const safeReach = Math.min(cap, correctionCapacity);
  const allowedReach = Math.min(requestedReach, safeReach);
  return {
    evidenceLevel: readiness.evidenceLevel,
    readiness: readiness.score,
    amplificationCap: cap,
    correctionCapacity,
    requestedReach,
    allowedReach: Number(allowedReach.toFixed(4)),
    status: allowedReach + 1e-9 >= requestedReach ? "ALLOW_WITH_EDITORIAL_REVIEW" : "THROTTLE"
  };
}

export function propagationPlan(asset = {}) {
  const level = safeLevel(asset.evidenceLevel);
  const index = LEVEL_INDEX.get(level);
  return PROPAGATION_WAVES.map((wave) => ({
    ...wave,
    eligible: index >= LEVEL_INDEX.get(wave.minimum)
  }));
}

export function compileBroadcastableKnowledgeObject(input = {}) {
  const question = String(input.question || "").trim();
  const evidenceLevel = safeLevel(input.evidenceLevel);
  const invariants = {
    question: Boolean(question),
    evidence: Boolean(input.evidence),
    limitations: Boolean(input.limitations),
    provenance: Boolean(input.provenance),
    attribution: Boolean(input.attribution),
    correctionEndpoint: Boolean(input.correctionEndpoint)
  };
  const seed = { question, evidenceLevel, title: input.title || "Untitled" };
  const object = {
    id: stableMediaId(seed),
    title: String(input.title || "Untitled"),
    question,
    evidenceLevel,
    evidence: input.evidence || [],
    limitations: input.limitations || [],
    provenance: input.provenance || [],
    attribution: input.attribution || [],
    correctionEndpoint: input.correctionEndpoint || null,
    mediaGenome: MEDIA_FORMS.map((form) => ({ form, status: "CANDIDATE" })),
    invariants,
    automaticPublicationAllowed: false,
    humanEditorialReviewRequired: true
  };
  return Object.freeze(object);
}

export function semanticTranscode(bko, target) {
  const targetSeconds = typeof target === "number" ? target : Number.parseInt(String(target), 10) || 0;
  const missing = Object.entries(bko?.invariants || {}).filter(([, present]) => !present).map(([key]) => key);
  if (missing.length) return { status: "MEANING_LOSS", targetSeconds, missing };
  const requiredForShort = targetSeconds > 0 && targetSeconds <= 60 ? ["question", "evidence", "limitations"] : ["question", "evidence"];
  const shortMissing = requiredForShort.filter((key) => !bko.invariants[key]);
  return shortMissing.length
    ? { status: "MEANING_LOSS", targetSeconds, missing: shortMissing }
    : { status: "SAFE_COMPRESSION", targetSeconds, missing: [] };
}

export function publicMediaReceipt(asset = {}) {
  const readiness = mediaReadiness(asset);
  const amplification = amplificationDecision(asset);
  const plan = propagationPlan(asset);
  return Object.freeze({
    system: "Ω-VERIFIED-KNOWLEDGE-PROPAGATION-AND-REGENERATION-T",
    mru: RADIO_CANADA_MRU.id,
    readiness,
    amplification,
    eligibleWaves: plan.filter((item) => item.eligible).map((item) => item.id),
    automaticPublicationAllowed: false,
    humanFinalAuthority: true,
    claimBoundary: "Architecture/prototype: no affiliation, deployment, editorial approval, scientific proof, or measured public benefit is implied."
  });
}
