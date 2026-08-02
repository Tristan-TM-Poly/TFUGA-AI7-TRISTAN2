"use strict";

import { badge, element, emptyState, link, oakBars, publicationGate, sectionHeader, table } from "../ui.js";
import { exportTheoryMarkdown } from "../exporters.js";

function claimCard(claim) {
  return element("article", { className: "claim-card" }, [
    element("div", { className: "card-topline" }, [badge(claim.kind, "neutral"), badge(claim.status, claim.status === "guardrail" ? "warning" : "success")]),
    element("h3", {}, [link(claim.title, `#/claim/${encodeURIComponent(claim.id)}`)]),
    element("p", { text: claim.statement }),
    element("details", {}, [
      element("summary", { text: "Limite, contre-hypothèses et test" }),
      element("p", {}, [element("strong", { text: "Limite : " }), claim.falsification_or_limit]),
      element("ul", {}, (claim.counter_hypotheses || []).map((item) => element("li", { text: item }))),
      element("p", {}, [element("strong", { text: "Prochain test : " }), claim.next_test])
    ])
  ]);
}

export function renderTheory({ store, route }) {
  const theory = store.getTheory(route.params.id);
  if (!theory) return emptyState("Théorie introuvable", "L’identifiant demandé n’existe pas dans le catalogue public.");
  const claims = store.getClaimsForTheory(theory.id);
  const neighbors = store.getNeighbors(theory.id);
  const root = element("div", { className: "view theory-view" });
  root.append(sectionHeader(theory.symbol, theory.title, theory.summary));

  root.append(element("div", { className: "theory-actions" }, [
    link("← Atlas", "#/atlas", "button secondary"),
    link("Claims filtrés", `#/claims?theory=${encodeURIComponent(theory.id)}`, "button secondary"),
    link("Graphe local", `#/graph/${encodeURIComponent(theory.id)}`, "button secondary"),
    element("button", { className: "button primary", text: "Exporter la fiche .md", onclick: () => exportTheoryMarkdown(theory, claims, neighbors) })
  ]));

  root.append(element("section", { className: "theory-layout" }, [
    element("article", { className: "panel theory-summary-panel" }, [
      element("div", { className: "tag-cloud" }, [badge(theory.maturity, theory.maturity === "prototype" ? "success" : "warning"), badge(theory.evidence, "neutral"), ...(theory.domains || []).map((domain) => badge(domain, "neutral"))]),
      element("h2", { text: "État actuel" }),
      element("p", { text: theory.status_note }),
      element("h3", { text: "Prochaine action vérifiable" }),
      element("p", { className: "next-action-callout", text: theory.next_action }),
      element("h3", { text: "Sorties attendues" }),
      element("ul", {}, (theory.outputs || []).map((output) => element("li", { text: output }))),
      element("h3", { text: "Risques M⁻" }),
      element("div", { className: "tag-cloud" }, (theory.risks || []).map((risk) => badge(risk, "danger")))
    ]),
    element("aside", { className: "panel" }, [
      element("h2", { text: "Profil OAK" }),
      oakBars(theory.oak),
      element("h3", { text: "Publication" }),
      publicationGate(theory.publication),
      element("dl", { className: "definition-list" }, [
        element("div", {}, [element("dt", { text: "Version" }), element("dd", { text: theory.version })]),
        element("div", {}, [element("dt", { text: "Visibilité" }), element("dd", { text: theory.visibility })]),
        element("div", {}, [element("dt", { text: "Source" }), element("dd", {}, [element("code", { text: theory.source_path })])]),
        element("div", {}, [element("dt", { text: "Mise à jour" }), element("dd", { text: theory.updated_at })]),
        element("div", {}, [element("dt", { text: "Artefacts" }), element("dd", { text: theory.artifacts })])
      ])
    ])
  ]));

  root.append(element("section", { className: "panel" }, [
    element("header", { className: "panel-header" }, [element("h2", { text: `Claims (${claims.length})` }), badge("aucune promotion automatique", "warning")]),
    element("div", { className: "claim-grid" }, claims.map(claimCard))
  ]));

  root.append(element("section", { className: "panel" }, [
    element("header", { className: "panel-header" }, [element("h2", { text: `Relations de navigation (${neighbors.length})` }), badge("non causal", "danger")]),
    table(
      ["Direction", "Théorie", "Type", "Force", "Rationale"],
      neighbors.map(({ theory: target, relation, direction }) => [
        direction === "out" ? "sortante →" : "entrante ←",
        link(`${target.symbol} — ${target.title}`, `#/theory/${encodeURIComponent(target.id)}`),
        relation.kind,
        Number(relation.strength).toFixed(2),
        relation.rationale
      ]),
      "Relations destinées à l’exploration, pas à l’inférence causale"
    )
  ]));
  return root;
}
