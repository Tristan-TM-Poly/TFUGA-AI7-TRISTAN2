"use strict";

const state = { theories: [], query: "", maturity: "", domain: "" };
const collator = new Intl.Collator("fr", { sensitivity: "base" });

const elements = {
  grid: document.querySelector("#atlas-grid"),
  template: document.querySelector("#theory-template"),
  search: document.querySelector("#search"),
  maturity: document.querySelector("#maturity"),
  domain: document.querySelector("#domain"),
  filters: document.querySelector("#filters"),
  resultCount: document.querySelector("#result-count"),
  metricTheories: document.querySelector("#metric-theories"),
  metricArtifacts: document.querySelector("#metric-artifacts"),
  metricPrototypes: document.querySelector("#metric-prototypes")
};

function normalize(value) {
  return String(value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

function matches(theory) {
  const searchable = normalize([
    theory.symbol,
    theory.title,
    theory.summary,
    theory.evidence,
    theory.status_note,
    theory.next_action,
    ...theory.domains
  ].join(" "));

  return (!state.query || searchable.includes(normalize(state.query)))
    && (!state.maturity || theory.maturity === state.maturity)
    && (!state.domain || theory.domains.includes(state.domain));
}

function oakLabel(key) {
  return {
    verite: "vérité",
    utilite: "utilité",
    testabilite: "testabilité",
    simplicite: "simplicité",
    valeur: "valeur",
    protection: "protection"
  }[key] ?? key;
}

function renderOakBars(container, oak) {
  container.replaceChildren();
  for (const [key, rawValue] of Object.entries(oak)) {
    const value = Math.max(0, Math.min(1, Number(rawValue)));
    const row = document.createElement("div");
    row.className = "oak-row";

    const label = document.createElement("span");
    label.textContent = oakLabel(key);

    const bar = document.createElement("span");
    bar.className = "bar";
    bar.setAttribute("aria-hidden", "true");
    const fill = document.createElement("i");
    fill.style.width = `${Math.round(value * 100)}%`;
    bar.append(fill);

    const output = document.createElement("output");
    output.textContent = value.toFixed(2);
    output.setAttribute("aria-label", `${oakLabel(key)} ${Math.round(value * 100)} pour cent`);

    row.append(label, bar, output);
    container.append(row);
  }
}

function createTheoryCard(theory) {
  const fragment = elements.template.content.cloneNode(true);
  const card = fragment.querySelector(".theory-card");
  card.dataset.id = theory.id;

  fragment.querySelector(".symbol").textContent = theory.symbol;
  fragment.querySelector(".maturity").textContent = theory.maturity;
  fragment.querySelector("h3").textContent = theory.title;
  fragment.querySelector(".summary").textContent = theory.summary;
  fragment.querySelector(".evidence").textContent = theory.evidence;
  fragment.querySelector(".artifacts").textContent = String(theory.artifacts);
  fragment.querySelector(".status-note").textContent = theory.status_note;
  fragment.querySelector(".next-action").textContent = theory.next_action;

  const source = fragment.querySelector(".source");
  const sourceLabel = document.createTextNode("Source canonique : ");
  const sourceCode = document.createElement("code");
  sourceCode.textContent = theory.source_path;
  source.append(sourceLabel, sourceCode);

  const tags = fragment.querySelector(".tags");
  for (const domain of theory.domains) {
    const tag = document.createElement("span");
    tag.textContent = domain;
    tags.append(tag);
  }

  renderOakBars(fragment.querySelector(".oak-bars"), theory.oak);
  return fragment;
}

function render() {
  const visible = state.theories.filter(matches).sort((a, b) => collator.compare(a.title, b.title));
  elements.grid.replaceChildren();

  if (!visible.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "Aucune branche ne correspond à ces filtres.";
    elements.grid.append(empty);
  } else {
    for (const theory of visible) elements.grid.append(createTheoryCard(theory));
  }

  elements.resultCount.textContent = `${visible.length} branche${visible.length > 1 ? "s" : ""} affichée${visible.length > 1 ? "s" : ""} sur ${state.theories.length}.`;
}

function populateDomains() {
  const domains = [...new Set(state.theories.flatMap((theory) => theory.domains))]
    .sort((a, b) => collator.compare(a, b));
  for (const domain of domains) {
    const option = document.createElement("option");
    option.value = domain;
    option.textContent = domain;
    elements.domain.append(option);
  }
}

function updateMetrics() {
  const artifacts = state.theories.reduce((sum, theory) => sum + Number(theory.artifacts || 0), 0);
  const prototypes = state.theories.filter((theory) => theory.maturity === "prototype").length;
  elements.metricTheories.textContent = String(state.theories.length);
  elements.metricArtifacts.textContent = String(artifacts);
  elements.metricPrototypes.textContent = String(prototypes);
}

function bindFilters() {
  elements.search.addEventListener("input", (event) => {
    state.query = event.target.value.trim();
    render();
  });
  elements.maturity.addEventListener("change", (event) => {
    state.maturity = event.target.value;
    render();
  });
  elements.domain.addEventListener("change", (event) => {
    state.domain = event.target.value;
    render();
  });
  elements.filters.addEventListener("reset", () => {
    window.setTimeout(() => {
      state.query = "";
      state.maturity = "";
      state.domain = "";
      render();
    }, 0);
  });
}

async function initialize() {
  try {
    const response = await fetch("data/theories.json", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    if (!Array.isArray(payload.theories)) throw new TypeError("Invalid theory dataset");

    state.theories = payload.theories;
    populateDomains();
    updateMetrics();
    bindFilters();
    render();
  } catch (error) {
    console.error("Unable to load Tristan Web OS data", error);
    elements.grid.innerHTML = "";
    const message = document.createElement("p");
    message.className = "empty-state";
    message.textContent = "Le jeu de données de l’Atlas n’a pas pu être chargé. Lancez le site via un serveur HTTP local.";
    elements.grid.append(message);
    elements.resultCount.textContent = "Atlas indisponible.";
  }
}

initialize();
