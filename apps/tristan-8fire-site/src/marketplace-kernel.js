"use strict";

const clamp01 = (value) => Math.max(0, Math.min(1, Number(value || 0)));
const roundMoney = (value) => Math.round(value * 100) / 100;

export const EVIDENCE_LEVELS = Object.freeze({
  HYPOTHESIS: 0.08,
  DOCUMENTED: 0.22,
  PROTOTYPE: 0.38,
  MEASURED: 0.58,
  REPLICATED: 0.78,
  INDEPENDENTLY_VERIFIED: 0.92,
  CONTRACTUALLY_VALIDATED: 1
});

export const QUEBEC_GROUP_FAMILIES = Object.freeze([
  { id: "territories", label: "Régions, territoires et MRC", mode: "public-aggregate", examples: "régions administratives, MRC, territoires publics" },
  { id: "municipal", label: "Municipalités et arrondissements", mode: "public-organization", examples: "villes, municipalités, arrondissements" },
  { id: "education", label: "Universités, cégeps et réseaux scolaires", mode: "public-organization", examples: "établissements, facultés, centres de services scolaires" },
  { id: "research", label: "Laboratoires et centres de recherche", mode: "public-or-consent", examples: "laboratoires, instituts, regroupements de recherche" },
  { id: "health", label: "Établissements et réseaux de santé", mode: "public-organization", examples: "CISSS/CIUSSS, hôpitaux, instituts" },
  { id: "public", label: "Ministères, organismes et sociétés publiques", mode: "public-organization", examples: "organismes, agences, sociétés d'État" },
  { id: "companies", label: "Entreprises, PME et startups", mode: "public-or-consent", examples: "entreprises inscrites et informations d'affaires publiques" },
  { id: "coops", label: "Coopératives et entreprises collectives", mode: "public-or-consent", examples: "coopératives, mutuelles, économie sociale" },
  { id: "nonprofit", label: "OBNL, fondations et organismes communautaires", mode: "public-or-consent", examples: "organismes sans but lucratif et communautaires" },
  { id: "associations", label: "Associations professionnelles et sectorielles", mode: "public-organization", examples: "ordres, associations, chambres et regroupements" },
  { id: "labour", label: "Organisations syndicales et professionnelles", mode: "public-organization-only", examples: "organisations publiques; aucune inférence d'adhésion individuelle" },
  { id: "culture", label: "Culture, médias et création", mode: "public-or-consent", examples: "médias, musées, arts, collectifs créatifs" },
  { id: "sports", label: "Sports et loisirs", mode: "public-or-consent", examples: "fédérations, clubs et ligues" },
  { id: "environment", label: "Groupes environnementaux et territoriaux", mode: "public-or-consent", examples: "organismes, bassins versants, groupes de conservation" },
  { id: "innovation", label: "Écosystèmes technologiques et entrepreneuriaux", mode: "public-or-consent", examples: "incubateurs, accélérateurs, grappes, hubs" },
  { id: "civic", label: "Institutions civiques et politiques publiques", mode: "public-organization-only", examples: "institutions, conseils et organisations publiques; aucun profil politique individuel" },
  { id: "indigenous", label: "Nations et organisations autochtones", mode: "governance-and-consent", examples: "représentation publique ou explicitement autorisée; souveraineté des données respectée" },
  { id: "communities", label: "Communautés et collectifs locaux", mode: "aggregate-or-consent", examples: "collectifs locaux; seuils anti-réidentification obligatoires" }
]);

const BLOCKED_EXTENSIONS = new Set(["exe", "msi", "dmg", "apk", "app", "com", "scr", "bat", "cmd", "ps1", "vbs", "jar"]);
const QUARANTINE_EXTENSIONS = new Set(["zip", "7z", "rar", "tar", "gz", "tgz", "bz2", "xz", "docm", "xlsm", "pptm", "html", "htm", "svg"]);
const TEXT_SOURCE_EXTENSIONS = new Set(["js", "mjs", "cjs", "ts", "tsx", "jsx", "py", "rs", "go", "java", "c", "h", "cpp", "hpp", "sh", "sql", "yaml", "yml", "toml"]);
const SAFE_DOCUMENT_EXTENSIONS = new Set(["pdf", "txt", "md", "docx", "xlsx", "pptx", "csv", "json", "xml", "rtf", "odt", "ods", "odp", "png", "jpg", "jpeg", "webp", "gif", "mp3", "wav", "mp4", "webm"]);

