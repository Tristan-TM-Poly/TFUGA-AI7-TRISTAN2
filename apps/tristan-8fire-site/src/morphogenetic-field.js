"use strict";

export const RESIDUAL_TYPES = Object.freeze([
  "unknown",
  "uncertain",
  "contradicted",
  "untested",
  "unimplemented",
  "unmeasured",
  "unproved"
]);

const EVIDENCE_OPERATORS = new Map([
  ["GO PROVE", ["formal-proof-or-explicit-unproved-status"]],
  ["GO EXPERIMENT", ["experiment-spec", "measurement-boundary"]],
  ["GO SIMULATE", ["model-domain", "solver-provenance", "simulation-not-proof"]],
  ["GO FALSIFY", ["falsifier", "counterexample-search"]],
  ["GO OAK", ["evidence-ledger", "uncertainty", "counterevidence"]],
  ["GO GLOBALPASS", ["qualified-combined-tree", "exact-head-or-tree-identity"]]
]);

function finiteNumber(value, fallback = 0) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function normalizeLabel(value, fallback) {
  const label = String(value ?? "").trim();
  return label || fallback;
}

function freezeList(values = []) {
  return Object.freeze(Array.from(values, (value) => Object.freeze(value)));
}

export function operatorEvidenceObligations(operator) {
  return Object.freeze([...(EVIDENCE_OPERATORS.get(String(operator)) || [])]);
}

export function createTransformationField({
  families,
  operators,
  objectType = "theory",
  namespace = "tf"
} = {}) {
  if (!Array.isArray(families) || !families.length) throw new TypeError("families must be a non-empty array");
  if (!Array.isArray(operators) || !operators.length) throw new TypeError("operators must be a non-empty array");

  const cells = [];
  for (let familyIndex = 0; familyIndex < families.length; familyIndex += 1) {
    const family = families[familyIndex];
    const familyId = Array.isArray(family) ? normalizeLabel(family[0], `family-${familyIndex + 1}`) : normalizeLabel(family?.id, `family-${familyIndex + 1}`);
    const familyLabel = Array.isArray(family) ? normalizeLabel(family[1], familyId) : normalizeLabel(family?.label, familyId);

    for (let operatorIndex = 0; operatorIndex < operators.length; operatorIndex += 1) {
      const rawOperator = operators[operatorIndex];
      const operator = typeof rawOperator === "string" ? rawOperator : normalizeLabel(rawOperator?.label, `OP-${operatorIndex + 1}`);
      const ordinal = familyIndex * operators.length + operatorIndex + 1;
      cells.push(Object.freeze({
        id: `${namespace}-${String(ordinal).padStart(4, "0")}`,
        ordinal,
        familyId,
        familyLabel,
        operator,
        objectType,
        obligations: operatorEvidenceObligations(operator),
        lifecycle: operator === "GO ZERO" || operator === "GO OBSOLETE" ? "destruction-candidate" : "candidate"
      }));
    }
  }

  return Object.freeze({
    schema: "tristan.transformation-field/0.1",
    objectType,
    familyCount: families.length,
    operatorCount: operators.length,
    cellCount: cells.length,
    cells: Object.freeze(cells)
  });
}

export function createEpistemicCapsule({
  intent,
  objectType = "theory",
  claims = [],
  models = [],
  evidence = [],
  simulations = [],
  proofs = [],
  residuals = [],
  interactions = [],
  provenance = [],
  version = "0.1"
} = {}) {
  const normalizedIntent = normalizeLabel(intent, "unspecified-intent");
  return Object.freeze({
    schema: "tristan.epistemic-capsule/0.1",
    version: normalizeLabel(version, "0.1"),
    intent: normalizedIntent,
    objectType: normalizeLabel(objectType, "theory"),
    claims: freezeList(claims),
    models: freezeList(models),
    evidence: freezeList(evidence),
    simulations: freezeList(simulations),
    proofs: freezeList(proofs),
    residuals: freezeList(residuals),
    interactions: freezeList(interactions),
    provenance: freezeList(provenance),
    epistemicBoundary: "A capsule is a portable compilation envelope; its presence does not certify truth, proof, measurement, provenance quality, or external-world validity."
  });
}

