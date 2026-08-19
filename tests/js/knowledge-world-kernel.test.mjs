import assert from "node:assert/strict";
import test from "node:test";

import {
  AUDIENCE_PROFILES,
  WORLD_MODES,
  compileCapabilityMembrane,
  compileEpistemicLens,
  compileProfileSet,
  compileWorld,
  evidenceFloorSatisfied,
  knowledgeWorldKernelReceipt,
  sanitizeRelationshipContext,
  stableWorldId,
  worldDiff
} from "../../apps/tristan-8fire-site/src/knowledge-world-kernel.js";

test("kernel exposes a compressed profile/mode grammar", () => {
  const receipt = knowledgeWorldKernelReceipt();
  assert.ok(receipt.profiles >= 8);
  assert.ok(receipt.modes >= 8);
  assert.equal(receipt.persistentWorldRoutesRequired, 1);
  assert.equal(receipt.automaticPublicationAllowed, false);
});

test("stable IDs ignore object key order", () => {
  assert.equal(stableWorldId({ b: 2, a: 1 }), stableWorldId({ a: 1, b: 2 }));
});

test("epistemic lens personalizes representation, never truth", () => {
  const lens = compileEpistemicLens({ profile: "RADIO_CANADA", mode: "MEDIA", evidenceLevel: "PROTOTYPE" });
  assert.equal(lens.truthMutationAllowed, false);
  assert.equal(lens.hiddenPsychographicInferenceAllowed, false);
  assert.ok(lens.operators.includes("VERIFY"));
  assert.ok(lens.representations.includes("evidence-passports"));
});

test("sensitive psychographic inputs are rejected", () => {
  const result = sanitizeRelationshipContext({
    role: "journalist",
    declaredInterests: ["science"],
    politicalOrientation: "x",
    persuasionSusceptibility: 0.8,
    relationshipState: "CONTACTED"
  });
  assert.equal(result.context.role, "journalist");
  assert.deepEqual(result.rejected, ["persuasionSusceptibility", "politicalOrientation"]);
  assert.equal(result.context.relationshipState, "CONTACTED");
});

test("capability membrane never grants publication or evidence mutation", () => {
  const membrane = compileCapabilityMembrane({ publicWorld: false, permissions: ["export", "edit", "comment", "publish"] });
  assert.equal(membrane.EXPORT, true);
  assert.equal(membrane.EDIT, true);
  assert.equal(membrane.PUBLISH, false);
  assert.equal(membrane.MUTATE_EVIDENCE_STATUS, false);
});

test("relationship state cannot inflate evidence status", () => {
  const world = compileWorld({
    entity: { id: "rc", label: "Radio-Canada" },
    profile: "RADIO_CANADA",
    mode: "MEDIA",
    evidenceLevel: "PROTOTYPE",
    relationship: { relationshipState: "COLLABORATING", permissions: ["export"] }
  });
  assert.equal(world.evidencePolicy.canonicalEvidenceLevel, "PROTOTYPE");
  assert.equal(world.personalizationPolicy.relationshipChangesEvidence, false);
  assert.equal(world.receipt.authority.canPublish, false);
});

test("evidence floors remain explicit and non-compensatory", () => {
  assert.equal(evidenceFloorSatisfied("PROTOTYPE", "MEASURED"), false);
  assert.equal(evidenceFloorSatisfied("REPLICATED", "MEASURED"), true);
  const journalist = compileWorld({ profile: "JOURNALIST", evidenceLevel: "PROTOTYPE" });
  assert.equal(journalist.evidencePolicy.floorSatisfied, false);
});

test("profile set reuses one object graph while changing lenses", () => {
  const objects = [{ id: "A1", title: "Hero artifact", evidenceLevel: "MEASURED", kind: "ARTIFACT" }];
  const set = compileProfileSet({ entity: { id: "tristan", label: "Tristan" }, evidenceLevel: "MEASURED", objects, residuals: ["Independent replication"] });
  assert.deepEqual(Object.keys(set), ["GENERAL", "RADIO_CANADA", "RESEARCHER"]);
  assert.equal(set.GENERAL.objects[0].id, set.RADIO_CANADA.objects[0].id);
  assert.notDeepEqual(set.GENERAL.lens.representations, set.RADIO_CANADA.lens.representations);
  assert.equal(set.RADIO_CANADA.receipt.missing[0], "Independent replication");
});

test("world diff explains personalization rather than hiding it", () => {
  const general = compileWorld({ profile: "GENERAL", mode: "DISCOVER", evidenceLevel: "MEASURED", objects: [{ id: "A" }] });
  const researcher = compileWorld({ profile: "RESEARCHER", mode: "VERIFY", evidenceLevel: "MEASURED", objects: [{ id: "A" }, { id: "B" }] });
  const diff = worldDiff(general, researcher);
  assert.equal(diff.profileChanged, true);
  assert.equal(diff.evidenceChanged, false);
  assert.deepEqual(diff.objectsAdded, ["B"]);
  assert.ok(diff.operatorsAdded.includes("FALSIFY"));
});

test("registries are defined without generating hard-coded pages", () => {
  assert.ok(AUDIENCE_PROFILES.RESEARCHER);
  assert.ok(WORLD_MODES.FAILURE);
});
