import test from "node:test";
import assert from "node:assert/strict";
import {
  RADIO_CANADA_MRU,
  amplificationDecision,
  compileBroadcastableKnowledgeObject,
  mediaOakGate,
  mediaReadiness,
  propagationPlan,
  publicMediaReceipt,
  semanticTranscode
} from "../../apps/tristan-8fire-site/src/public-media-kernel.js";

test("media readiness is bounded and evidence-aware", () => {
  const result = mediaReadiness({
    evidenceLevel: "REPLICATED",
    demonstrability: 1,
    visualPower: 1,
    publicRelevance: 1,
    clarity: 1,
    timeliness: 1,
    reproducibility: 1,
    rightsReadiness: 1
  });
  assert.ok(result.score > 0 && result.score <= 1);
  assert.equal(result.evidenceLevel, "REPLICATED");
});

test("OAK media gate blocks missing provenance and any auto-publication", () => {
  const decision = mediaOakGate({
    evidenceLevel: "PROTOTYPE",
    question: "Q?",
    evidence: true,
    limitations: true,
    provenance: false,
    rights: true,
    correctionEndpoint: true,
    humanEditorialReview: true,
    autoPublish: true
  });
  assert.equal(decision.status, "HOLD");
  assert.ok(decision.failed.includes("provenance"));
  assert.ok(decision.failed.includes("auto_publish_forbidden"));
  assert.equal(decision.humanFinalAuthority, true);
});

test("amplification cannot exceed evidence cap or correction capacity", () => {
  const decision = amplificationDecision({
    evidenceLevel: "HYPOTHESIS",
    correctionCapacity: 0.9,
    requestedReach: 1
  });
  assert.equal(decision.allowedReach, 0.1);
  assert.equal(decision.status, "THROTTLE");
});

test("propagation plan gates grand-public wave behind replication", () => {
  const measured = propagationPlan({ evidenceLevel: "MEASURED" });
  assert.equal(measured.find((wave) => wave.id === "W3").eligible, true);
  assert.equal(measured.find((wave) => wave.id === "W4").eligible, false);
  const replicated = propagationPlan({ evidenceLevel: "REPLICATED" });
  assert.equal(replicated.find((wave) => wave.id === "W4").eligible, true);
});

test("broadcastable object preserves required invariants for short transcode", () => {
  const bko = compileBroadcastableKnowledgeObject({
    title: "Demo",
    question: "Can this be verified?",
    evidenceLevel: "PROTOTYPE",
    evidence: ["test"],
    limitations: ["not measured in newsroom"],
    provenance: ["repo"],
    attribution: ["author"],
    correctionEndpoint: "issue"
  });
  assert.equal(semanticTranscode(bko, 60).status, "SAFE_COMPRESSION");
  assert.equal(bko.automaticPublicationAllowed, false);
});

test("semantic transcode reports meaning loss for incomplete object", () => {
  const bko = compileBroadcastableKnowledgeObject({ title: "Incomplete", question: "Q", evidenceLevel: "HYPOTHESIS" });
  const result = semanticTranscode(bko, 15);
  assert.equal(result.status, "MEANING_LOSS");
  assert.ok(result.missing.includes("evidence"));
});

test("Radio-Canada MRU and public receipt keep authority bounded", () => {
  const receipt = publicMediaReceipt({ evidenceLevel: "PROTOTYPE", correctionCapacity: 1, requestedReach: 1 });
  assert.equal(RADIO_CANADA_MRU.id, "RC-MRU-001");
  assert.equal(receipt.automaticPublicationAllowed, false);
  assert.equal(receipt.humanFinalAuthority, true);
  assert.match(receipt.claimBoundary, /no affiliation/i);
});
