"use strict";

export const KNOWLEDGE_WORLD_SCHEMA = "kworld-ir/0.2";

export const AUDIENCE_PROFILES = Object.freeze({
  GENERAL: Object.freeze({
    label: "Grand public",
    intent: "UNDERSTAND",
    depth: "overview",
    evidenceFloor: "PROTOTYPE",
    operators: ["ASK", "VIEW", "ZOOM", "TRACE", "COMPARE", "VERIFY"],
    representations: ["overview", "hero-artifacts", "timeline", "evidence-summary"],
    priorities: ["clarity", "public-value", "evidence", "unknowns"]
  }),
  RADIO_CANADA: Object.freeze({
    label: "Radio-Canada / média public",
    intent: "DISCOVER_VERIFY_STORY",
    depth: "editorial",
    evidenceFloor: "PROTOTYPE",
    operators: ["DISCOVER", "TRACE", "COMPARE", "VERIFY", "CHALLENGE", "REPRODUCE", "VISUALIZE"],
    representations: ["hero-artifacts", "evidence-passports", "visual-demos", "counterarguments", "media-readiness", "rights"],
    priorities: ["public-relevance", "evidence", "visual-power", "reproducibility", "rights", "correction-capacity"],
    affiliationBoundary: "Projection indépendante — aucune affiliation ou approbation de Radio-Canada"
  }),
  JOURNALIST: Object.freeze({
    label: "Journaliste",
    intent: "INVESTIGATE",
    depth: "editorial",
    evidenceFloor: "MEASURED",
    operators: ["ASK", "TRACE", "TIMELINE", "VERIFY", "CHALLENGE", "SOURCE", "EXPORT"],
    representations: ["claims", "sources", "timeline", "uncertainty", "opposition", "corrections"],
    priorities: ["provenance", "falsifiability", "context", "rights", "corrections"]
  }),
  RESEARCHER: Object.freeze({
    label: "Chercheur",
    intent: "FALSIFY_REPRODUCE",
    depth: "technical",
    evidenceFloor: "PROTOTYPE",
    operators: ["TRACE", "COMPARE", "DERIVE", "FALSIFY", "REPRODUCE", "SIMULATE", "SOURCE"],
    representations: ["claims", "methods", "baselines", "data", "code", "prior-art", "negative-results"],
    priorities: ["testability", "baseline", "uncertainty", "reproducibility", "prior-art"]
  }),
  TEACHER: Object.freeze({
    label: "Enseignant",
    intent: "TEACH_TRANSFER",
    depth: "pedagogical",
    evidenceFloor: "MEASURED",
    operators: ["EXPLAIN", "COMPARE", "SIMULATE", "TEST", "TRANSFER", "EXPAND"],
    representations: ["lesson", "visual-explainer", "exercise", "simulation", "sources"],
    priorities: ["clarity", "transfer", "accessibility", "evidence"]
  }),
  STUDENT: Object.freeze({
    label: "Étudiant",
    intent: "LEARN",
    depth: "guided",
    evidenceFloor: "PROTOTYPE",
    operators: ["ASK", "EXPLAIN", "ZOOM", "SIMULATE", "TEST", "REMEMBER"],
    representations: ["guided-explainer", "visuals", "examples", "exercise", "evidence-summary"],
    priorities: ["clarity", "scaffolding", "feedback", "transfer"]
  }),
  FOUNDER: Object.freeze({
    label: "Fondateur / entreprise",
    intent: "EVALUATE_APPLICATION",
    depth: "decision",
    evidenceFloor: "MEASURED",
    operators: ["COMPARE", "VERIFY", "SIMULATE", "TRACE", "EXPORT"],
    representations: ["use-case", "benchmark", "risk", "roadmap", "evidence", "ip-boundary"],
    priorities: ["utility", "benchmark", "risk", "cost", "ip", "reversibility"]
  }),
  INSTITUTION: Object.freeze({
    label: "Institution",
    intent: "EVALUATE_COLLABORATION",
    depth: "decision",
    evidenceFloor: "MEASURED",
    operators: ["DISCOVER", "COMPARE", "VERIFY", "TRACE", "COLLABORATE"],
    representations: ["mission-fit", "shared-value", "evidence", "risks", "collaboration-options"],
    priorities: ["mission-fit", "mutual-value", "feasibility", "evidence", "governance"]
  })
});