export function deriveResidualField(capsule) {
  if (!capsule || capsule.schema !== "tristan.epistemic-capsule/0.1") throw new TypeError("capsule must be a tristan.epistemic-capsule/0.1 object");
  const residuals = [];

  if (!capsule.claims.length) residuals.push({ type: "unknown", reason: "no-explicit-claims" });
  if (!capsule.evidence.length) residuals.push({ type: "untested", reason: "no-evidence-linked" });
  if (!capsule.proofs.length) residuals.push({ type: "unproved", reason: "no-formal-proof-linked" });
  if (!capsule.simulations.length) residuals.push({ type: "unimplemented", reason: "no-executable-world-linked" });
  if (!capsule.provenance.length) residuals.push({ type: "uncertain", reason: "no-provenance-linked" });
  for (const residual of capsule.residuals) residuals.push({ type: normalizeLabel(residual?.type, "unknown"), reason: normalizeLabel(residual?.reason, "declared-residual") });

  return Object.freeze({
    schema: "tristan.residual-field/0.1",
    intent: capsule.intent,
    count: residuals.length,
    types: Object.freeze([...new Set(residuals.map((item) => item.type))]),
    residuals: freezeList(residuals)
  });
}

export function evaluateAntiAdd({
  novelCoverage = 0,
  reuseGain = 0,
  verifiedGain = 0,
  complexityDebt = 0,
  maintenanceDebt = 0,
  irreversibility = 0
} = {}) {
  const benefit = finiteNumber(novelCoverage) + finiteNumber(reuseGain) + finiteNumber(verifiedGain);
  const debt = finiteNumber(complexityDebt) + finiteNumber(maintenanceDebt) + finiteNumber(irreversibility);
  const net = benefit - debt;

  let decision = "HOLD";
  if (finiteNumber(novelCoverage) <= 0 && finiteNumber(reuseGain) > 0) decision = "REUSE";
  else if (net > 0 && finiteNumber(verifiedGain) > 0) decision = "CANDIDATE";
  else if (net < -1) decision = "DESTROY";

  return Object.freeze({
    schema: "tristan.anti-add-receipt/0.1",
    benefit,
    debt,
    net,
    decision,
    boundary: "CANDIDATE is permission to evaluate, not permission to deploy, publish, merge, or claim scientific validation."
  });
}

export function evaluateMetaDepth({ depth = 1, verifiedGain = 0, minGainPerDepth = 0.25 } = {}) {
  const normalizedDepth = Math.max(0, Math.floor(finiteNumber(depth, 0)));
  const threshold = Math.max(0, finiteNumber(minGainPerDepth, 0.25));
  const requiredGain = normalizedDepth * threshold;
  const gain = finiteNumber(verifiedGain);
  return Object.freeze({
    schema: "tristan.meta-depth-gate/0.1",
    depth: normalizedDepth,
    verifiedGain: gain,
    requiredGain,
    allowed: gain >= requiredGain,
    law: "MetaDepth <= DepthSupportedByVerifiedGain"
  });
}

export function compileMorphogeneticWorkspace({
  intent,
  objectType = "theory",
  operator = "GO OAK",
  metaDepth = 1,
  scores = {}
} = {}) {
  const capsule = createEpistemicCapsule({ intent, objectType });
  const residualField = deriveResidualField(capsule);
  const antiAdd = evaluateAntiAdd(scores);
  const metaDepthGate = evaluateMetaDepth({ depth: metaDepth, verifiedGain: scores.verifiedGain });

  return Object.freeze({
    schema: "tristan.morphogenetic-workspace/0.1",
    intent: capsule.intent,
    objectType: capsule.objectType,
    operator: normalizeLabel(operator, "GO OAK"),
    obligations: operatorEvidenceObligations(operator),
    capsule,
    residualField,
    antiAdd,
    metaDepthGate,
    materialization: antiAdd.decision === "CANDIDATE" && metaDepthGate.allowed ? "CANDIDATE" : antiAdd.decision === "REUSE" ? "REUSE" : "HOLD",
    authority: "none",
    boundary: "Workspace compilation is a reversible planning artifact. It performs no external action and grants no authority."
  });
}
