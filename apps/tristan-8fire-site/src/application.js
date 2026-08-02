"use strict";

import { CorpusStore } from "./data-store.js";
import { createPreferences } from "./preferences.js";
import { createRouter } from "./router.js";
import { announce, element, emptyState } from "./ui.js";
import { renderAbout } from "./views/about.js";
import { renderAtlas } from "./views/atlas.js";
import { renderClaims, renderClaim } from "./views/claims.js";
import { renderDashboard } from "./views/dashboard.js";
import { renderEvidence } from "./views/evidence.js";
import { renderGraph } from "./views/graph.js";
import { renderMminus } from "./views/mminus.js";
import { renderProvenance } from "./views/provenance.js";
import { renderRoadmap } from "./views/roadmap.js";
import { renderTheory } from "./views/theory.js";

const ROUTES = Object.freeze({
  dashboard: renderDashboard,
  atlas: renderAtlas,
  theory: renderTheory,
  claims: renderClaims,
  claim: renderClaim,
  graph: renderGraph,
  evidence: renderEvidence,
  provenance: renderProvenance,
  mminus: renderMminus,
  roadmap: renderRoadmap,
  about: renderAbout
});

function setActiveNavigation(name) {
  for (const anchor of document.querySelectorAll("[data-route]")) {
    const active = anchor.dataset.route === name || (name === "theory" && anchor.dataset.route === "atlas") || (name === "claim" && anchor.dataset.route === "claims");
    anchor.classList.toggle("is-active", active);
    if (active) anchor.setAttribute("aria-current", "page");
    else anchor.removeAttribute("aria-current");
  }
}

function setupGlobalSearch(store) {
  const form = document.querySelector("#global-search");
  const input = document.querySelector("#global-search-input");
  const results = document.querySelector("#global-search-results");
  if (!form || !input || !results) return;

  function hide() { results.hidden = true; results.replaceChildren(); }
  function show(query) {
    const theories = store.searchTheories(query).slice(0, 6);
    const claims = store.searchClaims(query).slice(0, 6);
    results.replaceChildren();
    if (!query.trim()) return hide();
    results.append(element("p", { className: "search-result-heading", text: "Théories" }));
    for (const { item } of theories) results.append(element("a", { href: `#/theory/${encodeURIComponent(item.id)}` }, [element("strong", { text: item.symbol }), element("span", { text: item.title })]));
    results.append(element("p", { className: "search-result-heading", text: "Claims" }));
    for (const { item } of claims) results.append(element("a", { href: `#/claim/${encodeURIComponent(item.id)}` }, [element("strong", { text: item.id }), element("span", { text: item.title })]));
    if (!theories.length && !claims.length) results.append(element("p", { text: "Aucun résultat." }));
    results.hidden = false;
  }

  input.addEventListener("input", () => show(input.value));
  input.addEventListener("focus", () => show(input.value));
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const query = input.value.trim();
    if (query) window.location.hash = `#/atlas?q=${encodeURIComponent(query)}`;
    hide();
  });
  document.addEventListener("click", (event) => { if (!form.contains(event.target)) hide(); });
  document.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
      event.preventDefault(); input.focus(); input.select();
    }
    if (event.key === "/" && !/input|textarea|select/i.test(document.activeElement?.tagName || "")) {
      event.preventDefault(); input.focus();
    }
    if (event.key === "Escape") { hide(); input.blur(); }
  });
}

function setupPreferences(preferences) {
  const theme = document.querySelector("#toggle-theme");
  const density = document.querySelector("#toggle-density");
  theme?.addEventListener("click", () => preferences.toggleTheme());
  density?.addEventListener("click", () => preferences.toggleDensity());
  preferences.subscribe((value) => {
    if (theme) theme.setAttribute("aria-label", `Thème actuel : ${value.theme}. Changer le thème.`);
    if (density) density.setAttribute("aria-label", `Densité actuelle : ${value.density}. Changer la densité.`);
  });
}

function setupInstallPrompt() {
  let promptEvent = null;
  const button = document.querySelector("#install-app");
  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    promptEvent = event;
    if (button) button.hidden = false;
  });
  button?.addEventListener("click", async () => {
    if (!promptEvent) return;
    promptEvent.prompt();
    await promptEvent.userChoice;
    promptEvent = null;
    button.hidden = true;
  });
}

async function registerServiceWorker() {
  if (!("serviceWorker" in navigator) || location.protocol === "file:") return;
  try { await navigator.serviceWorker.register("sw.js"); } catch (error) { console.warn("Service worker unavailable", error); }
}

export async function startApplication() {
  const root = document.querySelector("#app");
  const loading = document.querySelector("#app-loading");
  const errorBox = document.querySelector("#app-error");
  if (!root) throw new Error("Missing #app root");
  const preferences = createPreferences();
  setupPreferences(preferences);
  setupInstallPrompt();

  try {
    const store = await new CorpusStore().load();
    setupGlobalSearch(store);
    const router = createRouter((route) => {
      const renderer = ROUTES[route.name];
      setActiveNavigation(route.name);
      root.replaceChildren();
      if (!renderer) root.append(emptyState("Route inconnue", `La vue « ${route.name} » n’existe pas.`));
      else root.append(renderer({ store, route, preferences, router }));
      document.title = `${route.name === "dashboard" ? "Tableau de preuve" : route.name} — Tristan Web OS`;
      window.scrollTo({ top: 0, behavior: preferences.get().motion === "reduced" ? "auto" : "smooth" });
      announce(`Vue ${route.name} chargée.`);
    });
    loading?.remove();
    errorBox?.remove();
    router.start();
    registerServiceWorker();
    window.TristanWebOS = Object.freeze({ store, router, preferences, version: "0.3.0" });
  } catch (error) {
    console.error(error);
    loading?.remove();
    if (errorBox) {
      errorBox.hidden = false;
      errorBox.textContent = `Le corpus n’a pas pu être chargé : ${error.message}`;
    } else root.append(emptyState("Chargement impossible", error.message));
  }
}
