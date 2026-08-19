"use strict";

import {
  GO_METABOLISM,
  HYPERMETA_CELLS,
  HYPERMETA_FAMILIES,
  HYPERMETA_OPERATORS,
  INTEGRATION_CONTRACTS,
  OAK_INVARIANTS,
  filterHyperMetaCells,
  hyperMetaKernelReceipt
} from "../hypermeta-kernel.js";
import {
  compileMorphogeneticWorkspace,
  createTransformationField
} from "../morphogenetic-field.js";

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "className") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key.startsWith("data-")) node.setAttribute(key, value);
    else if (value !== undefined && value !== null) node.setAttribute(key, value);
  }
  for (const child of Array.isArray(children) ? children : [children]) if (child) node.append(child);
  return node;
}

function metric(label, value, note) {
  return el("article", { className: "hm-metric" }, [
    el("strong", { text: value }),
    el("span", { text: label }),
    note ? el("small", { text: note }) : null
  ]);
}

function renderMetabolism() {
  const wrap = el("div", { className: "hm-metabolism" });
  const detail = el("div", { className: "hm-command-detail" });
  const controls = el("div", { className: "hm-command-grid", role: "list" });

  function select(command, button) {
    for (const candidate of controls.querySelectorAll("button")) candidate.classList.toggle("is-selected", candidate === button);
    detail.replaceChildren(
      el("p", { className: "eyebrow", text: command.label }),
      el("p", { text: command.role }),
      el("small", { text: "Cette interaction explique un régime d'architecture; elle n'exécute aucune action GitHub ou externe." })
    );
  }

  GO_METABOLISM.forEach((command, index) => {
    const button = el("button", { type: "button", className: "hm-command", text: command.label, role: "listitem" });
    button.addEventListener("click", () => select(command, button));
    controls.append(button);
    if (index === 0) queueMicrotask(() => select(command, button));
  });

  wrap.append(controls, detail);
  return wrap;
}

function renderContracts() {
  const grid = el("div", { className: "hm-contract-grid" });
  for (const contract of INTEGRATION_CONTRACTS) {
    grid.append(el("article", { className: `hm-contract ${contract.status}` }, [
      el("div", { className: "hm-contract-head" }, [
        el("span", { className: `hm-status ${contract.status}`, text: contract.statusLabel }),
        el("a", { href: contract.href, target: "_blank", rel: "noreferrer", text: `PR #${contract.pr}` })
      ]),
      el("h3", { text: contract.label }),
      el("p", { text: contract.note })
    ]));
  }
  return grid;
}

