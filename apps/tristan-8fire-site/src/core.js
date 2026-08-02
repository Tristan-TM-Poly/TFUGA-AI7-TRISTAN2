"use strict";

export const DATA_URLS = Object.freeze({
  config: "data/site-config.json",
  theories: "data/theories.json",
  claims: "data/claims.json",
  relations: "data/relations.json",
  roadmap: "data/roadmap.json"
});

export const DEFAULT_STATE = Object.freeze({
  route: { name: "home", params: {}, query: new URLSearchParams() },
  locale: "fr",
  readingMode: "simple",
  query: "",
  maturity: "",
  domain: "",
  family: "",
  claimStatus: "",
  sort: "relevance",
  selectedTheoryId: null,
  compareIds: [],
  favorites: [],
  data: {
    config: null,
    theories: [],
    claims: [],
    relations: [],
    roadmap: null
  },
  derived: {
    filteredTheories: [],
    filteredClaims: [],
    metrics: {},
    warnings: []
  },
  loading: true,
  error: null
});

const PREFERENCE_KEY = "tristan-web-os.preferences.v2";
const MAX_COMPARE = 4;

export function deepClone(value) {
  if (typeof structuredClone === "function") return structuredClone(value);
  return JSON.parse(JSON.stringify(value));
}

export function normalizeText(value) {
  return String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("fr-CA")
    .replace(/[^\p{L}\p{N}\s_-]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function clamp(value, minimum = 0, maximum = 1) {
  const number = Number(value);
  if (!Number.isFinite(number)) return minimum;
  return Math.max(minimum, Math.min(maximum, number));
}

export function unique(values) {
  return [...new Set(values)];
}

export function groupBy(values, keySelector) {
  const groups = new Map();
  for (const value of values) {
    const key = keySelector(value);
    const bucket = groups.get(key) ?? [];
    bucket.push(value);
    groups.set(key, bucket);
  }
  return groups;
}

export function countBy(values, keySelector) {
  const counts = new Map();
  for (const value of values) {
    const key = keySelector(value);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return counts;
}

export function safeJsonParse(raw, fallback = null) {
  try {
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}

export async function fetchJson(url, { signal } = {}) {
  const response = await fetch(url, {
    signal,
    cache: "no-cache",
    headers: { Accept: "application/json" }
  });
  if (!response.ok) {
    throw new Error(`Unable to fetch ${url}: HTTP ${response.status}`);
  }
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("json") && !url.endsWith(".json")) {
    throw new TypeError(`Expected JSON from ${url}`);
  }
  return response.json();
}

export async function loadAllData(urls = DATA_URLS, { signal } = {}) {
  const entries = Object.entries(urls);
  const payloads = await Promise.all(
    entries.map(async ([key, url]) => [key, await fetchJson(url, { signal })])
  );
  return Object.fromEntries(payloads);
}

function requireArray(value, label) {
  if (!Array.isArray(value)) throw new TypeError(`${label} must be an array`);
  return value;
}

function requireObject(value, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new TypeError(`${label} must be an object`);
  }
  return value;
}

function requireString(value, label) {
  if (typeof value !== "string" || !value.trim()) {
    throw new TypeError(`${label} must be a non-empty string`);
  }
  return value;
}

export function validateTheory(theory, index = 0) {
  requireObject(theory, `theories[${index}]`);
  for (const field of [
    "id", "symbol", "title", "summary", "family", "maturity",
    "evidence", "status_note", "next_action", "source_path"
  ]) {
    requireString(theory[field], `theories[${index}].${field}`);
  }
  requireArray(theory.domains, `theories[${index}].domains`);
  requireArray(theory.risks, `theories[${index}].risks`);
  requireArray(theory.outputs, `theories[${index}].outputs`);
  requireObject(theory.oak, `theories[${index}].oak`);
  requireObject(theory.publication, `theories[${index}].publication`);
  if (!Number.isInteger(theory.artifacts) || theory.artifacts < 0) {
    throw new TypeError(`theories[${index}].artifacts must be a non-negative integer`);
  }
  return theory;
}

export function validateClaim(claim, index = 0) {
  requireObject(claim, `claims[${index}]`);
  for (const field of [
    "id", "theory_id", "kind", "title", "statement", "status",
    "epistemic_level", "confidence_label", "falsification_or_limit", "next_test"
  ]) {
    requireString(claim[field], `claims[${index}].${field}`);
  }
  requireArray(claim.support, `claims[${index}].support`);
  requireArray(claim.counter_hypotheses, `claims[${index}].counter_hypotheses`);
  requireArray(claim.risk_tags, `claims[${index}].risk_tags`);
  return claim;
}

export function validateRelation(relation, index = 0) {
  requireObject(relation, `relations[${index}]`);
  for (const field of ["id", "source", "target", "kind", "rationale"]) {
    requireString(relation[field], `relations[${index}].${field}`);
  }
  return relation;
}

export function validateDataBundle(bundle) {
  requireObject(bundle, "bundle");
  const theories = requireArray(bundle.theories?.theories, "theories.theories");
  const claims = requireArray(bundle.claims?.claims, "claims.claims");
  const relations = requireArray(bundle.relations?.relations, "relations.relations");
  theories.forEach(validateTheory);
  claims.forEach(validateClaim);
  relations.forEach(validateRelation);

  const ids = new Set(theories.map((theory) => theory.id));
  if (ids.size !== theories.length) throw new Error("Theory ids must be unique");
  for (const claim of claims) {
    if (!ids.has(claim.theory_id)) {
      throw new Error(`Claim ${claim.id} references missing theory ${claim.theory_id}`);
    }
  }
  for (const relation of relations) {
    if (!ids.has(relation.source) || !ids.has(relation.target)) {
      throw new Error(`Relation ${relation.id} references a missing theory`);
    }
    if (relation.source === relation.target) {
      throw new Error(`Relation ${relation.id} cannot be a self-loop`);
    }
  }
  return bundle;
}

export class EventBus {
  #listeners = new Map();

  on(eventName, listener) {
    const listeners = this.#listeners.get(eventName) ?? new Set();
    listeners.add(listener);
    this.#listeners.set(eventName, listeners);
    return () => this.off(eventName, listener);
  }

  off(eventName, listener) {
    const listeners = this.#listeners.get(eventName);
    if (!listeners) return;
    listeners.delete(listener);
    if (!listeners.size) this.#listeners.delete(eventName);
  }

  emit(eventName, payload) {
    const listeners = this.#listeners.get(eventName);
    if (!listeners) return;
    for (const listener of [...listeners]) {
      try {
        listener(payload);
      } catch (error) {
        console.error(`Event listener failed for ${eventName}`, error);
      }
    }
  }

  clear() {
    this.#listeners.clear();
  }
}

export class Store {
  #state;
  #bus = new EventBus();

  constructor(initialState = DEFAULT_STATE) {
    this.#state = deepClone(initialState);
  }

  getState() {
    return this.#state;
  }

  subscribe(listener) {
    return this.#bus.on("change", listener);
  }

  update(updater, reason = "update") {
    const previous = this.#state;
    const draft = deepClone(previous);
    const next = updater(draft) ?? draft;
    this.#state = next;
    this.#bus.emit("change", { previous, next, reason });
    return next;
  }

  replace(nextState, reason = "replace") {
    const previous = this.#state;
    this.#state = deepClone(nextState);
    this.#bus.emit("change", { previous, next: this.#state, reason });
    return this.#state;
  }
}

export function parseHashRoute(hash = window.location.hash) {
  const raw = String(hash || "#/").replace(/^#/, "");
  const [pathPart, queryPart = ""] = raw.split("?");
  const path = pathPart.startsWith("/") ? pathPart : `/${pathPart}`;
  const segments = path.split("/").filter(Boolean);
  const query = new URLSearchParams(queryPart);

  if (!segments.length) return { name: "home", params: {}, query };
  if (segments[0] === "theory" && segments[1]) {
    return {
      name: "theory",
      params: { theoryId: decodeURIComponent(segments.slice(1).join("/")) },
      query
    };
  }
  const known = new Set(["home", "atlas", "claims", "graph", "proofs", "roadmap", "about"]);
  const routeName = segments[0] === "" ? "home" : segments[0];
  return {
    name: known.has(routeName) ? routeName : "not-found",
    params: {},
    query
  };
}

export function routeToHash(name, params = {}, query = {}) {
  let path = name === "home" ? "/" : `/${name}`;
  if (name === "theory" && params.theoryId) {
    path = `/theory/${encodeURIComponent(params.theoryId)}`;
  }
  const search = new URLSearchParams(query);
  const suffix = search.toString() ? `?${search.toString()}` : "";
  return `#${path}${suffix}`;
}

export function readPreferences(storage = window.localStorage) {
  const raw = storage.getItem(PREFERENCE_KEY);
  const parsed = safeJsonParse(raw, {});
  return {
    locale: parsed?.locale === "en" ? "en" : "fr",
    readingMode: ["simple", "technical", "complete"].includes(parsed?.readingMode)
      ? parsed.readingMode
      : "simple",
    favorites: Array.isArray(parsed?.favorites)
      ? parsed.favorites.filter((item) => typeof item === "string").slice(0, 200)
      : []
  };
}

export function writePreferences(state, storage = window.localStorage) {
  const payload = {
    locale: state.locale === "en" ? "en" : "fr",
    readingMode: state.readingMode,
    favorites: [...new Set(state.favorites)].slice(0, 200)
  };
  storage.setItem(PREFERENCE_KEY, JSON.stringify(payload));
}

export function hydrateStateWithData(state, bundle) {
  validateDataBundle(bundle);
  state.data.config = bundle.config;
  state.data.theories = bundle.theories.theories;
  state.data.claims = bundle.claims.claims;
  state.data.relations = bundle.relations.relations;
  state.data.roadmap = bundle.roadmap;
  state.loading = false;
  state.error = null;
  return state;
}

export function computeMetrics(data) {
  const theories = data.theories ?? [];
  const claims = data.claims ?? [];
  const relations = data.relations ?? [];
  const artifacts = theories.reduce((sum, theory) => sum + Number(theory.artifacts || 0), 0);
  const prototypes = theories.filter((theory) => theory.maturity === "prototype").length;
  const negativeResults = claims.filter((claim) => claim.status === "negative_result").length;
  const plannedTests = claims.filter((claim) => claim.status === "planned").length;
  const publicReady = theories.filter((theory) =>
    ["oak_gate", "ip_gate", "privacy_gate", "security_gate"]
      .every((gate) => theory.publication?.[gate] === true)
  ).length;
  return {
    theories: theories.length,
    claims: claims.length,
    relations: relations.length,
    artifacts,
    prototypes,
    negativeResults,
    plannedTests,
    publicReady
  };
}

export function buildDerivedState(state, { theorySearch, claimSearch } = {}) {
  const theories = state.data.theories ?? [];
  const claims = state.data.claims ?? [];

  state.derived.filteredTheories = theorySearch
    ? theorySearch({
        query: state.query,
        maturity: state.maturity,
        domain: state.domain,
        family: state.family,
        sort: state.sort
      })
    : theories;

  state.derived.filteredClaims = claimSearch
    ? claimSearch({
        query: state.query,
        status: state.claimStatus,
        theoryId: state.route.query?.get("theory") ?? ""
      })
    : claims;

  state.derived.metrics = computeMetrics(state.data);
  return state;
}

export function toggleFavorite(state, theoryId) {
  const favorites = new Set(state.favorites);
  if (favorites.has(theoryId)) favorites.delete(theoryId);
  else favorites.add(theoryId);
  state.favorites = [...favorites];
  return state;
}

export function toggleCompare(state, theoryId) {
  const compare = new Set(state.compareIds);
  if (compare.has(theoryId)) {
    compare.delete(theoryId);
  } else if (compare.size < MAX_COMPARE) {
    compare.add(theoryId);
  }
  state.compareIds = [...compare];
  return state;
}

export function createElement(tagName, options = {}, ...children) {
  const element = document.createElement(tagName);
  const {
    className,
    text,
    attrs = {},
    dataset = {},
    on = {}
  } = options;

  if (className) element.className = className;
  if (text !== undefined && text !== null) element.textContent = String(text);

  for (const [name, value] of Object.entries(attrs)) {
    if (value === false || value === null || value === undefined) continue;
    if (value === true) element.setAttribute(name, "");
    else element.setAttribute(name, String(value));
  }

  for (const [name, value] of Object.entries(dataset)) {
    element.dataset[name] = String(value);
  }

  for (const [eventName, listener] of Object.entries(on)) {
    element.addEventListener(eventName, listener);
  }

  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    if (child instanceof Node) element.append(child);
    else element.append(document.createTextNode(String(child)));
  }
  return element;
}

export function announce(message) {
  const region = document.querySelector("#announcer");
  if (!region) return;
  region.textContent = "";
  window.requestAnimationFrame(() => {
    region.textContent = message;
  });
}

export function setDocumentTitle(title) {
  document.title = title
    ? `${title} — Tristan Web OS`
    : "Tristan Web OS — Théories, preuves et prototypes";
}

export function safeExternalLink(url) {
  try {
    const parsed = new URL(url, window.location.href);
    if (!["http:", "https:"].includes(parsed.protocol)) return null;
    return parsed.href;
  } catch {
    return null;
  }
}

export function createDebounce(callback, delay = 120) {
  let handle = null;
  return (...args) => {
    window.clearTimeout(handle);
    handle = window.setTimeout(() => callback(...args), delay);
  };
}
