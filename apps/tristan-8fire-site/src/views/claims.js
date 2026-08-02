"use strict";

import { badge, element, emptyState, link, sectionHeader } from "../ui.js";
import { exportClaimsCsv, exportJson } from "../exporters.js";

function select(name, label, values, selected) {
  return element("label", {}, [
    element("span", { text: label }),
    element("select", { name }, [
      element("option", { value: "", text: `Tous — ${label.toLowerCase()}` }),
      ...values.map((value) => element("option", { value, text: value, selected: value === selected }))
    ])
  ]);
}

function claimRow(claim, theory) {
  const tone = claim.status === "guardrail" ? "warning" : claim.status === "planned" ? "neutral" : "success";
  return element("article", { className: "claim-ledger-card" }, [
    element("header", { className: "claim-ledger-header" }, [
      element("div", {}, [badge(claim.kind, "neutral"), badge(claim.status, tone), badge(claim.epistemic_level, "neutral")]),
      link(claim.id, `#/claim/${encodeURIComponent(claim.id)}`, "mono-link")
    ]),
    element("h2", {}, [link(claim.title, `#/claim/${encodeURIComponent(claim.id)}`)]),
    theory ? element("p", { className: "claim-theory" }, [link(`${theory.symbol} — ${theory.title}`, `#/theory/${encodeURIComponent(theory.id)}`)]) : null,
    element("p", { className: "claim-statement", text: claim.statement }),
    element("div", { className: "claim-columns" }, [
      element("div", {}, [element("h3", { text: "Limite / falsification" }), element("p", { text: claim.falsification_or_limit })]),
      element("div", {}, [element("h3", { text: "Prochain test" }), element("p", { text: claim.next_test })])
    ]),
    element("details", {}, [
      element("summary", { text: "Support, contre-hypothèses et risques" }),
      element("h3", { text: "Support déclaré" }),
      element("ul", {}, (claim.support || []).map((support) => element("li", {}, [element("code", { text: support.path }), ` — ${support.note}`]))),
      element("h3", { text: "Contre-hypothèses" }),
      element("ul", {}, (claim.counter_hypotheses || []).map((item) => element("li", { text: item }))),
      element("div", { className: "tag-cloud" }, (claim.risk_tags || []).map((risk) => badge(risk, "danger")))
    ])
  ]);
}

export function renderClaims({ store, route }) {
  const query = route.query.get("q") || "";
  const theory = route.query.get("theory") || "";
  const kind = route.query.get("kind") || "";
  const status = route.query.get("status") || "";
  const risk = route.query.get("risk") || "";
  const results = store.searchClaims(query, { theory, kind, status, risk });
  const stats = store.statistics();
  const root = element("div", { className: "view claims-view" });
  root.append(sectionHeader("Claim–Evidence Ledger", "133 affirmations sans effacement de l’incertitude", "Chaque entrée expose son statut, son niveau épistémique, son support déclaré, ses contre-hypothèses, sa limite et son prochain test."));

  const form = element("form", { className: "filter-console claims-filter", role: "search" }, [
    element("label", {}, [element("span", { text: "Recherche" }), element("input", { type: "search", name: "q", value: query, placeholder: "Claim, limite, test, risque…" })]),
    select("kind", "Type", stats.claimKinds.map(([value]) => value), kind),
    select("status", "Statut", stats.claimStatuses.map(([value]) => value), status),
    select("risk", "Risque", stats.risks.map(([value]) => value), risk),
    element("input", { type: "hidden", name: "theory", value: theory }),
    element("button", { type: "submit", className: "button primary", text: "Appliquer" }),
    link("Réinitialiser", "#/claims", "button secondary")
  ]);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const params = new URLSearchParams();
    for (const [key, value] of new FormData(form).entries()) if (String(value).trim()) params.set(key, String(value).trim());
    window.location.hash = `#/claims${params.size ? `?${params}` : ""}`;
  });
  root.append(form);

  if (theory) {
    const selected = store.getTheory(theory);
    if (selected) root.append(element("p", { className: "active-filter" }, ["Filtre actif : ", link(selected.symbol, `#/theory/${encodeURIComponent(selected.id)}`), " — ", selected.title]));
  }
  root.append(element("div", { className: "results-toolbar" }, [
    element("p", { text: `${results.length} claim${results.length > 1 ? "s" : ""} affiché${results.length > 1 ? "s" : ""}.` }),
    element("div", { className: "toolbar-actions" }, [
      element("button", { className: "button secondary", text: "Exporter CSV", onclick: () => exportClaimsCsv(results.map(({ item }) => item)) }),
      element("button", { className: "button secondary", text: "Exporter JSON", onclick: () => exportJson("tristan-web-os-claims-filtered.json", { claims: results.map(({ item }) => item) }) })
    ])
  ]));
  if (!results.length) root.append(emptyState("Aucun claim", "Aucune affirmation ne correspond à ces filtres."));
  else root.append(element("section", { className: "claim-ledger" }, results.map(({ item }) => claimRow(item, store.getTheory(item.theory_id)))));
  return root;
}

export function renderClaim({ store, route }) {
  const claim = store.getClaim(route.params.id);
  if (!claim) return emptyState("Claim introuvable", "L’identifiant demandé n’existe pas dans le registre public.");
  const theory = store.getTheory(claim.theory_id);
  const root = element("div", { className: "view claim-detail-view" });
  root.append(sectionHeader(claim.id, claim.title, claim.statement));
  root.append(element("div", { className: "theory-actions" }, [link("← Ledger", "#/claims", "button secondary"), theory ? link("Théorie source", `#/theory/${encodeURIComponent(theory.id)}`, "button primary") : null]));
  root.append(claimRow(claim, theory));
  root.append(element("section", { className: "panel" }, [
    element("h2", { text: "Contrat épistémique" }),
    element("dl", { className: "definition-list" }, [
      element("div", {}, [element("dt", { text: "Statut" }), element("dd", { text: claim.status })]),
      element("div", {}, [element("dt", { text: "Niveau" }), element("dd", { text: claim.epistemic_level })]),
      element("div", {}, [element("dt", { text: "Confiance" }), element("dd", { text: claim.confidence_label })]),
      element("div", {}, [element("dt", { text: "Portée" }), element("dd", { text: claim.publication_scope })]),
      element("div", {}, [element("dt", { text: "Promotion automatique" }), element("dd", { text: claim.automatic_promotion ? "autorisée" : "interdite" })])
    ])
  ]));
  return root;
}
