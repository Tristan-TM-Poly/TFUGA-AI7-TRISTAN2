import test from "node:test";
import assert from "node:assert/strict";
import {
  QUEBEC_GROUP_FAMILIES,
  classifyUpload,
  compileQuebecGroupTwin,
  downloadGate,
  groupTwinGate,
  marketplaceCapabilityStatus,
  pricingDecision,
  proofValueReceipt,
  uploadGate
} from "../../apps/tristan-8fire-site/src/marketplace-kernel.js";

test("passive documents are allowed and executables are blocked", () => {
  assert.equal(classifyUpload({ name: "paper.pdf", size: 100 }).risk, "ALLOW");
  assert.equal(classifyUpload({ name: "payload.exe", size: 100 }).risk, "BLOCK");
});

test("archives are quarantined and never executed", () => {
  const gate = uploadGate({ name: "dataset.zip", size: 1000 }, { isSubscriber: true, rightsDeclared: true, privacyDeclared: true });
  assert.equal(gate.status, "QUARANTINE");
  assert.equal(gate.executeUploadedContent, false);
});

test("value pricing stays provisional without independent proof", () => {
  const receipt = proofValueReceipt({ evidenceLevel: "MEASURED", utility: 1, reproducibility: 1, provenance: 1, rights: 1, uniqueness: 1, freshness: 1, buyerValidation: 1, independentReceipts: 0 });
  assert.equal(receipt.status, "PROVISIONAL_VALUE");
  assert.ok(receipt.suggestedCad > 0);
  assert.equal(pricingDecision(receipt, receipt.suggestedCad).status, "HOLD");
});

test("verified value enables bounded pricing", () => {
  const receipt = proofValueReceipt({ evidenceLevel: "REPLICATED", utility: 0.9, reproducibility: 0.9, provenance: 1, rights: 1, uniqueness: 0.7, freshness: 0.8, buyerValidation: 0.8, independentReceipts: 2 });
  assert.equal(receipt.status, "VERIFIED_VALUE");
  assert.equal(pricingDecision(receipt, receipt.suggestedCad).status, "PRICE_ALLOWED");
  assert.equal(pricingDecision(receipt, receipt.ceilingCad + 100).status, "HOLD");
});

test("paid download requires entitlement and safety gates", () => {
  const denied = downloadGate({ assetExists: true, malwareScanClean: true, rightsGate: true, privacyGate: true, valueReceiptVerified: true });
  assert.equal(denied.status, "DENY");
  const allowed = downloadGate({ assetExists: true, malwareScanClean: true, rightsGate: true, privacyGate: true, valueReceiptVerified: true, purchasePaid: true });
  assert.equal(allowed.status, "ALLOW_PRIVATE_DOWNLOAD");
});

test("group twins reject individual or sensitive inference", () => {
  const gate = groupTwinGate({ provenance: true, isPublicOrganization: true, personalProfiles: true, sensitiveInference: true });
  assert.equal(gate.status, "HOLD");
  assert.ok(gate.failed.includes("individual_profile_forbidden"));
  assert.ok(gate.failed.includes("sensitive_inference_forbidden"));
});

test("public organization twin can be compiled without person-level claims", () => {
  const twin = compileQuebecGroupTwin({ familyId: "education", name: "Établissement public exemple", isPublicOrganization: true, sourceMode: "public", provenance: true, uncertainty: 0.2 });
  assert.equal(twin.status, "TWIN_ALLOWED");
  assert.equal(twin.individualProfiles, false);
  assert.equal(twin.protectedAttributeInference, false);
  assert.ok(QUEBEC_GROUP_FAMILIES.length >= 15);
});

test("marketplace fails closed until every production capability exists", () => {
  assert.equal(marketplaceCapabilityStatus({ identity: true, privateStorage: true }).status, "FAIL_CLOSED");
  assert.equal(marketplaceCapabilityStatus({ identity: true, privateStorage: true, malwareScanning: true, payments: true, entitlementLedger: true, taxConfig: true }).status, "LIVE_READY");
});
