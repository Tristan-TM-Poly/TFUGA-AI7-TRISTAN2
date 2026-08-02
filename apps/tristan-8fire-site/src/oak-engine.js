"use strict";

export const OAK_CRITERIA = Object.freeze([
  { id: "scope_defined", label: "Portée définie", weight: 0.08, category: "truth" },
  { id: "status_explicit", label: "Statut épistémique explicite", weight: 0.08, category: "truth" },
  { id: "support_declared", label: "Support déclaré et traçable", weight: 0.10, category: "evidence" },
  { id: "independent_support", label: "Support indépendant disponible", weight: 0.10, category: "evidence" },
  { id: "counter_hypothesis", label: "Contre-hypothèse explicite", weight: 0.08, category: "falsification" },
  { id: "limit_defined", label: "Limite ou condition de falsification", weight: 0.10, category: "falsification", hard: true },
  { id: "next_test_defined", label: "Prochain test reproductible", weight: 0.10, category: "action", hard: true },
  { id: "baseline_defined", label: "Baseline de comparaison", weight: 0.08, category: "test" },
  { id: "uncertainty_explicit", label: "Incertitude et domaine de validité", weight: 0.08, category: "uncertainty" },
  { id: "negative_memory", label: "Mémoire négative conservée", weight: 0.06, category: "learning" },
  { id: "reversible_action", label: "Action suivante réversible", weight: 0.06, category: "safety" },
  { id: "human_review", label: "Révision humaine prévue", weight: 0.08, category: "governance", hard: true }
]);

export const PUBLICATION_GATES = Object.freeze([
  { id: "oak_gate", label: "OAKGate" },
  { id: "ip_gate", label: "IPGate" },
  { id: "privacy_gate", label: "PrivacyGate" },
  { id: "security_gate", label: "SecurityGate" }
]);

function clamp(value) {
  return Math.max(0, Math.min(1, Number(value) || 0));
}

function normalizeCriteria(raw = {}) {
  return Object.fromEntries(OAK_CRITERIA.map((criterion) => [criterion.id, Boolean(raw[criterion.id])]));
}

function normalizeGates(raw = {}) {
  return Object.fromEntries(PUBLICATION_GATES.map((gate) => [gate.id, Boolean(raw[gate.id])]));
}

export function evaluateOakGate(input = {}) {
  const criteria = normalizeCriteria(input.criteria);
  const gates = normalizeGates(input.gates);
  const autoPromotion = Boolean(input.automatic_promotion);
  const criteriaScore = OAK_CRITERIA.reduce((sum, criterion) => sum + (criteria[criterion.id] ? criterion.weight : 0), 0);
  const maximum = OAK_CRITERIA.reduce((sum, criterion) => sum + criterion.weight, 0);
  const normalizedScore = maximum ? clamp(criteriaScore / maximum) : 0;
  const missingCriteria = OAK_CRITERIA.filter((criterion) => !criteria[criterion.id]);
  const hardCriteria = missingCriteria.filter((criterion) => criterion.hard);
  const failedGates = PUBLICATION_GATES.filter((gate) => !gates[gate.id]);
  const blockers = [
    ...hardCriteria.map((criterion) => ({ code: `criterion.${criterion.id}`, message: `${criterion.label} est requis avant promotion.` })),
    ...failedGates.map((gate) => ({ code: `gate.${gate.id}`, message: `${gate.label} n’est pas franchie.` })),
    ...(autoPromotion ? [{ code: "governance.automatic_promotion", message: "La promotion automatique est interdite." }] : [])
  ];
  const confidenceDebt = clamp(1 - normalizedScore + failedGates.length * 0.12 + hardCriteria.length * 0.10);
  const status = blockers.length
    ? "blocked"
    : normalizedScore >= 0.85
      ? "human-review-candidate"
      : normalizedScore >= 0.65
        ? "draft-testable"
        : "insufficiently-specified";
  const nextActions = missingCriteria
    .sort((a, b) => Number(Boolean(b.hard)) - Number(Boolean(a.hard)) || b.weight - a.weight)
    .slice(0, 5)
    .map((criterion) => `Documenter ou exécuter : ${criterion.label}.`);
  if (failedGates.length) nextActions.unshift(`Résoudre les gates bloquées : ${failedGates.map((gate) => gate.label).join(", ")}.`);
  if (autoPromotion) nextActions.unshift("Désactiver toute promotion automatique et ajouter une approbation humaine explicite.");

  return {
    schema_version: "0.1.0",
    object: {
      type: String(input.object_type || "unknown"),
      id: String(input.object_id || "unidentified"),
      title: String(input.title || "Objet sans titre")
    },
    status,
    score: Number(normalizedScore.toFixed(4)),
    confidence_debt: Number(confidenceDebt.toFixed(4)),
    criteria,
    gates,
    blockers,
    missing_criteria: missingCriteria.map((criterion) => criterion.id),
    next_actions: nextActions,
    automatic_promotion: false,
    generated_at: new Date().toISOString(),
    epistemic_boundary: "OAKGate classe la préparation documentaire et expérimentale. Il ne certifie ni vérité, sécurité, légalité, brevetabilité, efficacité ni valeur marchande."
  };
}

