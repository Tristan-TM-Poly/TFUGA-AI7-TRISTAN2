"use strict";

const KEY = "tristan-web-os-preferences-v1";
const DEFAULTS = Object.freeze({ theme: "dark", density: "comfortable", motion: "system" });

function safeRead() {
  try {
    const parsed = JSON.parse(localStorage.getItem(KEY) || "{}");
    return { ...DEFAULTS, ...parsed };
  } catch {
    return { ...DEFAULTS };
  }
}

export function createPreferences() {
  let value = safeRead();
  const listeners = new Set();

  function apply() {
    const root = document.documentElement;
    root.dataset.theme = value.theme;
    root.dataset.density = value.density;
    root.dataset.motion = value.motion;
    root.style.colorScheme = value.theme === "light" ? "light" : "dark";
  }

  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(value)); } catch { /* private mode */ }
  }

  function set(patch) {
    value = { ...value, ...patch };
    apply();
    save();
    for (const listener of listeners) listener({ ...value });
  }

  apply();
  return {
    get: () => ({ ...value }),
    set,
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener); },
    reset() { value = { ...DEFAULTS }; apply(); save(); },
    toggleTheme() { set({ theme: value.theme === "dark" ? "light" : "dark" }); },
    toggleDensity() { set({ density: value.density === "compact" ? "comfortable" : "compact" }); }
  };
}