function extensionOf(fileName = "") {
  const value = String(fileName).trim().toLowerCase();
  const last = value.split("/").pop() || "";
  if (!last.includes(".")) return "";
  return last.split(".").pop() || "";
}

export function classifyUpload({ name = "", type = "", size = 0 } = {}) {
  const extension = extensionOf(name);
  const bytes = Math.max(0, Number(size || 0));
  let risk = "REVIEW";
  let category = "other";
  let reason = "unknown_file_type";

  if (BLOCKED_EXTENSIONS.has(extension)) {
    risk = "BLOCK";
    category = "executable";
    reason = "active_binary_forbidden";
  } else if (QUARANTINE_EXTENSIONS.has(extension)) {
    risk = "QUARANTINE";
    category = extension === "zip" || ["7z", "rar", "tar", "gz", "tgz", "bz2", "xz"].includes(extension) ? "archive" : "active-document";
    reason = category === "archive" ? "archive_scan_required" : "active_content_scan_required";
  } else if (TEXT_SOURCE_EXTENSIONS.has(extension)) {
    risk = "REVIEW";
    category = "source-code";
    reason = "store_as_text_never_execute";
  } else if (SAFE_DOCUMENT_EXTENSIONS.has(extension)) {
    risk = "ALLOW";
    category = "document-or-media";
    reason = "supported_passive_format";
  } else if (String(type).startsWith("text/")) {
    risk = "REVIEW";
    category = "text";
    reason = "mime_text_unknown_extension";
  }

  if (bytes > 5 * 1024 * 1024 * 1024) {
    risk = "BLOCK";
    reason = "file_too_large_over_5_gib";
  }

  return Object.freeze({ extension, bytes, risk, category, reason });
}

export function uploadGate(file, context = {}) {
  const classification = classifyUpload(file);
  const failed = [];
  if (!context.isSubscriber) failed.push("subscriber_required");
  if (!context.rightsDeclared) failed.push("rights_declaration_required");
  if (!context.privacyDeclared) failed.push("privacy_declaration_required");
  if (classification.risk === "BLOCK") failed.push(classification.reason);
  if (context.containsPersonalData && !context.privacyImpactAssessment) failed.push("privacy_impact_assessment_required");

  const status = failed.length ? "HOLD" : classification.risk === "QUARANTINE" || classification.risk === "REVIEW" ? "QUARANTINE" : "READY_FOR_PRIVATE_UPLOAD";
  return Object.freeze({ status, classification, failed, executeUploadedContent: false, publicByDefault: false });
}

export function proofValueReceipt(input = {}) {
  const evidenceLevel = String(input.evidenceLevel || "HYPOTHESIS").toUpperCase();
  const evidence = EVIDENCE_LEVELS[evidenceLevel] ?? EVIDENCE_LEVELS.HYPOTHESIS;
  const signals = Object.freeze({
    evidence,
    utility: clamp01(input.utility),
    reproducibility: clamp01(input.reproducibility),
    provenance: clamp01(input.provenance),
    rights: clamp01(input.rights),
    uniqueness: clamp01(input.uniqueness),
    freshness: clamp01(input.freshness),
    buyerValidation: clamp01(input.buyerValidation)
  });

  const score = clamp01(
    signals.evidence * 0.25 +
    signals.utility * 0.20 +
    signals.reproducibility * 0.15 +
    signals.provenance * 0.10 +
    signals.rights * 0.10 +
    signals.uniqueness * 0.10 +
    signals.freshness * 0.05 +
    signals.buyerValidation * 0.05
  );

  const independentReceipts = Math.max(0, Math.floor(Number(input.independentReceipts || 0)));
  const hardGates = {
    evidenceEnough: evidence >= EVIDENCE_LEVELS.MEASURED,
    provenanceEnough: signals.provenance >= 0.7,
    rightsEnough: signals.rights >= 0.9,
    reproducibilityEnough: signals.reproducibility >= 0.5,
    independentEvidence: independentReceipts >= 1
  };
  const verified = Object.values(hardGates).every(Boolean);

  const baseCad = 1.49;
  const suggestedCad = roundMoney(baseCad + 247.5 * score * score);
  const ceilingCad = roundMoney(Math.max(suggestedCad, suggestedCad * 1.35));
  const floorCad = roundMoney(Math.max(0.99, suggestedCad * 0.55));

  return Object.freeze({
    status: verified ? "VERIFIED_VALUE" : "PROVISIONAL_VALUE",
    score: roundMoney(score),
    suggestedCad,
    floorCad,
    ceilingCad,
    evidenceLevel,
    independentReceipts,
    hardGates,
    signals,
    pricingIsTruthClaim: false
  });
}