export function prefillTheory(theory, claims = []) {
  const hasSupport = claims.some((claim) => Array.isArray(claim.support) && claim.support.length > 0);
  const hasIndependent = claims.some((claim) => (claim.support || []).some((support) => !String(support.type || "").includes("canon")));
  const hasCounter = claims.every((claim) => Array.isArray(claim.counter_hypotheses) && claim.counter_hypotheses.length > 0);
  const hasLimit = claims.every((claim) => String(claim.falsification_or_limit || "").trim().length >= 15);
  const hasTest = claims.every((claim) => String(claim.next_test || "").trim().length >= 15);
  const text = `${theory.status_note || ""} ${(theory.risks || []).join(" ")}`.toLowerCase();
  const publication = theory.publication || {};
  return {
    object_type: "theory",
    object_id: theory.id,
    title: `${theory.symbol} — ${theory.title}`,
    criteria: {
      scope_defined: Boolean(theory.summary && theory.domains?.length),
      status_explicit: Boolean(theory.maturity && theory.evidence),
      support_declared: hasSupport,
      independent_support: hasIndependent,
      counter_hypothesis: hasCounter,
      limit_defined: hasLimit,
      next_test_defined: hasTest && Boolean(theory.next_action),
      baseline_defined: /baseline|compar|benchmark/i.test(`${theory.status_note || ""} ${theory.next_action || ""}`),
      uncertainty_explicit: /incert|limite|domaine|résidu|provisoire/i.test(`${theory.status_note || ""} ${theory.summary || ""}`),
      negative_memory: /n[’']a pas|aucune|risque|limite|échec|surpromesse|non prouv/i.test(text),
      reversible_action: !/irréversible|déploiement autonome|fabrication réelle/i.test(theory.next_action || ""),
      human_review: publication.automatic_external_action === false
    },
    gates: {
      oak_gate: Boolean(publication.oak_gate),
      ip_gate: Boolean(publication.ip_gate),
      privacy_gate: Boolean(publication.privacy_gate),
      security_gate: Boolean(publication.security_gate)
    },
    automatic_promotion: false
  };
}

export function prefillClaim(claim, theory) {
  const support = claim.support || [];
  const text = `${claim.falsification_or_limit || ""} ${(claim.risk_tags || []).join(" ")}`;
  const publication = theory?.publication || {};
  return {
    object_type: "claim",
    object_id: claim.id,
    title: claim.title,
    criteria: {
      scope_defined: Boolean(claim.statement && claim.theory_id),
      status_explicit: Boolean(claim.status && claim.epistemic_level),
      support_declared: support.length > 0,
      independent_support: support.some((item) => !String(item.type || "").includes("canon")),
      counter_hypothesis: Boolean(claim.counter_hypotheses?.length),
      limit_defined: String(claim.falsification_or_limit || "").trim().length >= 15,
      next_test_defined: String(claim.next_test || "").trim().length >= 15,
      baseline_defined: /baseline|compar|benchmark/i.test(`${claim.next_test || ""} ${claim.falsification_or_limit || ""}`),
      uncertainty_explicit: /incert|limite|domaine|résidu|provisoire/i.test(text),
      negative_memory: claim.kind === "limit" || Boolean(claim.risk_tags?.length),
      reversible_action: !/irréversible|déployer|administrer|fabriquer/i.test(claim.next_test || ""),
      human_review: claim.automatic_promotion === false
    },
    gates: {
      oak_gate: Boolean(publication.oak_gate),
      ip_gate: Boolean(publication.ip_gate),
      privacy_gate: Boolean(publication.privacy_gate),
      security_gate: Boolean(publication.security_gate)
    },
    automatic_promotion: Boolean(claim.automatic_promotion)
  };
}
