import assert from "node:assert/strict";
import test from "node:test";

import {
  evaluateOakGate,
  OAK_CRITERIA,
  PUBLICATION_GATES,
  prefillClaim,
  prefillTheory
} from "../../apps/tristan-8fire-site/src/oak-engine.js";

function allCriteria(value) {
  return Object.fromEntries(OAK_CRITERIA.map((criterion) => [criterion.id, value]));
}

function allGates(value) {
  return Object.fromEntries(PUBLICATION_GATES.map((gate) => [gate.id, value]));
}

test("criterion weights form one normalized readiness score", () => {
  const total = OAK_CRITERIA.reduce((sum, criterion) => sum + criterion.weight, 0);
  assert.ok(Math.abs(total - 1) < 1e-12);
});

test("an empty object is blocked by hard criteria and publication gates", () => {
  const result = evaluateOakGate({
    object_type: "claim",
    object_id: "claim-empty",
    title: "Empty claim",
    criteria: allCriteria(false),
    gates: allGates(false)
  });
  assert.equal(result.status, "blocked");
  assert.equal(result.score, 0);
  assert.ok(result.confidence_debt > 0.9);
  assert.ok(result.blockers.some((item) => item.code === "criterion.limit_defined"));
  assert.ok(result.blockers.some((item) => item.code === "criterion.next_test_defined"));
  assert.ok(result.blockers.some((item) => item.code === "criterion.human_review"));
  assert.ok(result.blockers.some((item) => item.code === "gate.security_gate"));
  assert.equal(result.automatic_promotion, false);
});

test("complete inputs become human review candidates, never certifications", () => {
  const result = evaluateOakGate({
    object_type: "theory",
    object_id: "omega-test",
    title: "Complete test theory",
    criteria: allCriteria(true),
    gates: allGates(true),
    automatic_promotion: false
  });
  assert.equal(result.status, "human-review-candidate");
  assert.equal(result.score, 1);
  assert.equal(result.confidence_debt, 0);
  assert.deepEqual(result.blockers, []);
  assert.match(result.epistemic_boundary, /ne certifie/i);
  assert.equal(result.automatic_promotion, false);
});

test("automatic promotion is always converted into a blocker", () => {
  const result = evaluateOakGate({
    object_type: "claim",
    object_id: "claim-auto",
    title: "Unsafe automatic claim",
    criteria: allCriteria(true),
    gates: allGates(true),
    automatic_promotion: true
  });
  assert.equal(result.status, "blocked");
  assert.ok(result.blockers.some((item) => item.code === "governance.automatic_promotion"));
  assert.equal(result.automatic_promotion, false);
});

test("theory prefill does not invent independent support", () => {
  const theory = {
    id: "omega-demo",
    symbol: "Ω-DEMO",
    title: "Demo",
    summary: "A sufficiently descriptive public theory summary.",
    domains: ["test"],
    maturity: "prototype",
    evidence: "internal test",
    status_note: "A baseline remains required and uncertainty is explicit.",
    next_action: "Compare the prototype against a baseline in a reversible test.",
    risks: ["surpromesse"],
    publication: {
      oak_gate: true,
      ip_gate: true,
      privacy_gate: true,
      security_gate: true,
      automatic_external_action: false
    }
  };
  const claims = [{
    support: [{ type: "canonical-card", path: "docs/demo.md" }],
    counter_hypotheses: ["A simpler baseline explains the result."],
    falsification_or_limit: "The effect disappears outside the declared test domain.",
    next_test: "Run a controlled reversible comparison against the baseline."
  }];
  const prefill = prefillTheory(theory, claims);
  assert.equal(prefill.criteria.support_declared, true);
  assert.equal(prefill.criteria.independent_support, false);
  assert.equal(prefill.criteria.human_review, true);
});

test("claim prefill preserves the no-promotion guard", () => {
  const claim = {
    id: "claim-demo",
    theory_id: "omega-demo",
    title: "Demo claim",
    statement: "A bounded effect is proposed inside a declared test domain.",
    status: "candidate",
    epistemic_level: "hypothesis",
    kind: "scope",
    support: [{ type: "external-study", path: "reports/study.md" }],
    counter_hypotheses: ["The measured effect is an artefact."],
    falsification_or_limit: "Reject when the effect is not stable under the baseline controls.",
    next_test: "Run a reversible benchmark with uncertainty and a negative control.",
    risk_tags: ["surpromesse"],
    automatic_promotion: false
  };
  const theory = {
    publication: {
      oak_gate: true,
      ip_gate: true,
      privacy_gate: true,
      security_gate: true
    }
  };
  const prefill = prefillClaim(claim, theory);
  assert.equal(prefill.criteria.independent_support, true);
  assert.equal(prefill.criteria.counter_hypothesis, true);
  assert.equal(prefill.automatic_promotion, false);
});
