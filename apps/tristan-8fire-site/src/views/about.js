"use strict";

import { badge, element, sectionHeader } from "../ui.js";

export function renderAbout({ store }) {
  const root = element("div", { className: "view about-view" });
  root.append(sectionHeader("Ω-WEB-TRISTAN-T", "Un site comme système épistémique", "Tristan Web OS sépare systématiquement vision, hypothèse, architecture, prototype, test, preuve, produit, confidentialité et propriété intellectuelle."));
  root.append(element("section", { className: "about-grid" }, [
    element("article", { className: "panel" }, [
      element("h2", { text: "Objet" }),
      element("p", { text: "Transformer le corpus de Tristan en graphe public navigable de propositions, preuves, codes, limites, prochaines expériences et actifs, sans publier automatiquement le coffre privé." }),
      element("div", { className: "pipeline-inline" }, [badge("Idée", "neutral"), badge("Théorie", "neutral"), badge("Claim", "neutral"), badge("Test", "warning"), badge("Prototype", "success"), badge("Usage", "success")])
    ]),
    element("article", { className: "panel" }, [
      element("h2", { text: "Invariant de publication" }),
      element("code", { className: "publication-formula", text: store.meta.publicationRule || "PUBLIC = OAKGate AND IPGate AND PrivacyGate AND SecurityGate" }),
      element("ul", {}, [
        element("li", { text: "OAKGate : statut, limite, test et résidu explicites." }),
        element("li", { text: "IPGate : aucune invention non protégée exposée par défaut." }),
        element("li", { text: "PrivacyGate : aucune donnée personnelle sensible requise." }),
        element("li", { text: "SecurityGate : aucune capacité risquée publiée sans réduction et garde-fou." })
      ])
    ]),
    element("article", { className: "panel" }, [
      element("h2", { text: "Ce que le site ne certifie pas" }),
      element("ul", {}, [
        element("li", { text: "La vérité scientifique d’une théorie par son nom ou sa cohérence interne." }),
        element("li", { text: "La causalité d’une relation affichée dans le graphe." }),
        element("li", { text: "La sécurité d’une pièce, d’un traitement, d’une expérience ou d’un produit." }),
        element("li", { text: "La brevetabilité, la conformité juridique, le marché ou les revenus." }),
        element("li", { text: "La supériorité sur une baseline sans benchmark reproductible." })
      ])
    ]),
    element("article", { className: "panel" }, [
      element("h2", { text: "Contrat des données" }),
      element("dl", { className: "definition-list" }, [
        element("div", {}, [element("dt", { text: "Version du schéma" }), element("dd", { text: store.meta.schemaVersion })]),
        element("div", {}, [element("dt", { text: "Généré le" }), element("dd", { text: store.meta.generatedAt })]),
        element("div", {}, [element("dt", { text: "Langue canonique publique" }), element("dd", { text: store.meta.locale })]),
        element("div", {}, [element("dt", { text: "Action externe automatique" }), element("dd", { text: "interdite" })])
      ]),
      element("p", { className: "fine-print", text: store.meta.disclaimer })
    ])
  ]));
  return root;
}