export const WORLD_MODES = Object.freeze({
  DISCOVER: ["hero-artifacts", "questions", "new-results", "residuals"],
  VERIFY: ["claims", "evidence", "sources", "uncertainty", "corrections"],
  THEORY: ["definition", "claims", "equations", "evidence", "prior-art", "limits", "lineage"],
  EXPERIMENT: ["question", "hypothesis", "baseline", "protocol", "results", "uncertainty", "reproduction"],
  SIMULATION: ["model", "assumptions", "parameters", "solver", "uncertainty", "validity-domain"],
  MEDIA: ["question", "story", "visual-demo", "evidence-passport", "rights", "correction-endpoint"],
  FAILURE: ["initial-claim", "test", "negative-result", "lesson", "descendant"],
  COLLABORATION: ["mission-fit", "shared-artifacts", "open-questions", "mutual-value", "permissions"],
  QUESTION: ["question", "known", "unknown", "evidence", "next-best-interaction"]
});

export const COGNITIVE_WEB_ISA = Object.freeze([
  "VIEW", "SEARCH", "ASK", "TRACE", "COMPARE", "ZOOM", "FILTER", "TIMELINE", "MAP",
  "CONNECT", "DERIVE", "SIMULATE", "PERTURB", "VERIFY", "FALSIFY", "PROVE", "REPRODUCE",
  "FORK", "CRITIQUE", "COMPRESS", "EXPAND", "EXPORT", "CONTACT", "COLLABORATE", "REMEMBER",
  "DISCOVER", "CHALLENGE", "VISUALIZE", "EXPLAIN", "TEST", "TRANSFER", "SOURCE"
]);

export const RELATIONSHIP_STATES = Object.freeze([
  "UNKNOWN", "DISCOVERED", "CONTACTED", "ENGAGED", "COLLABORATING", "ALUMNI"
]);

export const WORLD_CONSTITUTION = Object.freeze([
  "PersonalizeRepresentation ≠ PersonalizeTruth",
  "RelationshipState ≠ EvidenceStatus",
  "MediaCoverage ≠ ScientificValidation",
  "CanSee ≠ CanExport ≠ CanPublish",
  "CanDo ≠ MayDo",
  "VisualAuthority ≤ EvidenceAuthority",
  "HiddenPsychographicInference = 0",
  "AutomaticPublication = 0",
  "WorldPASS ≠ GlobalPASS"
]);

const EVIDENCE_ORDER = Object.freeze(["HYPOTHESIS", "FORMALIZATION", "PROTOTYPE", "MEASURED", "REPLICATED", "PROVEN"]);
const EVIDENCE_RANK = new Map(EVIDENCE_ORDER.map((level, index) => [level, index]));
const SENSITIVE_KEYS = Object.freeze([
  "politicalOrientation", "religion", "health", "sexualOrientation", "vulnerability", "psychographicProfile",
  "persuasionSusceptibility", "race", "ethnicity", "unionMembership"
]);

function safeArray(value) {
  return Array.isArray(value) ? value.filter((item) => item !== undefined && item !== null) : [];
}

function uniq(values) {
  return [...new Set(safeArray(values).map((value) => String(value)))];
}

function safeProfile(profile) {
  return AUDIENCE_PROFILES[profile] ? profile : "GENERAL";
}

function safeMode(mode) {
  return WORLD_MODES[mode] ? mode : "DISCOVER";
}

function safeRelationshipState(state) {
  return RELATIONSHIP_STATES.includes(state) ? state : "UNKNOWN";
}

function safeEvidence(level) {
  return EVIDENCE_RANK.has(level) ? level : "HYPOTHESIS";
}

function stableValue(value) {
  if (Array.isArray(value)) return value.map(stableValue);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, stableValue(value[key])]));
  }
  return value;
}

export function stableWorldId(seed) {
  const text = JSON.stringify(stableValue(seed));
  let hash = 2166136261;
  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return `WORLD-${(hash >>> 0).toString(16).padStart(8, "0")}`;
}

