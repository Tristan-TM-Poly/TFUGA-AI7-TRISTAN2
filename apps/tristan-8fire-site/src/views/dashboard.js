"use strict";

import { badge, element, formatNumber, formatPercent, link, metric, oakBars, sectionHeader, table } from "../ui.js";

function distribution(entries, total) {
  return element("div", { className: "distribution" }, entries.map(([label, count]) =>
    element("div", { className: "distribution-row" }, [
      element("div", { className: "distribution-label" }, [element("span", { text: label }), element("strong", { text: count })]),
      element("span", { className: "distribution-track", "aria-hidden": "true" }, [element("i", { style: `width:${Math.max(3, Math.round((count / total) * 100))}%` })])
    ])
  ));
}

export function renderDashboard({ store }) {
  const stats = store.statistics();
  const connected = store.mostConnected(8);
  const roadmap = store.roadmap().slice(0, 8);
  const root = element("div", { className: "view dashboard-view" });
  root.append(sectionHeader(
    "Tableau de preuve",
    "Le corpus en état mesurable",
    "Les compteurs décrivent des objets documentaires et logiciels. Ils ne mesurent ni la vérité scientifique globale ni la valeur économique."
  ));

  root.append(element("section", { className: "metric-grid", "aria-label": "Mesures du corpus" }, [
    metric("théories", formatNumber(stats.theories), "branches publiques structurées"),
    metric("claims", formatNumber(stats.claims), "avec limite et prochain test"),
    metric("relations", formatNumber(stats.relations), "navigation non causale"),
    metric("artefacts", formatNumber(stats.artifacts), "déclarés dans les fiches"),
    metric("quatre gates", `${stats.publicationReady}/${stats.theories}`, "résumés publiables"),
    metric("signaux M⁻", formatNumber(stats.negativeSignals), "limites ou résultats négatifs")
  ]));

  const panels = element("section", { className: "dashboard-panels" });
  panels.append(element("article", { className: "panel" }, [
    element("header", { className: "panel-header" }, [element("h2", { text: "Maturité" }), badge("état déclaré", "neutral")]),
    distribution(stats.maturity, stats.theories),
    element("p", { className: "fine-print", text: "Architecture ≠ prototype; prototype ≠ validation externe; hypothèse ≠ résultat." })
  ]));
  panels.append(element("article", { className: "panel" }, [
    element("header", { className: "panel-header" }, [element("h2", { text: "Profil OAK moyen" }), badge("navigation", "warning")]),
    oakBars(stats.averageOak),
    element("p", { className: "fine-print", text: "Moyenne descriptive des auto-évaluations provisoires, sans interprétation probabiliste." })
  ]));
  panels.append(element("article", { className: "panel" }, [
    element("header", { className: "panel-header" }, [element("h2", { text: "Risques dominants" }), badge("M⁻", "danger")]),
    element("div", { className: "tag-cloud" }, stats.risks.slice(0, 12).map(([risk, count]) => badge(`${risk} · ${count}`, "danger")))
  ]));
  root.append(panels);

  root.append(element("section", { className: "panel" }, [
    element("header", { className: "panel-header" }, [
      element("div", {}, [element("p", { className: "eyebrow", text: "Hypergraphe" }), element("h2", { text: "Nœuds les plus connectés" })]),
      link("Ouvrir le graphe", "#/graph", "button secondary")
    ]),
    table(
      ["Théorie", "Famille", "Maturité", "Degré", "Accès"],
      connected.map(({ theory, degree }) => [
        `${theory.symbol} — ${theory.title}`,
        theory.family,
        badge(theory.maturity, theory.maturity === "prototype" ? "success" : "warning"),
        degree,
        link("Fiche", `#/theory/${encodeURIComponent(theory.id)}`)
      ]),
      "Centralité de navigation, sans signification causale"
    )
  ]));

  root.append(element("section", { className: "panel" }, [
    element("header", { className: "panel-header" }, [
      element("div", {}, [element("p", { className: "eyebrow", text: "GO CRISTALLISE" }), element("h2", { text: "Actions les plus fertiles à vérifier" })]),
      link("Feuille de route complète", "#/roadmap", "button secondary")
    ]),
    element("ol", { className: "roadmap-list" }, roadmap.map(({ theory, action, priority }) =>
      element("li", {}, [
        element("div", {}, [link(theory.symbol, `#/theory/${encodeURIComponent(theory.id)}`), element("strong", { text: theory.title }), element("p", { text: action })]),
        badge(formatPercent(priority), "success")
      ])
    ))
  ]));
  return root;
}
