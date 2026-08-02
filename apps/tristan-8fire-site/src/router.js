"use strict";

const DEFAULT_ROUTE = { name: "dashboard", params: {}, query: new URLSearchParams() };

function decode(value) {
  try { return decodeURIComponent(value); } catch { return value; }
}

export function parseRoute(hash = window.location.hash) {
  const raw = String(hash || "").replace(/^#\/?/, "");
  if (!raw) return DEFAULT_ROUTE;
  const [pathPart, queryPart = ""] = raw.split("?");
  const segments = pathPart.split("/").filter(Boolean).map(decode);
  const name = segments[0] || "dashboard";
  const params = {};
  if (name === "theory" && segments[1]) params.id = segments[1];
  if (name === "claim" && segments[1]) params.id = segments[1];
  if (name === "graph" && segments[1]) params.focus = segments[1];
  return { name, params, query: new URLSearchParams(queryPart) };
}

export function routeTo(name, params = {}, query = {}) {
  const parts = [name];
  if (name === "theory" && params.id) parts.push(encodeURIComponent(params.id));
  if (name === "claim" && params.id) parts.push(encodeURIComponent(params.id));
  if (name === "graph" && params.focus) parts.push(encodeURIComponent(params.focus));
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  }
  return `#/${parts.join("/")}${search.size ? `?${search}` : ""}`;
}

export function createRouter(onRoute) {
  let current = parseRoute();
  const notify = () => {
    current = parseRoute();
    onRoute(current);
  };
  window.addEventListener("hashchange", notify);
  return {
    start() {
      if (!window.location.hash) history.replaceState(null, "", routeTo("dashboard"));
      notify();
    },
    current: () => current,
    go(name, params, query) { window.location.hash = routeTo(name, params, query); },
    destroy() { window.removeEventListener("hashchange", notify); }
  };
}