export function sanitizeRelationshipContext(context = {}) {
  const sanitized = {};
  const rejected = [];
  for (const [key, value] of Object.entries(context || {})) {
    if (SENSITIVE_KEYS.includes(key)) {
      rejected.push(key);
      continue;
    }
    if (["role", "declaredInterests", "sharedArtifacts", "interactionHistory", "relationshipState", "permissions", "organization", "publicMandate"].includes(key)) {
      sanitized[key] = value;
    }
  }
  sanitized.relationshipState = safeRelationshipState(sanitized.relationshipState);
  sanitized.declaredInterests = uniq(sanitized.declaredInterests);
  sanitized.sharedArtifacts = uniq(sanitized.sharedArtifacts);
  sanitized.interactionHistory = safeArray(sanitized.interactionHistory).slice(-20);
  return Object.freeze({ context: Object.freeze(sanitized), rejected: Object.freeze(rejected.sort()) });
}

export function compileEpistemicLens({ profile = "GENERAL", mode = "DISCOVER", evidenceLevel = "HYPOTHESIS", requestedDepth } = {}) {
  const profileId = safeProfile(profile);
  const modeId = safeMode(mode);
  const spec = AUDIENCE_PROFILES[profileId];
  const evidence = safeEvidence(evidenceLevel);
  return Object.freeze({
    profile: profileId,
    label: spec.label,
    intent: spec.intent,
    mode: modeId,
    depth: requestedDepth || spec.depth,
    evidenceLevel: evidence,
    evidenceFloor: spec.evidenceFloor,
    operators: Object.freeze(uniq([...spec.operators, ...(modeId === "VERIFY" ? ["VERIFY", "TRACE", "SOURCE"] : [])])),
    representations: Object.freeze(uniq([...spec.representations, ...WORLD_MODES[modeId]])),
    priorities: Object.freeze([...spec.priorities]),
    truthMutationAllowed: false,
    hiddenPsychographicInferenceAllowed: false,
    affiliationBoundary: spec.affiliationBoundary || null
  });
}

export function compileCapabilityMembrane({ publicWorld = true, permissions = [], relationshipState = "UNKNOWN" } = {}) {
  const granted = new Set(uniq(permissions));
  const state = safeRelationshipState(relationshipState);
  const membrane = {
    VIEW: true,
    ASK: true,
    TRACE: true,
    COMPARE: true,
    VERIFY: true,
    SIMULATE: true,
    FORK: true,
    EXPORT: granted.has("export"),
    CONTACT: granted.has("contact") || state !== "UNKNOWN",
    COMMENT: granted.has("comment"),
    EDIT: !publicWorld && granted.has("edit"),
    PUBLISH: false,
    DELETE_CANON: false,
    MUTATE_EVIDENCE_STATUS: false
  };
  return Object.freeze(membrane);
}

export function evidenceFloorSatisfied(level, floor) {
  return (EVIDENCE_RANK.get(safeEvidence(level)) ?? 0) >= (EVIDENCE_RANK.get(safeEvidence(floor)) ?? 0);
}

export function compileWorld({
  entity = { id: "anonymous", label: "Visiteur" },
  profile = "GENERAL",
  mode = "DISCOVER",
  evidenceLevel = "HYPOTHESIS",
  objects = [],
  residuals = [],
  relationship = {},
  requestedDepth,
  publicWorld = true
} = {}) {
  const relationshipResult = sanitizeRelationshipContext(relationship);
  const lens = compileEpistemicLens({ profile, mode, evidenceLevel, requestedDepth });
  const membrane = compileCapabilityMembrane({
    publicWorld,
    permissions: relationshipResult.context.permissions,
    relationshipState: relationshipResult.context.relationshipState
  });
  const canonicalEvidence = safeEvidence(evidenceLevel);
  const worldSeed = {
    entity: { id: String(entity?.id || "anonymous"), label: String(entity?.label || "Visiteur") },
    profile: lens.profile,
    mode: lens.mode,
    evidenceLevel: canonicalEvidence,
    objectIds: safeArray(objects).map((item) => String(item?.id || item)).sort(),
    relationshipState: relationshipResult.context.relationshipState
  };
  const id = stableWorldId(worldSeed);
  const world = {
    schema: KNOWLEDGE_WORLD_SCHEMA,
    id,
    entity: Object.freeze(worldSeed.entity),
    profile: lens.profile,
    mode: lens.mode,
    lens,
    objects: Object.freeze(safeArray(objects).map((item) => Object.freeze({
      id: String(item?.id || item),
      title: String(item?.title || item?.label || item?.id || item),
      evidenceLevel: safeEvidence(item?.evidenceLevel || canonicalEvidence),
      kind: String(item?.kind || "KNOWLEDGE_OBJECT")
    }))),
    residuals: Object.freeze(uniq(residuals)),
    relationship: relationshipResult.context,
    rejectedPersonalizationInputs: relationshipResult.rejected,
    capabilityMembrane: membrane,
    personalizationPolicy: Object.freeze({
      declaredContextOnly: true,
      sensitiveInference: false,
      truthMutation: false,
      evidenceMutation: false,
      relationshipChangesEvidence: false
    }),
    evidencePolicy: Object.freeze({
      canonicalEvidenceLevel: canonicalEvidence,
      audienceFloor: lens.evidenceFloor,
      floorSatisfied: evidenceFloorSatisfied(canonicalEvidence, lens.evidenceFloor),
      visualAuthorityMayNotExceedEvidenceAuthority: true
    })
  };
  return Object.freeze({ ...world, receipt: worldReceipt(world) });
}