export function pricingDecision(receipt, requestedCad) {
  const price = roundMoney(Number(requestedCad || 0));
  const failed = [];
  if (!receipt || receipt.status !== "VERIFIED_VALUE") failed.push("verified_value_required");
  if (!(price > 0)) failed.push("positive_price_required");
  if (receipt && price < receipt.floorCad) failed.push("below_verified_floor");
  if (receipt && price > receipt.ceilingCad) failed.push("above_verified_ceiling");
  return Object.freeze({ status: failed.length ? "HOLD" : "PRICE_ALLOWED", requestedCad: price, failed });
}

export function downloadGate(input = {}) {
  const failed = [];
  if (!input.assetExists) failed.push("asset_missing");
  if (!input.malwareScanClean) failed.push("malware_scan_required");
  if (!input.rightsGate) failed.push("rights_gate_required");
  if (!input.privacyGate) failed.push("privacy_gate_required");
  if (!input.valueReceiptVerified) failed.push("verified_value_receipt_required");
  if (!(input.includedInSubscription || input.purchasePaid)) failed.push("paid_entitlement_required");
  if (input.refunded || input.revoked) failed.push("entitlement_revoked");
  return Object.freeze({ status: failed.length ? "DENY" : "ALLOW_PRIVATE_DOWNLOAD", failed, publicUrlAllowed: false });
}

export function groupTwinGate(input = {}) {
  const failed = [];
  const sourceMode = String(input.sourceMode || "");
  const aggregateSize = Math.max(0, Number(input.aggregateSize || 0));
  const isPublicOrganization = Boolean(input.isPublicOrganization);
  if (!input.provenance) failed.push("provenance_required");
  if (input.personalProfiles) failed.push("individual_profile_forbidden");
  if (input.sensitiveInference) failed.push("sensitive_inference_forbidden");
  if (input.membershipInference) failed.push("membership_inference_forbidden");
  if (!isPublicOrganization && !["consent", "aggregate", "public"].includes(sourceMode)) failed.push("consent_or_public_aggregate_required");
  if (!isPublicOrganization && sourceMode === "aggregate" && aggregateSize < 20) failed.push("anti_reidentification_threshold");
  if (input.containsPersonalData && !input.privacyImpactAssessment) failed.push("privacy_impact_assessment_required");
  if (input.dataSovereigntyRequired && !input.governanceApproval) failed.push("community_governance_required");
  return Object.freeze({ status: failed.length ? "HOLD" : "TWIN_ALLOWED", failed, individualLevel: false });
}

export function compileQuebecGroupTwin(input = {}) {
  const family = QUEBEC_GROUP_FAMILIES.find((item) => item.id === input.familyId);
  if (!family) throw new Error("Unknown Quebec group family");
  const gate = groupTwinGate(input);
  return Object.freeze({
    id: String(input.id || `QC-TWIN-${family.id}`).toUpperCase(),
    name: String(input.name || family.label),
    familyId: family.id,
    familyLabel: family.label,
    region: String(input.region || "Québec"),
    sourceMode: String(input.sourceMode || family.mode),
    status: gate.status,
    gate,
    observables: Array.isArray(input.observables) ? [...input.observables] : [],
    provenance: Array.isArray(input.provenanceEntries) ? [...input.provenanceEntries] : [],
    uncertainty: clamp01(input.uncertainty ?? 1),
    lastVerifiedAt: input.lastVerifiedAt || null,
    individualProfiles: false,
    protectedAttributeInference: false,
    claimBoundary: "Twin of a collective/public entity; not a profile of any natural person and not proof of group membership."
  });
}

export function marketplaceCapabilityStatus(config = {}) {
  const requirements = {
    identity: Boolean(config.identity),
    privateStorage: Boolean(config.privateStorage),
    malwareScanning: Boolean(config.malwareScanning),
    payments: Boolean(config.payments),
    entitlementLedger: Boolean(config.entitlementLedger),
    taxConfig: Boolean(config.taxConfig)
  };
  const ready = Object.values(requirements).every(Boolean);
  return Object.freeze({ status: ready ? "LIVE_READY" : "FAIL_CLOSED", requirements, ready });
}
