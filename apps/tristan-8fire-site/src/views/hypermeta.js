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
      el("div", {}, [el("p", { className: "eyebrow", text: "Ω-HYPERMETA-1024-T" }), el("h2", { text: "Matrice 32 × 32" })]),
      el("p", { className: "hm-count" }, [counter, document.createTextNode(" cellules visibles")])
    ]),
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
      el("p", { className: "hm-lede", text: "Un espace interactif de transformations candidates. Le noyau génère 1024 cellules sans créer 1024 modules persistants." }),
      el("code", { className: "hm-equation", text: "Intent → Represent → Generate → Attack → Simulate → Prove/Measure → OAK → Compress → Regenerate" })
    ]),
    el("section", { className: "hm-metrics" }, [
      metric("familles", receipt.families, "domaines Hyper-Meta"),
      metric("opérateurs", receipt.operators, "ISA Ω-ZERO"),
      metric("cellules", receipt.generatedCells, receipt.deterministicClosure ? "fermeture déterministe PASS" : "closure FAIL"),
      metric("modules imposés", "0", "les cellules restent candidates")
    ]),
    el("section", { className: "hm-section" }, [
      el("div", { className: "hm-section-head" }, [
        el("div", {}, [el("p", { className: "eyebrow", text: "MÉTABOLISME UNIFIÉ" }), el("h2", { text: "Cinq régimes, une seule boucle" })]),
        el("span", { className: "hm-status hold", text: "INTERACTIVE MODEL" })
      ]),
      renderMetabolism()
    ]),
    el("section", { className: "hm-section" }, [
      el("div", { className: "hm-section-head" }, [
        el("div", {}, [el("p", { className: "eyebrow", text: "GLOBALPASS SNAPSHOT · 2026-08-18" }), el("h2", { text: "Contrats d'intégration GitHub" })])
      ]),
      renderContracts()
    ]),
    renderMatrix(),
    el("section", { className: "hm-section hm-compiler" }, [
      el("div", {}, [
        el("p", { className: "eyebrow", text: "THEORY → INTERACTIONPROGRAM" }),
        el("h2", { text: "Compilation vers le Web exécutable" }),
        el("pre", {}, [el("code", { text: "TheorySpec\n  ↓\nInteractionProgram\n  ↓\nExecutableWorld\n  ↓\nSimCapsule\n  ↓\nPublicationBundle\n  ├─ Web\n  ├─ GitHub\n  └─ Media" })])
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
