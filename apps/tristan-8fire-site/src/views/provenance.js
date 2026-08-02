"use strict";

import { badge, element, emptyState, formatNumber, link, sectionHeader, table } from "../ui.js";

async function loadJson(path, arrayKey) {
  const response = await fetch(path, { headers: { Accept: "application/json" }, cache: "no-cache" });
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  const payload = await response.json();
  if (arrayKey && !Array.isArray(payload[arrayKey])) throw new TypeError(`Invalid ${path}`);
  return payload;
}

function sourceTone(status) {
  if (status === "resolved-file") return "success";
  if (status === "resolved-directory") return "warning";
  return "danger";
}

function buildPanel(build) {
  return element("section", { className: "panel build-integrity" }, [
    element("header", { className: "panel-header" }, [
      element("div", {}, [element("p", { className: "eyebrow", text: "Build root" }), element("h2", { text: "Intégrité du snapshot public" })]),
      badge(`${build.metrics.files} fichiers`, "success")
    ]),
    element("dl", { className: "definition-list" }, [
      element("div", {}, [element("dt", { text: "Racine SHA-256" }), element("dd", {}, [element("code", { text: build.root_sha256 })])]),
      element("div", {}, [element("dt", { text: "Octets" }), element("dd", { text: formatNumber(build.metrics.bytes) })]),
      element("div", {}, [element("dt", { text: "Algorithme" }), element("dd", { text: build.algorithm })]),
      element("div", {}, [element("dt", { text: "Schéma" }), element("dd", { text: build.schema_version })])
    ]),
    element("p", { className: "fine-print", text: build.epistemic_boundary })
  ]);
}

function renderManifest(root, manifest, build, route, store) {
  const query = (route.query.get("q") || "").toLowerCase();
  const status = route.query.get("status") || "";
  const kind = route.query.get("kind") || "";
  const statuses = [...new Set(manifest.sources.map((item) => item.status))].sort();
  const kinds = [...new Set(manifest.sources.map((item) => item.kind))].sort();
  const filtered = manifest.sources.filter((source) => {
    const searchable = `${source.id} ${source.path} ${source.kind} ${source.status} ${source.theory_ids.join(" ")} ${source.claim_ids.join(" ")}`.toLowerCase();
    return (!query || searchable.includes(query)) && (!status || source.status === status) && (!kind || source.kind === kind);
  });

  root.append(buildPanel(build));
  root.append(element("section", { className: "metric-grid compact-metrics" }, [
    element("article", { className: "metric-card" }, [element("strong", { text: formatNumber(manifest.metrics.sources) }), element("span", { text: "sources" })]),
    element("article", { className: "metric-card" }, [element("strong", { text: formatNumber(manifest.metrics.resolved_files) }), element("span", { text: "fichiers résolus" })]),
    element("article", { className: "metric-card" }, [element("strong", { text: formatNumber(manifest.metrics.resolved_directories) }), element("span", { text: "dossiers résolus" })]),
    element("article", { className: "metric-card" }, [element("strong", { text: formatNumber(manifest.metrics.unresolved) }), element("span", { text: "références non résolues" })])
  ]));

  const form = element("form", { className: "filter-console provenance-filter" }, [
    element("label", {}, [element("span", { text: "Recherche" }), element("input", { type: "search", name: "q", value: route.query.get("q") || "", placeholder: "Chemin, claim, théorie, hash…" })]),
    element("label", {}, [element("span", { text: "Statut" }), element("select", { name: "status" }, [element("option", { value: "", text: "Tous les statuts" }), ...statuses.map((value) => element("option", { value, text: value, selected: value === status }))])]),
    element("label", {}, [element("span", { text: "Type" }), element("select", { name: "kind" }, [element("option", { value: "", text: "Tous les types" }), ...kinds.map((value) => element("option", { value, text: value, selected: value === kind }))])]),
    element("button", { type: "submit", className: "button primary", text: "Appliquer" }),
    link("Réinitialiser", "#/provenance", "button secondary")
  ]);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const params = new URLSearchParams();
    for (const [key, value] of new FormData(form).entries()) if (String(value).trim()) params.set(key, String(value).trim());
    window.location.hash = `#/provenance${params.size ? `?${params}` : ""}`;
  });
  root.append(form);
  root.append(element("p", { className: "fine-print", text: manifest.disclaimer }));

  root.append(element("section", { className: "panel" }, [
    element("header", { className: "panel-header" }, [element("h2", { text: `${filtered.length} sources affichées` }), badge("SHA-256 ≠ preuve", "warning")]),
    table(
      ["Source", "Statut", "Type", "SHA-256", "Taille", "Théories", "Claims"],
      filtered.map((source) => [
        element("div", {}, [element("strong", { text: source.id }), element("code", { text: source.path })]),
        badge(source.status, sourceTone(source.status)),
        source.kind,
        source.sha256 ? element("code", { text: source.sha256 }) : "—",
        source.size_bytes === null ? "—" : formatNumber(source.size_bytes),
        element("div", { className: "provenance-links" }, source.theory_ids.map((id) => {
          const theory = store.getTheory(id);
          return link(theory?.symbol || id, `#/theory/${encodeURIComponent(id)}`);
        })),
        element("div", { className: "provenance-links" }, source.claim_ids.slice(0, 8).map((id) => link(id, `#/claim/${encodeURIComponent(id)}`)))
      ]),
      "Empreintes du snapshot courant; une modification de fichier change le hash"
    )
  ]));
}

export function renderProvenance({ route, store }) {
  const root = element("div", { className: "view provenance-view" });
  root.append(sectionHeader("Info² / Provenance", "Du claim au fichier, puis à la racine du build", "Le manifeste distingue références résolues, chemins manquants et empreintes. La racine de build détecte les changements de bytes sans transformer l’intégrité en preuve scientifique."));
  const loading = element("section", { className: "loading-state compact-loading", "aria-busy": "true" }, [element("span", { className: "loading-orbit", "aria-hidden": "true" }), element("p", { text: "Chargement des manifestes de provenance et de build…" })]);
  root.append(loading);
  Promise.all([
    loadJson("data/provenance.json", "sources"),
    loadJson("data/build-manifest.json", "files")
  ])
    .then(([manifest, build]) => { loading.remove(); renderManifest(root, manifest, build, route, store); })
    .catch((error) => { loading.replaceWith(emptyState("Provenance indisponible", `Un manifeste n’est pas encore matérialisé ou ne peut pas être chargé : ${error.message}`)); });
  return root;
}
