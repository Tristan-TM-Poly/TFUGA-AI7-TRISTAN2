"use strict";

import { badge, element, link, sectionHeader } from "../ui.js";

function classify(text) {
  const value = String(text || "").toLowerCase();
  if (/surpass|battu|gain.*non|n[’']a pas/.test(value)) return ["baseline supérieure ou gain absent", "benchmark"];
  if (/aucune supériorité|non prouv|preuve insuffisante/.test(value)) return ["revendication bloquée", "preuve"];
  if (/sécur|dangereu|irréversible/.test(value)) return ["limite de sécurité", "sécurité"];
  if (/fabric|manufact|qualification/.test(value)) return ["fabrication ou qualification non démontrée", "fabrication"];
  if (/marché|revenu|utilisateur/.test(value)) return ["validation marché absente", "marché"];
  return ["limite explicite", "épistémique"];
}

function memories(store) {
  const rows = [];
  for (const theory of store.theories) {
    const texts = [theory.status_note, ...(theory.risks || [])];
    const combined = texts.join(" — ");
    if (!/n[’']a pas|aucune|non |limite|risque|insuffisant|surpromesse|échec|dangereu|abusive|artefact/i.test(combined)) continue;
    const [title, category] = classify(combined);
    rows.push({
      id: `mminus-${theory.id}`,
      theory,
      title,
      category,
      observation: theory.status_note,
      antiRule: `Ne pas promouvoir ${theory.symbol} au-delà de « ${theory.maturity} / ${theory.evidence} » sans exécuter le test suivant.`,
      recovery: theory.next_action
    });
  }
  for (const claim of store.claims.filter((item) => item.kind === "limit")) {
    const theory = store.getTheory(claim.theory_id);
    if (!theory) continue;
    rows.push({
      id: `mminus-${claim.id}`,
      theory,
      title: "garde-fou de claim",
      category: "claim",
      observation: claim.falsification_or_limit,
      antiRule: claim.statement,
      recovery: claim.next_test
    });
  }
  return rows;
}

export function renderMminus({ store }) {
  const rows = memories(store);
  const categories = new Map();
  for (const row of rows) categories.set(row.category, (categories.get(row.category) || 0) + 1);
  const root = element("div", { className: "view mminus-view" });
  root.append(sectionHeader("Mémoire négative M⁻", "Les erreurs deviennent des règles anti-erreur", "Le registre conserve résultats négatifs, limites, absences de preuve et conditions de récupération. Une limite bien documentée est un actif de recherche, pas un échec à cacher."));
  root.append(element("div", { className: "tag-cloud large-tags" }, [...categories.entries()].sort((a, b) => b[1] - a[1]).map(([category, count]) => badge(`${category} · ${count}`, "danger"))));
  root.append(element("section", { className: "memory-grid" }, rows.map((row) =>
    element("article", { className: "memory-card" }, [
      element("header", { className: "card-topline" }, [badge("M⁻", "danger"), badge(row.category, "neutral")]),
      element("h2", { text: row.title }),
      element("p", { className: "memory-theory" }, [link(`${row.theory.symbol} — ${row.theory.title}`, `#/theory/${encodeURIComponent(row.theory.id)}`)]),
      element("h3", { text: "Observation" }),
      element("p", { text: row.observation }),
      element("h3", { text: "Règle anti-erreur" }),
      element("p", { className: "anti-rule", text: row.antiRule }),
      element("h3", { text: "Chemin de récupération" }),
      element("p", { text: row.recovery })
    ])
  )));
  return root;
}
