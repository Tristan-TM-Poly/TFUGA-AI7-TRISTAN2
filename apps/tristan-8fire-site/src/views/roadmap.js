"use strict";

import { badge, element, formatPercent, link, sectionHeader } from "../ui.js";

function lane(title, description, items, tone) {
  return element("section", { className: "roadmap-lane" }, [
    element("header", {}, [element("h2", { text: title }), element("p", { text: description }), badge(`${items.length} actions`, tone)]),
    element("ol", {}, items.map(({ theory, action, priority }, index) =>
      element("li", { className: "roadmap-item" }, [
        element("span", { className: "roadmap-rank", text: String(index + 1).padStart(2, "0") }),
        element("div", {}, [
          element("p", { className: "roadmap-symbol" }, [link(theory.symbol, `#/theory/${encodeURIComponent(theory.id)}`)]),
          element("h3", { text: theory.title }),
          element("p", { text: action }),
          element("div", { className: "tag-cloud" }, [badge(theory.maturity, tone), badge(theory.evidence, "neutral"), ...(theory.risks || []).slice(0, 2).map((risk) => badge(risk, "danger"))])
        ]),
        element("strong", { className: "priority-score", text: formatPercent(priority), title: "Moyenne utilité, testabilité et valeur" })
      ])
    ))
  ]);
}

export function renderRoadmap({ store }) {
  const all = store.roadmap();
  const prototype = all.filter((item) => item.theory.maturity === "prototype");
  const architecture = all.filter((item) => item.theory.maturity === "architecture");
  const hypothesis = all.filter((item) => item.theory.maturity === "hypothèse");
  const root = element("div", { className: "view roadmap-view" });
  root.append(sectionHeader("GO CRISTALLISE", "De la prochaine action au prochain résultat", "La priorité est un signal heuristique calculé à partir d’utilité, testabilité et valeur déclarées. Elle ne remplace ni coût réel, disponibilité des données, sécurité, IP ni jugement humain."));
  root.append(element("section", { className: "roadmap-principles panel" }, [
    element("h2", { text: "Règle de passage" }),
    element("div", { className: "pipeline-inline" }, [
      badge("Hypothèse testée → connaissance", "success"),
      badge("Architecture codée → prototype", "success"),
      badge("Prototype testé → actif", "success"),
      badge("Actif utilisé → produit potentiel", "success"),
      badge("Produit vendu → preuve marché", "success")
    ]),
    element("p", { text: "Aucune branche ne doit ouvrir dix sous-branches avant d’avoir fermé au moins un artefact vérifiable." })
  ]));
  root.append(lane("Prototypes à comparer", "Les objets exécutables doivent rencontrer des baselines, des données et des métriques.", prototype, "success"));
  root.append(lane("Architectures à coder", "Le prochain gain vient d’une première version qui tourne, pas d’une extension nominale supplémentaire.", architecture, "warning"));
  root.append(lane("Hypothèses à réduire", "Transformer la vision en objet minimal falsifiable avant toute promotion.", hypothesis, "danger"));
  return root;
}
