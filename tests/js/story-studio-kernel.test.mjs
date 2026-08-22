import test from "node:test";
import assert from "node:assert/strict";
import {
  STORY_CAPABILITIES,
  STORY_CONSTITUTION,
  automationValue,
  compileStoryProgram,
  evaluateSceneEnvelope,
  metaPromotionDecision,
  queryCapabilities,
  regenerationClosure
} from "../../apps/tristan-8fire-site/src/story-studio-kernel.js";

test("story studio exposes a broad capability forest and hard invariants", () => {
  assert.ok(STORY_CAPABILITIES.length >= 80);
  assert.ok(STORY_CONSTITUTION.includes("Generated != Canon"));
  assert.ok(STORY_CONSTITUTION.includes("Generator != Judge"));
});

test("compiler creates a draft story program and expands franchise outputs", () => {
  const program = compileStoryProgram({ intent: "Cité mémoire", medium: "franchise", genre: "science-fiction" });
  assert.equal(program.canonStatus, "DRAFT");
  assert.equal(program.publication, "HOLD");
  assert.deepEqual(program.outputs, ["manga", "anime", "game", "novel", "website"]);
  assert.ok(program.storyIR.includes("CausalGraph"));
});

test("generated scene attempting canon without independent review is held", () => {
  const receipt = evaluateSceneEnvelope({ continuity: 0.9, causality: 0.9, rightsCleared: true, provenance: true, independentReview: false, attemptsCanon: true, verified: false });
  assert.equal(receipt.status, "HOLD");
  assert.ok(receipt.blockers.includes("independent-review"));
  assert.ok(receipt.blockers.includes("generated-is-not-canon"));
});

test("meta promotion requires positive verified gain, frozen benchmark and independent judge", () => {
  const pass = metaPromotionDecision({ verifiedGain: 0.4, complexity: 0.1, cost: 0.1, risk: 0.05, frozenBenchmark: true, independentJudge: true });
  const fail = metaPromotionDecision({ verifiedGain: 0.4, complexity: 0.1, cost: 0.1, risk: 0.05, frozenBenchmark: false, independentJudge: true });
  assert.equal(pass.decision, "PROMOTE");
  assert.equal(fail.decision, "PRUNE");
  assert.ok(fail.blockers.includes("benchmark-not-frozen"));
});

test("regeneration closure and automation value are explicit", () => {
  const closure = regenerationClosure(["generate", "verify", "canon"], ["generate", "verify"]);
  assert.equal(closure.ratio, 2 / 3);
  assert.deepEqual(closure.missing, ["canon"]);
  assert.ok(automationValue({ futureWorkEliminated: 10, reliability: 0.8, implementationCost: 2, risk: 1 }) > 0);
});

test("capability search filters by text and layer", () => {
  assert.ok(queryCapabilities("canon").length > 0);
  assert.ok(queryCapabilities("", "meta").every((item) => item.layer === "meta"));
});