export function worldReceipt(world) {
  const why = [
    `profile:${world.profile}`,
    `mode:${world.mode}`,
    `entity:${world.entity?.id || "anonymous"}`,
    `evidence:${world.evidencePolicy?.canonicalEvidenceLevel || "HYPOTHESIS"}`
  ];
  if (world.relationship?.relationshipState && world.relationship.relationshipState !== "UNKNOWN") {
    why.push(`relationship:${world.relationship.relationshipState}`);
  }
  return Object.freeze({
    id: `RECEIPT-${String(world.id || "UNKNOWN").replace(/^WORLD-/, "")}`,
    worldId: world.id,
    whyGenerated: Object.freeze(why),
    personalization: Object.freeze({
      profile: world.profile,
      declaredContextOnly: true,
      rejectedInputs: Object.freeze([...(world.rejectedPersonalizationInputs || [])])
    }),
    authority: Object.freeze({
      canPublish: Boolean(world.capabilityMembrane?.PUBLISH),
      canMutateEvidence: Boolean(world.capabilityMembrane?.MUTATE_EVIDENCE_STATUS),
      humanFinalAuthority: true
    }),
    missing: Object.freeze([...(world.residuals || [])]),
    reconstructible: true
  });
}

export function worldDiff(left, right) {
  const leftObjects = new Set(safeArray(left?.objects).map((item) => item.id));
  const rightObjects = new Set(safeArray(right?.objects).map((item) => item.id));
  return Object.freeze({
    profileChanged: left?.profile !== right?.profile,
    modeChanged: left?.mode !== right?.mode,
    evidenceChanged: left?.evidencePolicy?.canonicalEvidenceLevel !== right?.evidencePolicy?.canonicalEvidenceLevel,
    objectsAdded: Object.freeze([...rightObjects].filter((id) => !leftObjects.has(id)).sort()),
    objectsRemoved: Object.freeze([...leftObjects].filter((id) => !rightObjects.has(id)).sort()),
    operatorsAdded: Object.freeze(safeArray(right?.lens?.operators).filter((op) => !safeArray(left?.lens?.operators).includes(op))),
    operatorsRemoved: Object.freeze(safeArray(left?.lens?.operators).filter((op) => !safeArray(right?.lens?.operators).includes(op)))
  });
}

export function compileProfileSet({ entity, evidenceLevel = "PROTOTYPE", objects = [], residuals = [] } = {}) {
  return Object.freeze(Object.fromEntries(["GENERAL", "RADIO_CANADA", "RESEARCHER"].map((profile) => [profile, compileWorld({
    entity,
    profile,
    mode: profile === "RADIO_CANADA" ? "MEDIA" : profile === "RESEARCHER" ? "VERIFY" : "DISCOVER",
    evidenceLevel,
    objects,
    residuals,
    relationship: profile === "RADIO_CANADA" ? {
      role: "public-media",
      organization: "Radio-Canada",
      publicMandate: true,
      relationshipState: "DISCOVERED",
      declaredInterests: ["science", "public understanding", "evidence"],
      permissions: []
    } : {}
  })])));
}

export function knowledgeWorldKernelReceipt() {
  return Object.freeze({
    schema: KNOWLEDGE_WORLD_SCHEMA,
    profiles: Object.keys(AUDIENCE_PROFILES).length,
    modes: Object.keys(WORLD_MODES).length,
    operators: COGNITIVE_WEB_ISA.length,
    persistentWorldRoutesRequired: 1,
    automaticPublicationAllowed: false,
    hiddenPsychographicInferenceAllowed: false,
    constitution: WORLD_CONSTITUTION
  });
}
