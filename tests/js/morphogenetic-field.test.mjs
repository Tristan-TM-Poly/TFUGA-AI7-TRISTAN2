import assert from "node:assert/strict";
import test from "node:test";

import {
  createEpistemicCapsule,
  createTransformationField,
  compileMorphogeneticWorkspace,
  deriveResidualField,
  evaluateAntiAdd,
  evaluateMetaDepth,
  operatorEvidenceObligations
} from "../../apps/tristan-8fire-site/src/morphogenetic-field.js";
import {
  HYPERMETA_FAMILIES,
  HYPERMETA_OPERATORS,
  generateHyperMetaCells,
  hyperMetaKernelReceipt
} from "../../apps/tristan-8fire-site/src/hypermeta-kernel.js";

test("HyperMeta bootstrap remains 1024 while custom grammars can shrink or expand", () => {
  const bootstrap = hyperMetaKernelReceipt();
  const compact = generateHyperMetaCells({
    families: [["proof", "Proof"], ["simulation", "Simulation"]],
    operators: ["GO OAK", "GO PROVE", "GO ZERO"],
    namespace: "compact"
  });

  assert.equal(bootstrap.generatedCells, 1024);
  assert.equal(bootstrap.dynamicGrammar, true);
  assert.equal(HYPERMETA_FAMILIES.length, 32);
  assert.equal(HYPERMETA_OPERATORS.length, 32);
  assert.equal(compact.length, 6);
  assert.equal(compact[0].id, "compact-0001");
  assert.equal(compact.at(-1).id, "compact-0006");
});

test("TransformationField attaches evidence obligations without claiming completion", () => {
  const field = createTransformationField({
    families: [["claim", "Claim"]],
    operators: ["GO PROVE", "GO SIMULATE"],
    objectType: "claim"
  });

  assert.equal(field.cellCount, 2);
  assert.deepEqual(field.cells[0].obligations, ["formal-proof-or-explicit-unproved-status"]);
  assert.deepEqual(field.cells[1].obligations, ["model-domain", "solver-provenance", "simulation-not-proof"]);
  assert.deepEqual(operatorEvidenceObligations("GO MERGE"), []);
});

test("EpistemicCapsule produces explicit residuals for missing evidence surfaces", () => {
  const capsule = createEpistemicCapsule({ intent: "Tester X", objectType: "theory" });
  const residual = deriveResidualField(capsule);

  assert.equal(capsule.authority, undefined);
  assert.equal(residual.count, 5);
  assert.deepEqual([...residual.types].sort(), ["uncertain", "unimplemented", "unknown", "unproved", "untested"].sort());
});

test("ANTI-ADD distinguishes reuse, candidate, hold and destruction", () => {
  assert.equal(evaluateAntiAdd({ novelCoverage: 0, reuseGain: 2, complexityDebt: 0.25 }).decision, "REUSE");
  assert.equal(evaluateAntiAdd({ novelCoverage: 1, reuseGain: 1, verifiedGain: 1, complexityDebt: 0.5 }).decision, "CANDIDATE");
  assert.equal(evaluateAntiAdd({ novelCoverage: 1, verifiedGain: 0, complexityDebt: 1 }).decision, "HOLD");
  assert.equal(evaluateAntiAdd({ novelCoverage: 0, verifiedGain: 0, complexityDebt: 2 }).decision, "DESTROY");
});

test("MetaDepth is bounded by verified gain", () => {
  assert.equal(evaluateMetaDepth({ depth: 2, verifiedGain: 0.5, minGainPerDepth: 0.25 }).allowed, true);
  assert.equal(evaluateMetaDepth({ depth: 3, verifiedGain: 0.5, minGainPerDepth: 0.25 }).allowed, false);
});

test("Morphogenetic workspace is reversible, authority-free and fail-closed", () => {
  const pass = compileMorphogeneticWorkspace({
    intent: "Prouver une propriété",
    objectType: "claim",
    operator: "GO PROVE",
    metaDepth: 1,
    scores: { novelCoverage: 1, reuseGain: 0.5, verifiedGain: 0.5, complexityDebt: 0.25 }
  });
  const hold = compileMorphogeneticWorkspace({
    intent: "Ajouter une couche méta non justifiée",
    objectType: "theory",
    operator: "GO EVOLVE",
    metaDepth: 4,
    scores: { novelCoverage: 1, reuseGain: 0, verifiedGain: 0.25, complexityDebt: 0 }
  });

  assert.equal(pass.materialization, "CANDIDATE");
  assert.equal(pass.authority, "none");
  assert.deepEqual(pass.obligations, ["formal-proof-or-explicit-unproved-status"]);
  assert.equal(hold.materialization, "HOLD");
  assert.equal(hold.metaDepthGate.allowed, false);
});