function renderMorphogeneticCompiler() {
  const section = el("section", { className: "hm-section" });
  const intent = el("input", { type: "text", value: "Tester une théorie avec le minimum de complexité persistante", "aria-label": "Intention à compiler" });
  const objectType = el("select", { "aria-label": "Type d'objet" });
  for (const type of ["theory", "claim", "equation", "dataset", "simulation", "experiment", "artifact", "question"]) objectType.append(el("option", { value: type, text: type }));
  const operator = el("select", { "aria-label": "Opérateur principal" });
  for (const item of HYPERMETA_OPERATORS) operator.append(el("option", { value: item, text: item }));
  operator.value = "GO OAK";
  const depth = el("input", { type: "number", min: "0", max: "12", step: "1", value: "1", "aria-label": "MetaDepth" });
  const verifiedGain = el("input", { type: "number", min: "0", step: "0.25", value: "0.5", "aria-label": "Gain vérifié" });
  const novelCoverage = el("input", { type: "number", min: "0", step: "0.25", value: "0.5", "aria-label": "Couverture nouvelle" });
  const reuseGain = el("input", { type: "number", min: "0", step: "0.25", value: "0.5", "aria-label": "Gain de réutilisation" });
  const complexityDebt = el("input", { type: "number", min: "0", step: "0.25", value: "0.5", "aria-label": "Dette de complexité" });
  const output = el("div", { className: "hm-command-detail", "aria-live": "polite" });

  function labeled(label, control) {
    return el("label", {}, [el("small", { text: label }), control]);
  }

  function compile() {
    const scores = {
      verifiedGain: Number(verifiedGain.value),
      novelCoverage: Number(novelCoverage.value),
      reuseGain: Number(reuseGain.value),
      complexityDebt: Number(complexityDebt.value)
    };
    const workspace = compileMorphogeneticWorkspace({
      intent: intent.value,
      objectType: objectType.value,
      operator: operator.value,
      metaDepth: Number(depth.value),
      scores
    });
    const localField = createTransformationField({
      families: [[objectType.value, objectType.value]],
      operators: [operator.value],
      objectType: objectType.value,
      namespace: "local"
    });
    output.replaceChildren(
      el("p", { className: "eyebrow", text: `MATERIALIZATION · ${workspace.materialization}` }),
      el("p", { text: workspace.intent }),
      el("code", { text: `${localField.cells[0].id} · ${localField.cells[0].familyLabel} × ${localField.cells[0].operator}` }),
      el("p", { text: `Résidus initiaux: ${workspace.residualField.count} · ${workspace.residualField.types.join(", ") || "aucun"}` }),
      el("p", { text: `ANTI-ADD: ${workspace.antiAdd.decision} · net ${workspace.antiAdd.net.toFixed(2)} · MetaDepth ${workspace.metaDepthGate.allowed ? "PASS" : "HOLD"} (${workspace.metaDepthGate.verifiedGain.toFixed(2)} / ${workspace.metaDepthGate.requiredGain.toFixed(2)})` }),
      el("p", { text: `Obligations: ${workspace.obligations.join(", ") || "aucune obligation spéciale ajoutée"}` }),
      el("small", { text: workspace.boundary })
    );
  }

  const controls = el("div", { className: "hm-filters" }, [
    labeled("Intent", intent),
    labeled("Objet", objectType),
    labeled("Opérateur", operator),
    labeled("MetaDepth", depth),
    labeled("Verified gain", verifiedGain),
    labeled("Novel coverage", novelCoverage),
    labeled("Reuse gain", reuseGain),
    labeled("Complexity debt", complexityDebt)
  ]);
  for (const control of [intent, objectType, operator, depth, verifiedGain, novelCoverage, reuseGain, complexityDebt]) control.addEventListener(control === intent ? "input" : "change", compile);
  compile();

  section.append(
    el("div", { className: "hm-section-head" }, [
      el("div", {}, [
        el("p", { className: "eyebrow", text: "Ω-VERIFIED-MORPHOGENETIC-CAPABILITY-FIELD" }),
        el("h2", { text: "Intent → EpistemicCapsule → ResidualField → ANTI-ADD" })
      ]),
      el("span", { className: "hm-status hold", text: "REVERSIBLE COMPILER" })
    ]),
    el("p", { className: "fineprint", text: "Cette couche ne crée ni page persistante, ni preuve, ni permission. Elle décide d'abord REUSE / HOLD / CANDIDATE sous un gate de profondeur méta." }),
    controls,
    output
  );
  return section;
}

function renderMatrix() {
  const section = el("section", { className: "hm-section" });
  const search = el("input", { type: "search", placeholder: "Rechercher prove, media, residual…", "aria-label": "Rechercher les cellules Hyper-Meta" });
  const family = el("select", { "aria-label": "Filtrer par famille" }, [el("option", { value: "all", text: "Toutes les familles" })]);
  const operator = el("select", { "aria-label": "Filtrer par opérateur" }, [el("option", { value: "all", text: "Tous les opérateurs" })]);
  const counter = el("strong", { text: "1024" });
  const grid = el("div", { className: "hm-grid" });

  for (const [id, label] of HYPERMETA_FAMILIES) family.append(el("option", { value: id, text: label }));
  for (const item of HYPERMETA_OPERATORS) operator.append(el("option", { value: item, text: item }));

  function paint() {
    const cells = filterHyperMetaCells({ query: search.value, family: family.value, operator: operator.value });
    counter.textContent = String(cells.length);
    grid.replaceChildren();
    const fragment = document.createDocumentFragment();
    for (const cell of cells) {
      fragment.append(el("article", { className: "hm-cell", tabindex: "0" }, [
        el("div", { className: "hm-cell-top" }, [
          el("code", { text: cell.id.toUpperCase() }),
          el("span", { text: `#${cell.ordinal}` })
        ]),
        el("h3", { text: cell.familyLabel }),
        el("p", { text: cell.operator }),
        el("small", { text: cell.lifecycle })
      ]));
    }
    grid.append(fragment);
  }

  [search, family, operator].forEach((control) => control.addEventListener(control === search ? "input" : "change", paint));
  paint();

  section.append(
    el("div", { className: "hm-section-head" }, [
      el("div", {}, [el("p", { className: "eyebrow", text: "Ω-HYPERMETA-1024-T · BOOTSTRAP GRAMMAR" }), el("h2", { text: "Matrice 32 × 32 compressible" })]),
      el("p", { className: "hm-count" }, [counter, document.createTextNode(" cellules visibles")])
    ]),
    el("p", { className: "fineprint", text: "32×32 est maintenant un bootstrap mutable. Le noyau accepte des ensembles de familles et d'opérateurs plus petits ou plus grands; toute promotion reste soumise à OAK et à la dette de complexité." }),
    el("div", { className: "hm-filters" }, [search, family, operator]),
    grid
  );
  return section;
}

