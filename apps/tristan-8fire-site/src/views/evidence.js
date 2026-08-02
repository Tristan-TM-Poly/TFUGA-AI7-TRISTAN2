"use strict";

import { badge, element, formatNumber, link, sectionHeader, table } from "../ui.js";

function supportCount(claim) { return Array.isArray(claim.support) ? claim.support.length : 0; }

function evidenceState(claim) {
  if (claim.status === "guardrail") return ["garde-fou", "warning"];
  if (claim.status === "planned") return ["test planifié", "neutral"];
  if (supportCount(claim) > 1) return ["support multiple", "success"];
  return ["référence canonique", "danger"];
}

export function renderEvidence({ store }) {
  const claimsWithTheory = store.claims.map((claim) => ({ claim, theory: store.getTheory(claim.theory_id) }));
  const supportPaths = new Map();
  for (const { claim } of claimsWithTheory) {
    for (const support of claim.support || []) supportPaths.set(support.path, (supportPaths.get(support.path) || 0) + 1);
  }
  const uniqueSources = [...supportPaths.entries()].sort((a, b) => b[1] - a[1]);
  const root = element("div", { className: "view evidence-view" });
  root.append(sectionHeader("Evidence Fabric", "Claim → support → limite → test", "Cette matrice rend visibles les dépendances documentaires. Une référence canonique décrit la conception; elle ne constitue pas automatiquement une validation indépendante."));

  root.append(element("section", { className: "metric-grid compact-metrics" }, [
    element("article", { className: "metric-card" }, [element("strong", { text: formatNumber(store.claims.length) }), element("span", { text: "claims" })]),
    element("article", { className: "metric-card" }, [element("strong", { text: formatNumber(uniqueSources.length) }), element("span", { text: "sources distinctes" })]),
    element("article", { className: "metric-card" }, [element("strong", { text: formatNumber(store.claims.filter((claim) => claim.status === "planned").length) }), element("span", { text: "tests planifiés" })]),
    element("article", { className: "metric-card" }, [element("strong", { text: "0" }), element("span", { text: "promotion automatique" })])
  ]));

  root.append(element("section", { className: "panel" }, [
    element("header", { className: "panel-header" }, [element("h2", { text: "Matrice des claims" }), badge("audit public", "neutral")]),
    table(
      ["Claim", "Théorie", "État", "Supports", "Limite explicite", "Prochain test"],
      claimsWithTheory.map(({ claim, theory }) => {
        const [label, tone] = evidenceState(claim);
        return [
          link(claim.id, `#/claim/${encodeURIComponent(claim.id)}`),
          theory ? link(theory.symbol, `#/theory/${encodeURIComponent(theory.id)}`) : claim.theory_id,
          badge(label, tone),
          supportCount(claim),
          claim.falsification_or_limit,
          claim.next_test
        ];
      }),
      "Registre complet des liens entre affirmations, supports déclarés et falsification"
    )
  ]));

  root.append(element("section", { className: "panel" }, [
    element("header", { className: "panel-header" }, [element("h2", { text: "Concentration des sources" }), badge("risque de dépendance", "warning")]),
    element("div", { className: "source-list" }, uniqueSources.map(([path, count]) =>
      element("article", {}, [element("code", { text: path }), element("strong", { text: `${count} claim${count > 1 ? "s" : ""}` })])
    )),
    element("p", { className: "fine-print", text: "Une forte concentration sur les références internes indique un besoin de données, publications ou réplications externes; elle n’invalide pas l’architecture mais limite son statut." })
  ]));
  return root;
}
