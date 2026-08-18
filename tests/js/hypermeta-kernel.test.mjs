import assert from "node:assert/strict";
import test from "node:test";

import {
  GO_METABOLISM,
  HYPERMETA_CELLS,
  HYPERMETA_FAMILIES,
  HYPERMETA_OPERATORS,
  INTEGRATION_CONTRACTS,
  filterHyperMetaCells,
  hyperMetaKernelReceipt
} from "../../apps/tristan-8fire-site/src/hypermeta-kernel.js";

test("HyperMeta kernel closes deterministically at 32 x 32 = 1024 cells", () => {
  const receipt = hyperMetaKernelReceipt();
  assert.equal(HYPERMETA_FAMILIES.length, 32);
  assert.equal(HYPERMETA_OPERATORS.length, 32);
  assert.equal(HYPERMETA_CELLS.length, 1024);
  assert.equal(receipt.expectedCells, 1024);
  assert.equal(receipt.deterministicClosure, true);
});

test("HyperMeta cell ids and ordinals are unique and contiguous", () => {
  assert.equal(new Set(HYPERMETA_CELLS.map((cell) => cell.id)).size, 1024);
  assert.deepEqual(HYPERMETA_CELLS.map((cell) => cell.ordinal), Array.from({ length: 1024 }, (_, index) => index + 1));
  assert.equal(HYPERMETA_CELLS[0].id, "hm-0001");
  assert.equal(HYPERMETA_CELLS.at(-1).id, "hm-1024");
});

test("filters preserve family and operator contracts", () => {
  const proof = filterHyperMetaCells({ family: "proof" });
  const globalPass = filterHyperMetaCells({ operator: "GO GLOBALPASS" });
  const mediaOak = filterHyperMetaCells({ query: "media go oak" });
  assert.equal(proof.length, 32);
  assert.equal(globalPass.length, 32);
  assert.equal(mediaOak.length, 1);
  assert.equal(mediaOak[0].familyId, "media");
  assert.equal(mediaOak[0].operator, "GO OAK");
});

test("unified metabolism exposes exactly the requested five regimes", () => {
  assert.deepEqual(GO_METABOLISM.map((item) => item.label), [
    "GO PR MAX",
    "GO TRISTAN",
    "GO TRISTAN2",
    "GO TRISTAN²",
    "MULTI-MERGE-MAX"
  ]);
});

test("integration snapshot fails closed for unmerged draft capabilities", () => {
  const merged = INTEGRATION_CONTRACTS.filter((contract) => contract.status === "merged");
  const hold = INTEGRATION_CONTRACTS.filter((contract) => contract.status === "hold");
  assert.deepEqual(merged.map((contract) => contract.pr), [477]);
  assert.deepEqual(hold.map((contract) => contract.pr).sort((a, b) => a - b), [459, 467, 470]);
});