export function renderHyperMeta() {
  const receipt = hyperMetaKernelReceipt();
  const root = el("div", { className: "hm-page" });

  root.append(
    el("section", { className: "hm-hero" }, [
      el("p", { className: "eyebrow", text: "GO PR MAX × GO TRISTAN × GO TRISTAN2 × GO TRISTAN² × MULTI-MERGE-MAX" }),
      el("h1", { text: "Hyper-Meta Lab" }),
      el("p", { className: "hm-lede", text: "Un champ morphogénétique de transformations candidates. Le 32×32 n'est plus une ontologie fixe: c'est une grammaire bootstrap que le système peut compresser ou étendre sous vérification." }),
      el("code", { className: "hm-equation", text: "Intent → Capsule → Residual → Transform → Attack → Verify → ANTI-ADD → Materialize / Hold / Reuse" })
    ]),
    el("section", { className: "hm-metrics" }, [
      metric("familles bootstrap", receipt.families, "grammaire mutable"),
      metric("opérateurs bootstrap", receipt.operators, "ISA Ω-ZERO mutable"),
      metric("cellules bootstrap", receipt.generatedCells, receipt.deterministicClosure ? "fermeture déterministe PASS" : "closure FAIL"),
      metric("grammaire dynamique", receipt.dynamicGrammar ? "ON" : "OFF", "32×32 n'est pas irréductible")
    ]),
    el("section", { className: "hm-section" }, [
      el("div", { className: "hm-section-head" }, [
        el("div", {}, [el("p", { className: "eyebrow", text: "MÉTABOLISME UNIFIÉ" }), el("h2", { text: "Cinq régimes, une seule boucle" })]),
        el("span", { className: "hm-status hold", text: "INTERACTIVE MODEL" })
      ]),
      renderMetabolism()
    ]),
    renderMorphogeneticCompiler(),
    el("section", { className: "hm-section" }, [
      el("div", { className: "hm-section-head" }, [
        el("div", {}, [el("p", { className: "eyebrow", text: "GLOBALPASS SNAPSHOT · 2026-08-18" }), el("h2", { text: "Contrats d'intégration GitHub" })])
      ]),
      renderContracts()
    ]),
    renderMatrix(),
    el("section", { className: "hm-section hm-compiler" }, [
      el("div", {}, [
        el("p", { className: "eyebrow", text: "KNOWLEDGE PROGRAM → PORTABLE CAPSULE" }),
        el("h2", { text: "Compilation vers les projections exécutables" }),
        el("pre", {}, [el("code", { text: "Intent\n  ↓\nEpistemicCapsule\n  ↓\nTransformationField\n  ↓\nInteractionProgram\n  ↓\nExecutableWorld / Proof / Experiment\n  ↓\nPublicationBundle\n  ├─ Web\n  ├─ GitHub\n  └─ Media" })])
      ]),
      el("div", {}, [
        el("h3", { text: "OAK invariants" }),
        el("ul", { className: "hm-invariants" }, OAK_INVARIANTS.map((item) => el("li", { text: item }))),
        el("p", { className: "fineprint", text: receipt.claimBoundary })
      ])
    ])
  );

  return root;
}

export { HYPERMETA_CELLS };
