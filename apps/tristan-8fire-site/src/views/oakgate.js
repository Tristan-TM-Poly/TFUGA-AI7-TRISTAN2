"use strict";

import { evaluateOakGate, OAK_CRITERIA, PUBLICATION_GATES, prefillClaim, prefillTheory } from "../oak-engine.js";
import { exportJson } from "../exporters.js";
import { badge, element, formatPercent, link, sectionHeader } from "../ui.js";

function objectOptions(store) {
  const theories = store.theories
    .slice()
    .sort((a, b) => a.title.localeCompare(b.title, "fr"))
    .map((theory) => ({ value: `theory:${theory.id}`, label: `${theory.symbol} — ${theory.title}` }));
  const claims = store.claims
    .slice()
    .sort((a, b) => a.id.localeCompare(b.id, "fr"))
    .map((claim) => ({ value: `claim:${claim.id}`, label: `${claim.id} — ${claim.title}` }));
  return [
    { group: "Théories", items: theories },
    { group: "Claims", items: claims }
  ];
}

function currentInput(store, value) {
  const [type, id] = String(value || "").split(":", 2);
  if (type === "claim") {
    const claim = store.getClaim(id);
    if (!claim) return null;
    return prefillClaim(claim, store.getTheory(claim.theory_id));
  }
  const theory = store.getTheory(id) || store.theories[0];
  return theory ? prefillTheory(theory, store.getClaimsForTheory(theory.id)) : null;
}

function checkbox(definition, checked, namespace) {
  const id = `${namespace}-${definition.id}`;
  return element("label", { className: "oak-check" }, [
    element("input", { type: "checkbox", id, name: definition.id, checked }),
    element("span", {}, [
      element("strong", { text: definition.label }),
      definition.category ? element("small", { text: `${definition.category}${definition.hard ? " · bloqueur" : ""}` }) : null
    ])
  ]);
}

function readForm(form, base) {
  const data = new FormData(form);
  return {
    ...base,
    criteria: Object.fromEntries(OAK_CRITERIA.map((criterion) => [criterion.id, data.has(criterion.id)])),
    gates: Object.fromEntries(PUBLICATION_GATES.map((gate) => [gate.id, data.has(gate.id)])),
    automatic_promotion: data.has("automatic_promotion")
  };
}

function reportPanel(report) {
  const tone = report.status === "human-review-candidate" ? "success" : report.status === "blocked" ? "danger" : "warning";
  return element("section", { className: "oak-report panel" }, [
    element("header", { className: "panel-header" }, [
      element("div", {}, [element("p", { className: "eyebrow", text: "Résultat local" }), element("h2", { text: report.object.title })]),
      badge(report.status, tone)
    ]),
    element("div", { className: "oak-report-metrics" }, [
      element("article", {}, [element("strong", { text: formatPercent(report.score) }), element("span", { text: "complétude pondérée" })]),
      element("article", {}, [element("strong", { text: formatPercent(report.confidence_debt) }), element("span", { text: "dette de confiance" })]),
      element("article", {}, [element("strong", { text: report.blockers.length }), element("span", { text: "bloqueurs" })]),
      element("article", {}, [element("strong", { text: report.missing_criteria.length }), element("span", { text: "critères manquants" })])
    ]),
    element("h3", { text: "Bloqueurs" }),
    report.blockers.length
      ? element("ul", { className: "blocker-list" }, report.blockers.map((item) => element("li", {}, [element("code", { text: item.code }), ` — ${item.message}`])))
      : element("p", { className: "success-callout", text: "Aucun bloqueur structurel détecté. Une révision humaine reste obligatoire." }),
    element("h3", { text: "Actions suivantes" }),
    report.next_actions.length
      ? element("ol", {}, report.next_actions.map((item) => element("li", { text: item })))
      : element("p", { text: "Documenter la revue humaine et lier les résultats exécutés avant toute promotion." }),
    element("p", { className: "fine-print", text: report.epistemic_boundary }),
    element("button", { className: "button primary", type: "button", text: "Exporter le paquet OAK JSON", onclick: () => exportJson(`oakgate-${report.object.id}.json`, report) })
  ]);
}

export function renderOakGate({ store, route }) {
  const defaultValue = route.query.get("object") || `theory:${store.theories[0]?.id || ""}`;
  let base = currentInput(store, defaultValue);
  let lastReport = base ? evaluateOakGate(base) : null;
  const root = element("div", { className: "view oakgate-view" });
  root.append(sectionHeader("OAKGate Lab", "Auditer sans certifier", "Le laboratoire classe la préparation documentaire et expérimentale d’une théorie ou d’un claim. Il ne valide ni la science, ni la sécurité, ni l’IP, ni le marché."));

  const form = element("form", { className: "oakgate-form panel" });
  const selector = element("select", { name: "object", "aria-label": "Objet à auditer" });
  for (const group of objectOptions(store)) {
    const optgroup = element("optgroup", { label: group.group });
    for (const option of group.items) optgroup.append(element("option", { value: option.value, text: option.label, selected: option.value === defaultValue }));
    selector.append(optgroup);
  }
  const criteriaGrid = element("div", { className: "oak-check-grid" });
  const gatesGrid = element("div", { className: "oak-check-grid gate-check-grid" });
  const automatic = checkbox({ id: "automatic_promotion", label: "Promotion automatique", category: "interdite", hard: true }, false, "governance");

  function rebuild() {
    base = currentInput(store, selector.value);
    criteriaGrid.replaceChildren(...OAK_CRITERIA.map((criterion) => checkbox(criterion, Boolean(base?.criteria?.[criterion.id]), "criterion")));
    gatesGrid.replaceChildren(...PUBLICATION_GATES.map((gate) => checkbox(gate, Boolean(base?.gates?.[gate.id]), "gate")));
    automatic.querySelector("input").checked = Boolean(base?.automatic_promotion);
  }

  selector.addEventListener("change", () => {
    rebuild();
    const params = new URLSearchParams({ object: selector.value });
    history.replaceState(null, "", `#/oakgate?${params}`);
  });

  form.append(
    element("label", { className: "oak-object-selector" }, [element("span", { text: "Objet public" }), selector]),
    element("fieldset", {}, [element("legend", { text: "Critères de préparation" }), criteriaGrid]),
    element("fieldset", {}, [element("legend", { text: "Portes de publication" }), gatesGrid]),
    element("fieldset", { className: "automatic-promotion-field" }, [element("legend", { text: "Gouvernance" }), automatic]),
    element("div", { className: "theory-actions" }, [
      element("button", { className: "button primary", type: "submit", text: "Évaluer localement" }),
      link("Voir la gouvernance", "#/about", "button secondary")
    ])
  );
  rebuild();

  const reportHost = element("div", { className: "oak-report-host" });
  if (lastReport) reportHost.append(reportPanel(lastReport));
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!base) return;
    lastReport = evaluateOakGate(readForm(form, base));
    reportHost.replaceChildren(reportPanel(lastReport));
  });
  root.append(form, reportHost);
  return root;
}
