"use strict";

export const HYPERMETA_FAMILIES = Object.freeze([
  ["genesis", "Meta Genesis"],
  ["destruction", "Meta Destruction"],
  ["selection", "Meta Selection"],
  ["representation", "Meta Representation"],
  ["questions", "Meta Questions"],
  ["residual", "Meta Residual"],
  ["causality", "Meta Causality"],
  ["scale", "Meta Scale"],
  ["proof", "Meta Proof"],
  ["uncertainty", "Meta Uncertainty"],
  ["experiment", "Meta Experiment"],
  ["simulation", "Meta Simulation"],
  ["memory", "Meta Memory"],
  ["compression", "Meta Compression"],
  ["routing", "Meta Routing"],
  ["resource", "Meta Resource"],
  ["architecture", "Meta Architecture"],
  ["interaction", "Meta Interaction"],
  ["media", "Meta Media"],
  ["collective", "Meta Collective"],
  ["economy", "Meta Economy"],
  ["github", "Meta GitHub"],
  ["research", "Meta Research"],
  ["safety", "Meta Safety"],
  ["temporal", "Meta Temporal"],
  ["adversary", "Meta Adversary"],
  ["learning", "Meta Learning"],
  ["synthesis", "Meta Synthesis"],
  ["self", "Meta Self"],
  ["evolution", "Meta Evolution"],
  ["regeneration", "Meta Regeneration"],
  ["zero", "Omega Zero"]
]);

export const HYPERMETA_OPERATORS = Object.freeze([
  "GO NULL", "GO MIN", "GO ANTI-ADD", "GO STRANGE", "GO IMPOSSIBLE", "GO RESIDUAL",
  "GO FALSIFY", "GO COMPRESS", "GO DESTROY", "GO REGENERATE", "GO TRANSFER", "GO ABLATE",
  "GO COUNTERFACTUAL", "GO MULTIREP", "GO GLOBALPASS", "GO MRU", "GO WAE", "GO OPTION",
  "GO OAK", "GO SELF", "GO EVOLVE", "GO MERGE", "GO FISSION", "GO HARVEST", "GO PROVE",
  "GO EXPERIMENT", "GO SIMULATE", "GO ROUTE", "GO CRYSTALLIZE", "GO SELF-DISTILL",
  "GO OBSOLETE", "GO ZERO"
]);

export const GO_METABOLISM = Object.freeze([
  { id: "pr-max", label: "GO PR MAX", role: "Materialize the minimum revolutionary unit as a reversible, evidence-carrying change." },
  { id: "tristan", label: "GO TRISTAN", role: "Explore questions, representations, residuals and candidate transformations." },
  { id: "tristan2", label: "GO TRISTAN2", role: "Improve the discovery process and compile reusable macros, contracts and routes." },
  { id: "tristan-squared", label: "GO TRISTAN²", role: "Generate bounded descendants, attack them, benchmark them and retain verified gain only." },
  { id: "multi-merge-max", label: "MULTI-MERGE-MAX", role: "Fuse only compatible capabilities whose combined GlobalPASS dominates isolated alternatives." }
]);

export const INTEGRATION_CONTRACTS = Object.freeze([
  {
    id: "simvis-r03",
    label: "ExecutableWorld + Publication Fabric + AudioVisualIR",
    pr: 477,
    status: "merged",
    statusLabel: "MERGED / CANONICAL INPUT",
    href: "https://github.com/Tristan-TM-Poly/TFUGA-AI7-TRISTAN2/pull/477",
    note: "Available on main. Web projections may consume these contracts; simulation and media representations remain evidence-bounded."
  },
  {
    id: "generative-closure-r03",
    label: "Generative Closure / Meta-Morphogenesis",
    pr: 470,
    status: "hold",
    statusLabel: "HOLD / DRAFT",
    href: "https://github.com/Tristan-TM-Poly/TFUGA-AI7-TRISTAN2/pull/470",
    note: "Candidate capability. Do not present its morphogenesis receipts as canonical until GlobalPASS promotion."
  },
  {
    id: "self-regenerating-hgfm-r02",
    label: "Self-Regenerating HGFM",
    pr: 467,
    status: "hold",
    statusLabel: "HOLD / DRAFT",
    href: "https://github.com/Tristan-TM-Poly/TFUGA-AI7-TRISTAN2/pull/467",
    note: "Candidate hypergraph kernel. The site may describe the proposal but must not imply canonical merge status."
  },
  {
    id: "uvtc-r02",
    label: "Universal Verified Transformation Compiler / UTIR",
    pr: 459,
    status: "hold",
    statusLabel: "HOLD / DRAFT",
    href: "https://github.com/Tristan-TM-Poly/TFUGA-AI7-TRISTAN2/pull/459",
    note: "Candidate transformation ABI. Its instructions create obligations; they do not fabricate proof, measurement or OAK completion."
  }
]);

export const OAK_INVARIANTS = Object.freeze([
  "simulation != proof",
  "visualization != truth",
  "publication != validation",
  "reproducibility != correctness",
  "representation != truth",
  "program != execution",
  "technical capability != epistemic authority",
  "LocalPASS != GlobalPASS"
]);

export function generateHyperMetaCells() {
  const cells = [];
  for (let familyIndex = 0; familyIndex < HYPERMETA_FAMILIES.length; familyIndex += 1) {
    const [familyId, familyLabel] = HYPERMETA_FAMILIES[familyIndex];
    for (let operatorIndex = 0; operatorIndex < HYPERMETA_OPERATORS.length; operatorIndex += 1) {
      const operator = HYPERMETA_OPERATORS[operatorIndex];
      const ordinal = familyIndex * HYPERMETA_OPERATORS.length + operatorIndex + 1;
      cells.push(Object.freeze({
        id: `hm-${String(ordinal).padStart(4, "0")}`,
        ordinal,
        familyId,
        familyLabel,
        operator,
        label: `${familyLabel} × ${operator}`,
        lifecycle: operator === "GO ZERO" || operator === "GO OBSOLETE" ? "destruction-candidate" : "candidate"
      }));
    }
  }
  return Object.freeze(cells);
}

export const HYPERMETA_CELLS = generateHyperMetaCells();

export function filterHyperMetaCells({ query = "", family = "all", operator = "all" } = {}) {
  const normalized = String(query).trim().toLocaleLowerCase("fr");
  return HYPERMETA_CELLS.filter((cell) => {
    if (family !== "all" && cell.familyId !== family) return false;
    if (operator !== "all" && cell.operator !== operator) return false;
    if (!normalized) return true;
    return `${cell.id} ${cell.familyLabel} ${cell.operator} ${cell.label}`.toLocaleLowerCase("fr").includes(normalized);
  });
}

export function hyperMetaKernelReceipt() {
  const expected = HYPERMETA_FAMILIES.length * HYPERMETA_OPERATORS.length;
  return Object.freeze({
    schema: "tristan.hypermeta-kernel/0.1",
    families: HYPERMETA_FAMILIES.length,
    operators: HYPERMETA_OPERATORS.length,
    generatedCells: HYPERMETA_CELLS.length,
    expectedCells: expected,
    deterministicClosure: HYPERMETA_CELLS.length === expected,
    claimBoundary: "1024 generated instruction cells are a design/search space, not 1024 verified scientific results or persistent modules."
  });
}
