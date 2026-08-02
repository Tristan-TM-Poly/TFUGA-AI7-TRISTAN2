"use strict";

import { badge, element, emptyState, link, oakBars, publicationGate, sectionHeader } from "../ui.js";
import { exportTheoriesCsv, exportJson } from "../exporters.js";

function options(values, selected, allLabel) {
  return [element("option", { value: "", text: allLabel })].concat(values.map((value) =>
    element("option", { value, text: value, selected: value === selected })
  ));
}

function theoryCard(theory) {
  return element("article", { className: "theory-card advanced-card" }, [
    element("div", { className: "card-topline" }, [
      link(theory.symbol, `#/theory/${encodeURIComponent(theory.id)}`, "symbol-link"),
      badge(theory.maturity, theory.maturity === "prototype" ? "success" : theory.maturity === "hypothèse" ? "danger" : "warning")
    ]),
    element("h2", {}, [link(theory.title, `#/theory/${encodeURIComponent(theory.id)}`)]),
    element("p", { className: "summary", text: theory.summary }),
    element("div", { className: "tag-cloud" }, (theory.domains || []).map((domain) => badge(domain, "neutral"))),
    element("dl", { className: "compact-facts" }, [
      element("div", {}, [element("dt", { text: "Preuve" }), element("dd", { text: theory.evidence })]),
      element("div", {}, [element("dt", { text: "Famille" }), element("dd", { text: theory.family })]),
      element("div", {}, [element("dt", { text: "Claims" }), element("dd", { text: theory.claims_count })]),
      element("div", {}, [element("dt", { text: "Artefacts" }), element("dd", { text: theory.artifacts })])
    ]),
    oakBars(theory.oak),
    element("details", {}, [
      element("summary", { text: "État OAK et prochaine action" }),
      element("p", { text: theory.status_note }),
      element("p", {}, [element("strong", { text: "Action : " }), theory.next_action]),
      publicationGate(theory.publication)
    ])
  ]);
}

export function renderAtlas({ store, route }) {
  const query = route.query.get("q") || "";
  const maturity = route.query.get("maturity") || "";
  const family = route.query.get("family") || "";
  const domain = route.query.get("domain") || "";
  const risk = route.query.get("risk") || "";
  const results = store.searchTheories(query, { maturity, family, domain, risk });
  const stats = store.statistics();
  const root = element("div", { className: "view atlas-view" });
  root.append(sectionHeader("Atlas", "44 branches, une interface de vérification", "Filtre par maturité, famille, domaine ou risque. Chaque carte conserve son état, sa limite, ses portes de publication et sa prochaine expérience."));

  const form = element("form", { className: "filter-console", role: "search" });
  const search = element("input", { type: "search", name: "q", value: query, placeholder: "Rechercher une théorie, un domaine, un risque…", "aria-label": "Recherche dans les théories" });
  const maturitySelect = element("select", { name: "maturity", "aria-label": "Filtrer par maturité" }, options(stats.maturity.map(([value]) => value), maturity, "Toutes les maturités"));
  const familySelect = element("select", { name: "family", "aria-label": "Filtrer par famille" }, options(stats.families.map(([value]) => value), family, "Toutes les familles"));
  const domainSelect = element("select", { name: "domain", "aria-label": "Filtrer par domaine" }, options(stats.domains.map(([value]) => value), domain, "Tous les domaines"));
  const riskSelect = element("select", { name: "risk", "aria-label": "Filtrer par risque" }, options(stats.risks.map(([value]) => value), risk, "Tous les risques"));
  form.append(search, maturitySelect, familySelect, domainSelect, riskSelect,
    element("button", { type: "submit", className: "button primary", text: "Appliquer" }),
    link("Réinitialiser", "#/atlas", "button secondary")
  );
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const params = new URLSearchParams();
    for (const [key, value] of data.entries()) if (String(value).trim()) params.set(key, String(value).trim());
    window.location.hash = `#/atlas${params.size ? `?${params}` : ""}`;
  });
  root.append(form);

  root.append(element("div", { className: "results-toolbar" }, [
    element("p", { text: `${results.length} théorie${results.length > 1 ? "s" : ""} affichée${results.length > 1 ? "s" : ""}.` }),
    element("div", { className: "toolbar-actions" }, [
      element("button", { className: "button secondary", text: "Exporter CSV", onclick: () => exportTheoriesCsv(results.map(({ item }) => item)) }),
      element("button", { className: "button secondary", text: "Exporter JSON", onclick: () => exportJson("tristan-web-os-theories-filtered.json", { theories: results.map(({ item }) => item) }) })
    ])
  ]));

  if (!results.length) root.append(emptyState("Aucun résultat", "Réduis le nombre de filtres ou essaie un terme plus général."));
  else root.append(element("section", { className: "atlas-grid" }, results.map(({ item }) => theoryCard(item))));
  return root;
}
